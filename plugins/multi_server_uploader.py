import os
import asyncio
import aiohttp
import logging
import time
import __main__
import base64
from pyrogram import Client

logger = logging.getLogger(__name__)

# --- CONFIGURATION (API Keys) ---
DOODSTREAM_API_KEY = "542876jnkjx49k31k1de4h" 
STREAMWISH_API_KEY = "534f5100961cd89227dc"

# --- PROGRESS BAR HELPER (10 Sec Interval) ---
last_update_time = {}

def size_format(b):
    for unit in ["", "K", "M", "G", "T"]:
        if b < 1024: return f"{b:.2f}{unit}B"
        b /= 1024

async def progress_bar(current, total, message, start_time, status_text):
    global last_update_time
    now = time.time()
    msg_id = message.id
    
    # প্রতি ১০ সেকেন্ড পর পর আপডেট হবে যাতে টেলিগ্রাম ব্লক না করে
    if msg_id in last_update_time and (now - last_update_time[msg_id]) < 10:
        return
    
    last_update_time[msg_id] = now
    diff = now - start_time
    percentage = current * 100 / total
    speed = current / (diff if diff > 0 else 1)
    
    progress = "[{0}{1}]".format(
        ''.join(["▰" for i in range(round(percentage / 10))]),
        ''.join(["▱" for i in range(10 - round(percentage / 10))])
    )
    
    tmp = f"<b>{status_text}</b>\n\n" \
          f"<code>{progress} {round(percentage, 2)}%</code>\n" \
          f"🚀 <b>Speed:</b> {size_format(speed)}/s\n" \
          f"📦 <b>Process:</b> {size_format(current)} of {size_format(total)}\n" \
          f"⏱️ <b>Time:</b> {round(diff)}s"
    
    try: await message.edit_text(tmp)
    except: pass

# --- ADVANCED RGB HTML PATCH (Fixing Recursion) ---
def patched_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    title = data.get("title") or data.get("name")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    overview = data.get("overview", "No Plot Available.")

    # RGB NEON CSS
    style_css = """
    <style>
        @keyframes rainbow { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(360deg); } }
        @keyframes glow { 0%, 100% { box-shadow: 0 0 10px #ff007f, 0 0 20px #00d2ff; } 50% { box-shadow: 0 0 20px #39ff14, 0 0 40px #9d00ff; } }
        .download-container { background: #0f0f13; padding: 20px; border-radius: 15px; border: 1px solid #2a2a35; }
        .btn-box { position: relative; margin-bottom: 20px; border-radius: 12px; padding: 3px; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rainbow 5s linear infinite; }
        .btn-main { background: #1a1a24; display: flex; align-items: center; justify-content: center; padding: 18px; border-radius: 10px; color: #fff; text-decoration: none; font-weight: bold; font-size: 16px; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; animation: glow 3s ease-in-out infinite; }
        .btn-main:hover { background: transparent; transform: scale(1.03); color: #fff; }
        .tg-btn { border: 2px solid #00d2ff; background: #0088cc; }
        .server-tag { position: absolute; top: -10px; left: 15px; background: #ff007f; color: #fff; padding: 2px 10px; font-size: 10px; border-radius: 5px; font-weight: bold; z-index: 10; }
    </style>
    """

    btn_html = ""
    for link in links:
        lbl = link.get('label', 'Download')
        if link.get('tg_url'):
            b64 = base64.b64encode(link['tg_url'].encode('utf-8')).decode('utf-8')
            btn_html += f'''<div class="btn-box"><span class="server-tag">FASTEST</span><a href="#" class="btn-main tg-btn" onclick="goToLink('{b64}')">✈️ GET IN TELEGRAM FILE</a></div>'''
        else:
            url = link.get('url', '#')
            btn_html += f'''<div class="btn-box"><span class="server-tag">CLOUD</span><a href="{url}" target="_blank" class="btn-main">🚀 {lbl}</a></div>'''

    # Complete HTML (No Recursion)
    return f"""
    {style_css}
    <div class="download-container">
        <h2 style="color:#00d2ff; text-align:center;">{title} ({year})</h2>
        <img src="{poster}" style="width:100%; border-radius:10px; margin-bottom:20px; border:2px solid #2a2a35;">
        <p style="color:#d1d1d1; font-size:14px; line-height:1.6;">{overview[:200]}...</p>
        <div style="margin-top:30px;">{btn_html}</div>
    </div>
    <script>function goToLink(b){{window.location.href=atob(b);}}</script>
    """

# --- UPLOADERS (Robust Parallel) ---
async def up_gofile(p):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.gofile.io/servers") as r:
                srv = (await r.json())["data"]["servers"][0]["name"]
            d = aiohttp.FormData(); d.add_field('file', open(p, 'rb'))
            async with s.post(f"https://{srv}.gofile.io/contents/uploadfile", data=d) as r:
                return f"https://gofile.io/d/{(await r.json())['data']['code']}"
    except: return None

async def up_dood(p):
    if not DOODSTREAM_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://doodapi.com/api/upload/server?key={DOODSTREAM_API_KEY}") as r:
                u = (await r.json())["result"]
            d = aiohttp.FormData(); d.add_field('api_key', DOODSTREAM_API_KEY); d.add_field('file', open(p, 'rb'))
            async with s.post(u, data=d) as r:
                return f"https://doodstream.com/d/{(await r.json())['result'][0]['filecode']}"
    except: return None

async def up_wish(p):
    if not STREAMWISH_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.streamwish.com/api/upload/server?key={STREAMWISH_API_KEY}") as r:
                u = (await r.json())["result"]
            d = aiohttp.FormData(); d.add_field('key', STREAMWISH_API_KEY); d.add_field('file', open(p, 'rb'))
            async with s.post(u, data=d) as r:
                return f"https://streamwish.com/{(await r.json())['result'][0]['filecode']}"
    except: return None

# --- PATCHED PROCESSOR ---
async def patched_process_file_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status = await message.reply_text(f"⏳ <b>Initializing:</b> {temp_name}")
    
    try:
        # 1. Save TG DB
        cp = await message.copy(__main__.DB_CHANNEL_ID)
        convo["links"].append({"label": f"Telegram: {temp_name}", "tg_url": f"https://t.me/{(await client.get_me()).username}?start=get-{cp.id}"})
        
        # 2. Download with Progress
        start = time.time()
        path = await message.download(progress=progress_bar, progress_args=(status, start, f"📥 Downloading: {temp_name}"))
        
        # 3. Parallel Upload
        await status.edit_text(f"📤 <b>Uploading to Cloud Servers...</b>\n📦 File: {temp_name}")
        g_task, d_task, w_task = await asyncio.gather(up_gofile(path), up_dood(path), up_wish(path))
        
        if g_task: convo["links"].append({"label": "High Speed Download", "url": g_task})
        if d_task: convo["links"].append({"label": "Watch Online (Server 1)", "url": d_task})
        if w_task: convo["links"].append({"label": "Watch Online (Server 2)", "url": w_task})
        
        if os.path.exists(path): os.remove(path)
        await status.edit_text(f"✅ <b>Successfully Processed:</b> {temp_name}\n(Parallel Upload Complete)")
        
    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

# --- PLUGIN REGISTER ---
async def register(bot: Client):
    __main__.process_file_upload = patched_process_file_upload
    __main__.generate_html_code = patched_generate_html_code
    print("🚀 [Plugin] Final 100% Fixed Multi-Server Uploader Activated!")
