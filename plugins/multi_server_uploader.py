import os
import asyncio
import aiohttp
import logging
import time
import __main__
import base64

logger = logging.getLogger(__name__)

# --- CONFIGURATION (এপিআই কি গুলো এখানে দিন) ---
DOODSTREAM_API_KEY = "534f5100961cd89227dc" 
STREAMWISH_API_KEY = "542876jnkjx49k31k1de4h"

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
    if msg_id in last_update_time and (now - last_update_time[msg_id]) < 10:
        return
    last_update_time[msg_id] = now
    
    diff = now - start_time
    percentage = (current * 100) / total
    speed = current / (diff if diff > 0 else 1)
    
    # Elegant Progress Bar
    progress = "▰" * round(percentage / 10) + "▱" * (10 - round(percentage / 10))
    
    tmp = (f"🚀 <b>{status_text}</b>\n\n"
           f"<code>{progress} {round(percentage, 2)}%</code>\n"
           f"📊 <b>Speed:</b> {size_format(speed)}/s\n"
           f"📦 <b>Done:</b> {size_format(current)} / {size_format(total)}\n"
           f"⏱️ <b>Elapsed:</b> {round(diff)}s")
    
    try: await message.edit_text(tmp)
    except: pass

# --- UPLOAD WITH PROGRESS WRAPPER ---
async def upload_with_progress(session, url, data, file_path, status_msg, task_name):
    file_size = os.path.getsize(file_path)
    start_time = time.time()
    
    # কাস্টম রিডার প্রসেস বার দেখানোর জন্য
    async def file_sender():
        with open(file_path, 'rb') as f:
            chunk = f.read(1024*1024) # 1MB chunk
            read_bytes = 0
            while chunk:
                yield chunk
                read_bytes += len(chunk)
                await progress_bar(read_bytes, file_size, status_msg, start_time, task_name)
                chunk = f.read(1024*1024)

    data.add_field('file', file_sender(), filename=os.path.basename(file_path))
    async with session.post(url, data=data) as resp:
        return await resp.json()

# --- HTML GENERATOR (পেশাদার RGB বাটন ও আনলক সিস্টেম) ---
def patched_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # মেইন ফাইলের আনলক লজিক ঠিক রেখে শুধু ডিজাইন পরিবর্তন
    title = data.get("title") or data.get("name")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    
    # Professional RGB/Neon CSS
    style_css = """
    <style>
        :root { --main-bg: #0f1016; --box-bg: #161b22; --accent: #00d2ff; }
        .server-grid { display: flex; flex-direction: column; gap: 15px; padding: 10px; }
        .rgb-box { position: relative; padding: 2px; border-radius: 12px; background: linear-gradient(45deg, #ff0000, #00ff00, #0000ff, #ff0000); background-size: 400%; animation: rgb-glow 10s linear infinite; }
        @keyframes rgb-glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
        .btn-link { background: #161b22; color: white !important; display: flex; align-items: center; justify-content: center; padding: 16px; border-radius: 10px; text-decoration: none !important; font-weight: bold; font-size: 15px; border: 1px solid #30363d; transition: 0.3s; }
        .btn-link:hover { background: transparent; transform: scale(1.02); }
        .tg-btn { border: 2px solid #0088cc; box-shadow: 0 0 10px #0088cc; }
        .icon { margin-right: 10px; font-size: 20px; }
        .server-label { position: absolute; top: -10px; left: 15px; background: #238636; color: white; padding: 2px 10px; font-size: 11px; border-radius: 5px; font-weight: bold; }
    </style>
    """

    server_list_html = ""
    for link in links:
        lbl = link.get('label', 'Download')
        if link.get('tg_url'):
            b64 = base64.b64encode(link['tg_url'].encode('utf-8')).decode('utf-8')
            server_list_html += f'''
            <div class="rgb-box">
                <span class="server-label">TELEGRAM CLOUD</span>
                <a href="#" class="btn-link tg-btn" onclick="goToLink('{b64}')">
                    <span class="icon">✈️</span> GET IN TELEGRAM FILE
                </a>
            </div>'''
        else:
            url = link.get('url', '#')
            icon = "🎬" if "Watch" in lbl or "Play" in lbl else "🚀"
            server_list_html += f'''
            <div class="rgb-box">
                <span class="server-label">DIRECT SERVER</span>
                <a href="{url}" target="_blank" class="btn-link">
                    <span class="icon">{icon}</span> {lbl}
                </a>
            </div>'''

    # মেইন ফাইলের অরিজিনাল স্ট্রাকচার (Unlock logic সহ)
    original_html = __main__.generate_html_code(data, [], [], [], 0)
    # বাটন সেকশন রিপ্লেস করা হচ্ছে
    final_html = original_html.replace('<div class="server-list">', f'{style_css}<div class="server-list">{server_list_html}')
    return final_html

# --- SERVER UPLOADERS (Robust Sequential with Progress) ---

async def up_gofile(path, status):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.gofile.io/servers") as r:
                srv = (await r.json())["data"]["servers"][0]["name"]
            url = f"https://{srv}.gofile.io/contents/uploadfile"
            res = await upload_with_progress(s, url, aiohttp.FormData(), path, status, "Gofile Uploading")
            return f"https://gofile.io/d/{res['data']['code']}"
    except: return None

async def up_dood(path, status):
    if not DOODSTREAM_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://doodapi.com/api/upload/server?key={DOODSTREAM_API_KEY}") as r:
                url = (await r.json())["result"]
            data = aiohttp.FormData(); data.add_field('api_key', DOODSTREAM_API_KEY)
            res = await upload_with_progress(s, url, data, path, status, "DoodStream Uploading")
            return f"https://doodstream.com/d/{res['result'][0]['filecode']}"
    except: return None

async def up_wish(path, status):
    if not STREAMWISH_API_KEY: return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.streamwish.com/api/upload/server?key={STREAMWISH_API_KEY}") as r:
                url = (await r.json())["result"]
            data = aiohttp.FormData(); data.add_field('key', STREAMWISH_API_KEY)
            res = await upload_with_progress(s, url, data, path, status, "StreamWish Uploading")
            return f"https://streamwish.com/{res['result'][0]['filecode']}"
    except: return None

# --- PROCESSOR ---
async def patched_process_file_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status = await message.reply_text(f"⏳ <b>Initializing:</b> {temp_name}")
    
    try:
        # 1. Telegram DB (Instant)
        cp = await message.copy(__main__.DB_CHANNEL_ID)
        convo["links"].append({"label": f"Telegram: {temp_name}", "tg_url": f"https://t.me/{(await client.get_me()).username}?start=get-{cp.id}"})
        
        # 2. Download Progress
        start = time.time()
        path = await message.download(progress=progress_bar, progress_args=(status, start, f"📥 Downloading: {temp_name}"))
        
        # 3. Sequential Cloud Uploads with Progress
        # Gofile
        g_link = await up_gofile(path, status)
        if g_link: convo["links"].append({"label": "🚀 High Speed Download", "url": g_link})
        
        # Dood
        d_link = await up_dood(path, status)
        if d_link: convo["links"].append({"label": "🎬 Watch Online (Server 1)", "url": d_link})
        
        # Wish
        w_link = await up_wish(path, status)
        if w_link: convo["links"].append({"label": "📺 Watch Online (Server 2)", "url": w_link})
        
        if os.path.exists(path): os.remove(path)
        await status.edit_text(f"✅ <b>Successfully Processed:</b> {temp_name}\n(All Servers Completed)")
        
    except Exception as e:
        await status.edit_text(f"❌ Error: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

# --- PLUGIN REGISTER ---
async def register(bot: Client):
    __main__.process_file_upload = patched_process_file_upload
    __main__.generate_html_code = patched_generate_html_code
    print("🚀 [Plugin] Sequential Uploader with 10s Progress Bar & RGB Buttons Activated!")
