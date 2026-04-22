# -*- coding: utf-8 -*-
import os
import re
import json
import base64
import asyncio
import __main__ 
from aiohttp import web
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
DB_CHANNEL_ID = int(os.getenv("DB_CHANNEL_ID", "0"))
PORT = int(os.getenv("STREAM_PORT", 8000)) 
DOMAIN_URL = os.getenv("DOMAIN_URL", "").rstrip("/")
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "") 
AUTO_DELETE_TIME = 300 

_bot: Client = None

# ==========================================
# 🔐 ENCRYPTION & DECRYPTION
# ==========================================
def encode_id(msg_id: int) -> str:
    payload = f"TGLINK_{msg_id}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

def decode_id(payload: str) -> int:
    try:
        missing_padding = len(payload) % 4
        if missing_padding: payload += "=" * (4 - missing_padding)
        decoded = base64.urlsafe_b64decode(payload.encode()).decode()
        if decoded.startswith("TGLINK_"):
            return int(decoded.split("_")[1])
    except: pass
    return 0

# ==========================================
# 🌐 HTTP STREAM SERVER
# ==========================================
async def stream_handler(request):
    try:
        msg_id_str = request.match_info.get('msg_id')
        if not msg_id_str: return web.Response(text="Server is Online!")
        
        msg_id = int(msg_id_str)
        msg = await _bot.get_messages(DB_CHANNEL_ID, msg_id)
        
        if not msg or not msg.media:
            return web.Response(status=404, text="File Not Found")

        media = msg.video or msg.document or msg.audio
        file_size = media.file_size
        file_name = getattr(media, 'file_name', f"video_{msg_id}.mp4")

        range_header = request.headers.get('Range', '')
        offset, limit = 0, file_size
        if range_header:
            match = re.search(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                offset = int(match.group(1))
                if match.group(2): limit = int(match.group(2)) + 1
                    
        headers = {
            'Content-Type': getattr(media, 'mime_type', 'video/mp4'),
            'Accept-Ranges': 'bytes',
            'Content-Range': f'bytes {offset}-{limit-1}/{file_size}',
            'Content-Length': str(limit - offset),
            'Access-Control-Allow-Origin': '*' 
        }
        
        disposition = 'attachment' if request.query.get('download') else 'inline'
        headers['Content-Disposition'] = f'{disposition}; filename="{file_name}"'

        response = web.StreamResponse(status=206 if range_header else 200, headers=headers)
        await response.prepare(request)
        async for chunk in _bot.stream_media(msg, offset=offset, limit=limit):
            await response.write(chunk)
        return response
    except:
        return web.Response(status=500, text="Internal Error")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/stream/{msg_id}', stream_handler)
    app.router.add_get('/', lambda r: web.Response(text="🚀 Server is Running!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()

# ==========================================
# 🪄 MAGIC OVERRIDES (Template & Logic)
# ==========================================
async def magic_process_file_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text("⏳ **ডাটাবেসে সেভ হচ্ছে...**", quote=True)
    try:
        copied_msg = await message.copy(chat_id=DB_CHANNEL_ID)
        convo["links"].append({"label": temp_name, "msg_id": copied_msg.id, "is_grouped": True})
        await status_msg.edit_text(f"✅ **সেভ হয়েছে:** {temp_name}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

def magic_generate_html_code(data, links, *args, **kwargs):
    # মুভির ডিটেইলস পুনরুদ্ধার করা হলো
    title = data.get("title") or data.get("name", "Unknown")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    rating = f"{data.get('vote_average', 0):.1f}/10"
    overview = data.get("overview", "No description available.")
    genres_str = ", ".join([g['name'] for g in data.get('genres', [])]) if data.get('genres') else "Movie"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]

    bot_username = _bot.me.username if _bot else "Bot"
    server_list_html = ""
    first_stream_url = ""

    for i, link in enumerate(links):
        if 'msg_id' in link:
            m_id = link['msg_id']
            stream_url = f"{DOMAIN_URL}/stream/{m_id}"
            download_url = f"{DOMAIN_URL}/stream/{m_id}?download=1"
            tg_url = f"https://t.me/{bot_username}?start={encode_id(m_id)}"
            if i == 0: first_stream_url = stream_url
            
            lbl = link.get('label', f'Quality {i+1}')
            server_list_html += f'''
            <div class="server-card">
                <p>📺 {lbl}</p>
                <div class="btn-group">
                    <a href="{download_url}" class="dl-btn">⚡ Download</a>
                    <a href="{tg_url}" class="tg-btn">✈️ Telegram</a>
                </div>
            </div>'''

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ background:#0f0f13; color:white; font-family:sans-serif; margin:0; padding:15px; }}
            .container {{ max-width:600px; margin:auto; background:#1a1a24; padding:20px; border-radius:15px; box-shadow:0 0 20px rgba(0,0,0,0.5); }}
            .poster {{ width:100%; border-radius:10px; margin-bottom:15px; }}
            .title {{ font-size:22px; color:#00d2ff; margin:10px 0; }}
            .meta {{ font-size:14px; color:#aaa; margin-bottom:15px; }}
            .plot {{ background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; font-size:14px; line-height:1.5; margin-bottom:20px; }}
            .server-card {{ background:#252533; padding:15px; border-radius:10px; margin-bottom:15px; border-left:4px solid red; }}
            .btn-group {{ display:flex; gap:10px; margin-top:10px; }}
            .dl-btn, .tg-btn {{ flex:1; padding:12px; text-decoration:none; border-radius:5px; font-weight:bold; text-align:center; color:white; font-size:14px; }}
            .dl-btn {{ background:#E50914; }} .tg-btn {{ background:#0088cc; }}
            video {{ width:100%; border-radius:10px; margin-bottom:20px; background:black; }}
            #main-content {{ display:none; }}
            .unlock-btn {{ width:100%; padding:15px; background:red; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer; font-size:16px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <img src="{poster}" class="poster">
            <div class="title">{title} ({year})</div>
            <div class="meta">⭐ {rating} | 🎭 {genres_str}</div>
            
            <div id="unlock-area">
                <div class="plot">{overview[:200]}...</div>
                <button class="unlock-btn" onclick="unlock()">▶️ UNLOCK PLAYER & DOWNLOAD</button>
            </div>

            <div id="main-content">
                <div class="plot">{overview}</div>
                {f'<video controls><source src="{first_stream_url}"></video>' if first_stream_url else ''}
                {server_list_html}
            </div>
        </div>
        <script>
            function unlock() {{
                document.getElementById('unlock-area').style.display = 'none';
                document.getElementById('main-content').style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """

# ==========================================
# 🤖 PLUGIN REGISTER & HANDLERS
# ==========================================
async def register(bot: Client):
    global _bot
    _bot = bot
    __main__.process_file_upload = magic_process_file_upload
    __main__.generate_html_code = magic_generate_html_code
    asyncio.create_task(start_web_server())

    # ✅ ফিক্সড স্টার্ট হ্যান্ডলার (Double Message Block করার জন্য)
    @bot.on_message(filters.command("start") & filters.private, group=-1)
    async def secure_start_handler(client, message):
        if len(message.command) > 1:
            msg_id = decode_id(message.command[1])
            if msg_id > 0:
                # Force Sub Check
                if FORCE_SUB_CHANNEL:
                    try:
                        await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
                    except UserNotParticipant:
                        btn = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
                               [InlineKeyboardButton("🔄 Try Again", url=f"https://t.me/{(await client.get_me()).username}?start={message.command[1]}")] ]
                        await message.reply_text("⚠️ ফাইলটি পেতে আমাদের চ্যানেলে জয়েন করুন।", reply_markup=InlineKeyboardMarkup(btn))
                        message.stop_propagation()
                        return
                    except: pass
                
                try:
                    sent_msg = await client.copy_message(message.chat.id, DB_CHANNEL_ID, msg_id)
                    # ✋ মেইন বটের অন্য কোনো মেসেজ আসা বন্ধ করবে
                    message.stop_propagation() 
                    
                    del_msg = await message.reply_text(f"🚀 ফাইলটি পাঠানো হয়েছে। এটি {AUTO_DELETE_TIME//60} মিনিট পর ডিলিট হবে।")
                    await asyncio.sleep(AUTO_DELETE_TIME)
                    await client.delete_messages(message.chat.id, [sent_msg.id, del_msg.id])
                except:
                    message.stop_propagation()
