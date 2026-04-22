# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import base64
import random
import asyncio
import __main__  # মেইন ফাইলকে ইম্পোর্ট করা হলো (ম্যাজিক এর জন্য)
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant

# ==========================================
# ⚙️ CONFIGURATION FOR KOYEB
# ==========================================
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", 0))
# Koyeb এ Stream Server চলবে 8000 পোর্টে
PORT = int(os.getenv("STREAM_PORT", 8000)) 
# Koyeb এর ডোমেইন (Environment Variable থেকে নিবে, না থাকলে ডিফল্ট)
DOMAIN_URL = os.getenv("DOMAIN_URL", "https://your-app-name.koyeb.app").rstrip("/")

FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "") # F-Sub চ্যানেল ইউজারনেম (Optiona, @ ছাড়া)
AUTO_DELETE_TIME = 300 # ৫ মিনিট পর টেলিগ্রাম থেকে ফাইল ডিলিট হবে

_bot: Client = None

# ==========================================
# 🔐 ENCRYPTION & DECRYPTION FUNCTIONS
# ==========================================
def encode_id(msg_id: int) -> str:
    payload = f"TGLINK_{msg_id}"
    return base64.urlsafe_b64encode(payload.encode()).decode()

def decode_id(payload: str) -> int:
    try:
        decoded = base64.urlsafe_b64decode(payload.encode()).decode()
        if decoded.startswith("TGLINK_"):
            return int(decoded.split("_")[1])
    except:
        pass
    return 0

# ==========================================
# 🌐 HTTP STREAM SERVER (DIRECT PLAY & DL)
# ==========================================
async def stream_handler(request):
    try:
        msg_id = int(request.match_info['msg_id'])
        msg = await _bot.get_messages(DB_CHANNEL_ID, msg_id)
        
        if not msg or not getattr(msg, 'media', None):
            return web.Response(status=404, text="404: File Not Found in Telegram Database!")

        media = msg.video or msg.document
        file_size = getattr(media, 'file_size', 0)
        file_name = getattr(media, 'file_name', f"video_{msg_id}.mp4")

        range_header = request.headers.get('Range', '')
        offset, limit = 0, file_size
        
        if range_header:
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                offset = int(match.group(1))
                if match.group(2): limit = int(match.group(2)) + 1
                    
        chunk_size = limit - offset

        headers = {
            'Content-Type': getattr(media, 'mime_type', 'video/mp4'),
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {offset}-{limit-1}/{file_size}',
            'Content-Length': str(chunk_size),
            'Access-Control-Allow-Origin': '*' 
        }
        
        if request.query.get('download'):
            headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
        else:
            headers['Content-Disposition'] = f'inline; filename="{file_name}"'

        response = web.StreamResponse(status=206 if range_header else 200, headers=headers)
        await response.prepare(request)

        async for chunk in _bot.stream_media(msg, offset=offset, limit=limit):
            await response.write(chunk)

        return response
    except Exception as e:
        print(f"Stream Error: {e}")
        return web.Response(status=500, text="Internal Stream Server Error!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/stream/{msg_id}', stream_handler)
    app.router.add_get('/', lambda r: web.Response(text="🚀 Koyeb Stream Server is Active!"))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print(f"✅ Web Stream Server Started on Port {PORT}")

# ==========================================
# 🪄 MAGIC OVERRIDES (Monkey Patching)
# মেইন কোডকে না ছুঁয়েই থার্ড-পার্টি আপলোড অফ করে টেলিগ্রাম সিস্টেম চালু করা
# ==========================================

async def magic_process_file_upload(client, message, uid, temp_name):
    """এই ফাংশনটি মেইন ফাইলের আপলোড সিস্টেমকে পুরোপুরি অফ করে শুধু টেলিগ্রামে সেভ করবে"""
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text(f"⏳ **ডাটাবেসে সেভ হচ্ছে...** ({temp_name})", quote=True)
    
    try:
        # শুধু ডাটাবেস চ্যানেলে মেসেজ ফরোয়ার্ড হবে (কোনো থার্ড পার্টি সার্ভার নাই)
        copied_msg = await message.copy(chat_id=DB_CHANNEL_ID)
        
        # থার্ড পার্টির URL এর বদলে শুধু মেসেজ ID সেভ হবে
        convo["links"].append({
            "label": temp_name, 
            "msg_id": copied_msg.id,
            "is_grouped": True
        })
        await status_msg.edit_text(f"✅ **সফলভাবে সেভ হয়েছে:** {temp_name}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Failed: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)


def magic_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    """এই ফাংশনটি মেইন ফাইলের HTML ডিজাইন চেঞ্জ করে আমাদের স্ট্রিমিং ও টেলিগ্রাম বাটন বসিয়ে দিবে"""
    title = data.get("title") or data.get("name")
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    BTN_TELEGRAM = "https://i.ibb.co/kVfJvhzS/photo-2025-12-23-12-38-56-7587031987190235140.jpg"

    is_adult = data.get('adult', False) or data.get('force_adult', False)
    theme = data.get("theme", "netflix")
    if theme == "netflix":
        root_css = "--bg-color: #0f0f13; --box-bg: #1a1a24; --text-main: #ffffff; --text-muted: #d1d1d1; --primary: #E50914; --accent: #00d2ff; --border: #2a2a35; --btn-grad: linear-gradient(90deg, #E50914 0%, #ff5252 100%); --btn-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);"
    elif theme == "prime":
        root_css = "--bg-color: #0f171e; --box-bg: #1b2530; --text-main: #ffffff; --text-muted: #8197a4; --primary: #00A8E1; --accent: #00A8E1; --border: #2c3e50; --btn-grad: linear-gradient(90deg, #00A8E1 0%, #00d2ff 100%); --btn-shadow: 0 4px 15px rgba(0, 168, 225, 0.4);"
    else:
        root_css = "--bg-color: #f4f4f9; --box-bg: #ffffff; --text-main: #333333; --text-muted: #555555; --primary: #6200ea; --accent: #6200ea; --border: #dddddd; --btn-grad: linear-gradient(90deg, #6200ea 0%, #b388ff 100%); --btn-shadow: 0 4px 15px rgba(98, 0, 234, 0.4);"

    genres_str = ", ".join([g['name'] for g in data.get('genres',[])]) if not data.get('is_manual') else "Movie"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    rating = f"{data.get('vote_average', 0):.1f}/10"
    
    if is_adult:
        poster_html = f'<div class="nsfw-container" onclick="revealNSFW(this)"><img src="{poster}" class="nsfw-blur"><div class="nsfw-warning">🔞 18+ Click to Reveal</div></div>'
    else:
        poster_html = f'<img src="{poster}">'

    # 🔥 NEW EMBED PLAYER & SERVER LOGIC
    bot_username = _bot.me.username if _bot else "MovieBot"
    embed_html = ""
    server_list_html = ""

    for i, link in enumerate(links):
        if 'msg_id' in link:
            msg_id = link['msg_id']
            stream_url = f"{DOMAIN_URL}/stream/{msg_id}"
            download_url = base64.b64encode(f"{DOMAIN_URL}/stream/{msg_id}?download=1".encode()).decode()
            tg_url = base64.b64encode(f"https://t.me/{bot_username}?start={encode_id(msg_id)}".encode()).decode()
            
            # প্রথম ফাইলটি লাইভ প্লেয়ারে সেট হবে
            if i == 0:
                embed_html = f'''
                <div class="section-title">🍿 Watch Online (Live Player)</div>
                <div class="embed-container" style="background:#000;">
                    <video controls crossorigin playsinline style="width:100%; height:100%; border-radius:10px;">
                        <source src="{stream_url}" type="video/mp4">
                        Your browser does not support HTML5 video.
                    </video>
                </div>
                <hr style="border-top: 1px dashed var(--border); margin: 20px 0;">
                '''
            
            lbl = link.get('label', 'Download')
            server_list_html += f'''
            <div class="quality-title">📺 {lbl}</div>
            <div class="server-grid">
                <button class="final-server-btn cloud-btn" onclick="goToLink('{download_url}')" style="background: #E50914;">⚡ Direct Download</button>
                <button class="final-server-btn tg-btn" onclick="goToLink('{tg_url}')">✈️ Get via Telegram</button>
            </div>
            '''

    weighted_ad_list = owner_ad_links_list or ["https://google.com"]

    return f"""
    <style>
        :root {{ {root_css} }}
        body {{ font-family: sans-serif; background: var(--bg-color); color: var(--text-main); margin: 0; padding: 20px; }}
        .app-wrapper {{ max-width: 650px; margin: auto; background: var(--box-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border); }}
        .movie-title {{ color: var(--accent); font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; }}
        .info-box {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .info-poster img {{ width: 150px; border-radius: 8px; }}
        .info-text {{ font-size: 14px; line-height: 1.8; }}
        .section-title {{ font-size: 18px; margin: 20px 0 10px; border-bottom: 2px solid var(--primary); display: inline-block; }}
        .plot-box {{ background: rgba(0,0,0,0.05); padding: 15px; border-left: 4px solid var(--primary); font-size: 14px; margin-bottom: 20px; }}
        .main-btn {{ width: 100%; padding: 15px; font-weight: bold; background: var(--btn-grad); color: #fff; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; }}
        .quality-title {{ font-weight: bold; color: var(--accent); margin-top: 20px; margin-bottom: 10px; background: rgba(0,0,0, 0.1); padding: 8px; border-radius: 6px; border-left: 3px solid var(--accent); }}
        .server-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
        .final-server-btn {{ padding: 12px; border: none; border-radius: 6px; color: #fff; font-weight: bold; cursor: pointer; width: 100%; }}
        .cloud-btn {{ background: #e50914; }} .tg-btn {{ background: #0088cc; }}
        #view-links {{ display: none; }}
        .embed-container {{ position: relative; padding-bottom: 56.25%; height: 0; border-radius: 10px; overflow: hidden; }}
        .embed-container video {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; }}
        .nsfw-container {{ position: relative; cursor: pointer; }}
        .nsfw-blur {{ filter: blur(25px); transition: 0.5s; }}
        .nsfw-warning {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: red; font-weight: bold; background: rgba(0,0,0,0.8); padding: 5px; border-radius: 5px; }}
        @media (max-width: 480px) {{ .info-box {{ flex-direction: column; align-items: center; }} .server-grid {{ grid-template-columns: 1fr; }} }}
    </style>
    <script>
        const AD_LINKS = {json.dumps(weighted_ad_list)};
        function startUnlock(btn) {{
            window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
            btn.innerHTML = "⏳ Please Wait... 5s";
            let t = 5;
            let timer = setInterval(() => {{
                t--; btn.innerHTML = "⏳ Please Wait... " + t + "s";
                if(t <= 0) {{
                    clearInterval(timer);
                    document.getElementById('view-details').style.display = 'none';
                    document.getElementById('view-links').style.display = 'block';
                }}
            }}, 1000);
        }}
        function goToLink(b64) {{ window.location.href = atob(b64); }}
        function revealNSFW(c) {{ c.querySelector('.nsfw-blur').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}
    </script>
    <div class="app-wrapper">
        <div id="view-details">
            <div class="movie-title">{title} ({year})</div>
            <div class="info-box"><div class="info-poster">{poster_html}</div><div class="info-text">⭐ {rating} <br>🎭 {genres_str} <br>📅 {year}</div></div>
            <div class="section-title">📖 Storyline</div>
            <div class="plot-box">{overview}</div>
            <button class="main-btn" onclick="startUnlock(this)">▶️ UNLOCK PLAYER & DOWNLOAD LINKS</button>
        </div>
        <div id="view-links">
            <h3 style="color:#00e676;">✅ Unlocked Successfully!</h3>
            {embed_html}
            {server_list_html}
        </div>
    </div>
    """

# ==========================================
# 🤖 PLUGIN REGISTER & HANDLERS
# ==========================================
async def register(bot: Client):
    global _bot
    _bot = bot
    
    # 🪄 MAGIC: মেইন কোডের ফাংশনগুলোকে আমাদের ফাংশন দিয়ে রিপ্লেস করে দেওয়া হলো
    __main__.process_file_upload = magic_process_file_upload
    __main__.generate_html_code = magic_generate_html_code
    
    # ব্যাকগ্রাউন্ডে স্ট্রিমিং সার্ভার চালু করা হলো
    asyncio.create_task(start_web_server())
    print("🪄 Magic Override Applied! Third-party uploads disabled. Telegram Native Engine Active!")

    # 🔐 সিকিউর টেলিগ্রাম লিংক এর জন্য আলাদা স্টার্ট হ্যান্ডলার (Group -1)
    @bot.on_message(filters.command("start") & filters.private, group=-1)
    async def secure_start_handler(client, message):
        if len(message.command) > 1 and message.command[1].startswith("TGLINK_"):
            msg_id = decode_id(message.command[1])
            
            if msg_id > 0:
                if FORCE_SUB_CHANNEL:
                    try:
                        await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
                    except UserNotParticipant:
                        btn = [[InlineKeyboardButton("📢 Join Channel First", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
                               [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={message.command[1]}")] ]
                        return await message.reply_text("⚠️ **ফাইলটি পেতে হলে প্রথমে আমাদের চ্যানেলে জয়েন করুন!**", reply_markup=InlineKeyboardMarkup(btn))
                    except:
                        pass
                
                try:
                    sent_msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, msg_id)
                    time_msg = await message.reply_text(f"⚠️ **সতর্কবার্তা:** ফাইলটি **{AUTO_DELETE_TIME//60} মিনিট** পর ডিলিট হয়ে যাবে। এখনই সেভ করে নিন!")
                    
                    # মেইন স্ক্রিপ্টের অন্যান্য স্টার্ট ফাংশন অফ করা হলো
                    message.stop_propagation()
                    
                    await asyncio.sleep(AUTO_DELETE_TIME)
                    await client.delete_messages(message.chat.id, [sent_msg.id, time_msg.id])
                    await client.send_message(message.chat.id, "🗑 **ফাইলটি ডিলিট করা হয়েছে!**")
                except Exception as e:
                    await message.reply_text("❌ ফাইলটি খুঁজে পাওয়া যায়নি!")
                    message.stop_propagation()
