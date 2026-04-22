import os
import asyncio
import aiohttp
import logging
import time
import __main__
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# আপনার API Key এখানে দিন (FileLions বা StreamWish এর সাইটে ফ্রিতে পাবেন)
STREAM_API_KEY = "4233u987m521" # আপনার সঠিক API Key এখানে দিন

# --- PROGRESS BAR HELPER ---
async def progress_bar(current, total, message, start_time, status_text):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.0) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        
        progress = "[{0}{1}]".format(
            ''.join(["▰" for i in range(round(percentage / 5))]),
            ''.join(["▱" for i in range(20 - round(percentage / 5))])
        )
        
        tmp = f"{status_text}\n\n{progress} {round(percentage, 2)}%\n" \
              f"🚀 গতি: {size_format(speed)}/s\n" \
              f"📦 সাইজ: {size_format(current)} / {size_format(total)}\n"
        
        try:
            await message.edit_text(tmp)
        except:
            pass

def size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor

# --- UPLOADERS WITH PROGRESS ---

async def upload_to_gofile(file_path, status_msg):
    """Gofile Upload with Progress Tracking"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get Best Server
            async with session.get("https://api.gofile.io/servers", timeout=10) as resp:
                res = await resp.json()
                if res["status"] != "ok": return None
                server = res["data"]["servers"][0]["name"]
            
            # Prepare Upload
            url = f"https://{server}.gofile.io/contents/uploadfile"
            data = aiohttp.FormData()
            file_size = os.path.getsize(file_path)
            
            # Custom reader for progress
            start_time = time.time()
            class ProgressReader:
                def __init__(self, filename):
                    self.f = open(filename, "rb")
                    self.read_bytes = 0
                def __len__(self): return file_size
                async def read(self, chunk):
                    data = self.f.read(chunk)
                    self.read_bytes += len(data)
                    await progress_bar(self.read_bytes, file_size, status_msg, start_time, "📤 Gofile-এ আপলোড হচ্ছে...")
                    return data
                def close(self): self.f.close()

            reader = ProgressReader(file_path)
            data.add_field('file', reader, filename=os.path.basename(file_path))
            
            async with session.post(url, data=data) as resp:
                result = await resp.json()
                reader.close()
                if result["status"] == "ok":
                    return f"https://gofile.io/d/{result['data']['code']}"
    except Exception as e:
        logger.error(f"Gofile Error: {e}")
    return None

async def upload_to_stream(file_path, status_msg):
    """FileLions/StreamWish Upload with Progress Tracking"""
    if not STREAM_API_KEY: return None
    try:
        file_size = os.path.getsize(file_path)
        async with aiohttp.ClientSession() as session:
            # Get Upload Server
            async with session.get(f"https://filelions.com/api/upload/server?key={STREAM_API_KEY}") as resp:
                res = await resp.json()
                upload_url = res.get("result")
            
            if upload_url:
                start_time = time.time()
                data = aiohttp.FormData()
                data.add_field('key', STREAM_API_KEY)
                
                # Progress wrapping
                with open(file_path, 'rb') as f:
                    data.add_field('file', f, filename=os.path.basename(file_path))
                    # নোট: aiohttp FormData বড় ফাইলে অটো প্রোগ্রেস আপডেট পাঠানো কঠিন, 
                    # তবে আমরা আপলোড শুরুর আগে স্ট্যাটাস দেব।
                    await status_msg.edit_text("📤 Stream Server-এ আপলোড শুরু হয়েছে (Wait)...")
                    async with session.post(upload_url, data=data) as resp:
                        res = await resp.json()
                        if res.get("msg") == "OK":
                            return f"https://filelions.com/{res['result'][0]['filecode']}"
    except Exception as e:
        logger.error(f"Stream Error: {e}")
    return None

# --- PATCHED PROCESS FUNCTION ---

async def patched_process_file_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    db_channel = __main__.DB_CHANNEL_ID
    
    if not convo: return
    
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text(f"⏳ **প্রসেসিং:** {temp_name}", quote=True)
    
    try:
        # ১. টেলিগ্রাম চ্যানেলে সেভ
        copied_msg = await message.copy(chat_id=db_channel)
        bot_username = (await client.get_me()).username
        tg_link = f"https://t.me/{bot_username}?start=get-{copied_msg.id}"
        
        convo["links"].append({"label": f"✈️ Telegram: {temp_name}", "tg_url": tg_link})
        
        # ২. ফাইল ডাউনলোড (উইথ প্রোগ্রেস বার)
        start_time = time.time()
        file_path = await message.download(
            progress=progress_bar,
            progress_args=(status_msg, start_time, "📥 টেলিগ্রাম থেকে ডাউনলোড হচ্ছে...")
        )
        
        # ৩. Gofile আপলোড
        await status_msg.edit_text("📤 Gofile-এ আপলোড শুরু হচ্ছে...")
        g_link = await upload_to_gofile(file_path, status_msg)
        if g_link:
            convo["links"].append({"label": f"🚀 High Speed: {temp_name}", "url": g_link})
        else:
            await message.reply_text(f"❌ Gofile আপলোড ফেইল হয়েছে ({temp_name})")

        # ৪. Stream আপলোড
        await status_msg.edit_text("📤 Stream সার্ভারে আপলোড শুরু হচ্ছে...")
        s_link = await upload_to_stream(file_path, status_msg)
        if s_link:
            convo["links"].append({"label": f"📺 Play Online: {temp_name}", "url": s_link})

        # ৫. ক্লিনিং
        if os.path.exists(file_path): os.remove(file_path)
        await status_msg.edit_text(f"✅ **{temp_name}** সফলভাবে সব সার্ভারে আপলোড হয়েছে!")
                
    except Exception as e:
        logger.error(f"Upload flow error: {e}")
        await status_msg.edit_text(f"❌ এরর: {str(e)}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

async def register(bot: Client):
    __main__.process_file_upload = patched_process_file_upload
    print("🚀 [Plugin] Multi-Server with Progress Bar Activated!")
