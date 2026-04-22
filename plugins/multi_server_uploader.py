import os
import asyncio
import aiohttp
import logging
import time
import __main__
import base64
import json
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# --- CONFIGURATION (এপিআই কি গুলো এখানে দিন) ---
DOODSTREAM_API_KEY = "38827...your_key" # Doodstream.com থেকে নিন
STREAMWISH_API_KEY = "4233...your_key"  # Streamwish.com থেকে নিন

# --- FANCY RGB HTML GENERATOR PATCH ---
def patched_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # মেইন ফাইলের অরিজিনাল লজিক ঠিক রেখে শুধু বাটন ডিজাইন আপডেট করবে
    title = data.get("title") or data.get("name")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    
    # CSS for Neon/RGB Buttons
    style_html = """
    <style>
        :root { --neon-blue: #00d2ff; --neon-pink: #ff007f; --neon-green: #39ff14; --neon-purple: #9d00ff; }
        .server-grid { display: grid; grid-template-columns: 1fr; gap: 15px; margin-top: 20px; }
        .btn-wrapper { position: relative; overflow: hidden; border-radius: 10px; padding: 2px; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; animation: animate 20s linear infinite; }
        @keyframes animate { 0% { background-position: 0% 0%; } 50% { background-position: 400% 0%; } 100% { background-position: 0% 0%; } }
        .fancy-btn { background: #1a1a24; color: #fff; border: none; padding: 15px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 10px; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; text-decoration: none; font-size: 14px; }
        .fancy-btn:hover { background: transparent; transform: scale(1.02); }
        .tg-style { background: #0088cc !important; border: 2px solid #fff; box-shadow: 0 0 15px #0088cc; }
        .stream-style { border: 1px solid var(--neon-green); box-shadow: 0 0 10px rgba(57, 255, 20, 0.3); }
        .dl-style { border: 1px solid var(--neon-blue); box-shadow: 0 0 10px rgba(0, 210, 255, 0.3); }
        .quality-badge { background: var(--neon-pink); padding: 5px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 5px; display: inline-block; }
    </style>
    """

    server_list_html = ""
    for link in links:
        lbl = link.get('label', 'Download')
        if link.get('tg_url'):
            encoded_url = base64.b64encode(link['tg_url'].encode('utf-8')).decode('utf-8')
            server_list_html += f'''
            <div class="btn-wrapper" style="animation-duration: 5s;">
                <a href="#" class="fancy-btn tg-style" onclick="goToLink('{encoded_url}')">
                    <span>✈️ GET FILE ON TELEGRAM</span>
                </a>
            </div>'''
        else:
            url = link.get('url', '#')
            style_class = "stream-style" if "Play" in lbl or "Stream" in lbl else "dl-style"
            icon = "🎬" if "Play" in lbl else "🚀"
            server_list_html += f'''
            <div class="btn-wrapper">
                <a href="{url}" target="_blank" class="fancy-btn {style_class}">
                    <span>{icon} {lbl}</span>
                </a>
            </div>'''

    # এই ফাংশনটি মেইন ফাইলের generate_html_code এর মতই স্ট্রাকচার রিটার্ন করবে
    # তবে আমরা এখানে শুধুমাত্র শর্টকাট নিচ্ছি। 
    # মেইন ফাইলের বডি কপি করে বাটন সেকশন রিপ্লেস করা হচ্ছে।
    original_html = __main__.generate_html_code(data, [], [], [], 0) # Base template
    final_html = original_html.replace('<div class="server-list">', f'{style_html}<div class="server-list">{server_list_html}')
    return final_html

# --- UPLOADERS ---

async def upload_gofile(file_path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gofile.io/servers") as r:
                srv = (await r.json())["data"]["servers"][0]["name"]
            data = aiohttp.FormData()
            data.add_field('file', open(file_path, 'rb'))
            async with session.post(f"https://{srv}.gofile.io/contents/uploadfile", data=data) as r:
                res = await r.json()
                return f"https://gofile.io/d/{res['data']['code']}"
    except: return None

async def upload_dood(file_path):
    if not DOODSTREAM_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://doodapi.com/api/upload/server?key={DOODSTREAM_API_KEY}") as r:
                url = (await r.json())["result"]
            data = aiohttp.FormData(); data.add_field('api_key', DOODSTREAM_API_KEY); data.add_field('file', open(file_path, 'rb'))
            async with session.post(url, data=data) as r:
                res = await r.json()
                return f"https://doodstream.com/d/{res['result'][0]['filecode']}"
    except: return None

async def upload_streamwish(file_path):
    if not STREAMWISH_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.streamwish.com/api/upload/server?key={STREAMWISH_API_KEY}") as r:
                url = (await r.json())["result"]
            data = aiohttp.FormData(); data.add_field('key', STREAMWISH_API_KEY); data.add_field('file', open(file_path, 'rb'))
            async with session.post(url, data=data) as r:
                res = await r.json()
                return f"https://streamwish.com/{res['result'][0]['filecode']}"
    except: return None

# --- PROCESS FUNCTION ---

async def patched_process_file_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text(f"⏳ **Processing:** {temp_name}\n\n1. Saving to Telegram DB...")
    
    try:
        # 1. Telegram DB
        copied = await message.copy(__main__.DB_CHANNEL_ID)
        tg_url = f"https://t.me/{(await client.get_me()).username}?start=get-{copied.id}"
        convo["links"].append({"label": f"Telegram: {temp_name}", "tg_url": tg_url})
        
        # 2. Download
        await status_msg.edit_text(f"⏳ **Processing:** {temp_name}\n\n2. Downloading for Cloud Upload...")
        path = await message.download()
        
        # 3. Parallel Uploading (Gofile, Dood, Streamwish)
        await status_msg.edit_text(f"⏳ **Processing:** {temp_name}\n\n3. Uploading to Multiple Servers (Parallel)...")
        tasks = [upload_gofile(path), upload_dood(path), upload_streamwish(path)]
        results = await asyncio.gather(*tasks)
        
        labels = ["🚀 Gofile (High Speed)", "🎬 DoodStream (Watch Online)", "📺 StreamWish (Multi-Server)"]
        for i, link in enumerate(results):
            if link:
                convo["links"].append({"label": labels[i], "url": link})
        
        if os.path.exists(path): os.remove(path)
        await status_msg.edit_text(f"✅ **{temp_name}** আপলোড সম্পন্ন হয়েছে!\n\nআপনার পোস্টে এখন আরজিবি বাটন দেখা যাবে।")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ এরর: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

# --- PLUGIN REGISTER ---
async def register(bot: Client):
    __main__.process_file_upload = patched_process_file_upload
    __main__.generate_html_code = patched_generate_html_code
    print("🔥 [Plugin] RGB Multi-Server Uploader & HTML Patcher Activated!")
