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
STREAM_API_KEY = "4233u987m521" # আপনার সঠিক API Key

# --- PROGRESS BAR HELPER ---
def size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor: return f"{b:.2f}{unit}{suffix}"
        b /= factor

async def progress_bar(current, total, message, start_time, status_text):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.0) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / (diff if diff > 0 else 1)
        
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

# --- UPLOADERS ---

async def upload_to_gofile(file_path, status_msg):
    """Gofile Upload (Fixed Serialization)"""
    try:
        async with aiohttp.ClientSession() as session:
            # Get Server
            async with session.get("https://api.gofile.io/servers", timeout=10) as resp:
                res = await resp.json()
                if res["status"] != "ok": return None
                server = res["data"]["servers"][0]["name"]
            
            # Upload
            url = f"https://{server}.gofile.io/contents/uploadfile"
            # এখানে আমরা সহজ পদ্ধতি ব্যবহার করছি যাতে Serialization error না হয়
            data = aiohttp.FormData()
            data.add_field('file', open(file_path, 'rb'), filename=os.path.basename(file_path))
            
            await status_msg.edit_text("📤 Gofile-এ আপলোড হচ্ছে... (প্রসেস বার ক্লাউড সাইড থেকে লিমিটেড)")
            async with session.post(url, data=data) as resp:
                result = await resp.json()
                if result["status"] == "ok":
                    return f"https://gofile.io/d/{result['data']['code']}"
    except Exception as e:
        logger.error(f"Gofile Error: {e}")
    return None

async def upload_to_stream(file_path, status_msg):
    """Stream Server Upload (Fixed DNS/Connection)"""
    if not STREAM_API_KEY: return None
    # ফাইললায়ন্স অনেক সময় ব্লক থাকে, তাই আমরা streamwish ব্যবহার করার চেষ্টা করব
    api_servers = ["https://api.streamwish.com/api/upload/server", "https://filelions.live/api/upload/server"]
    
    for api_url in api_servers:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{api_url}?key={STREAM_API_KEY}", timeout=10) as resp:
                    res = await resp.json()
                    upload_url = res.get("result")
                
                if upload_url:
                    data = aiohttp.FormData()
                    data.add_field('key', STREAM_API_KEY)
                    data.add_field('file', open(file_path, 'rb'), filename=os.path.basename(file_path))
                    
                    await status_msg.edit_text(f"📤 Stream সার্ভারে পাঠানো হচ্ছে... ({api_url.split('.')[1]})")
                    async with session.post(upload_url, data=data, timeout=600) as resp:
                        res = await resp.json()
                        if res.get("msg") == "OK":
                            file_code = res['result'][0]['filecode']
                            domain = "streamwish.com" if "streamwish" in api_url else "filelions.live"
                            return f"https://{domain}/{file_code}"
        except Exception as e:
            logger.error(f"Stream Server ({api_url}) Error: {e}")
            continue # একটি ফেইল করলে পরেরটা ট্রাই করবে
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
        
        # ২. ফাইল ডাউনলোড (প্রোগ্রেস বার সহ)
        start_time = time.time()
        file_path = await message.download(
            progress=progress_bar,
            progress_args=(status_msg, start_time, "📥 টেলিগ্রাম থেকে ডাউনলোড হচ্ছে...")
        )
        
        # ৩. Gofile আপলোড
        g_link = await upload_to_gofile(file_path, status_msg)
        if g_link:
            convo["links"].append({"label": f"🚀 High Speed: {temp_name}", "url": g_link})
        else:
            await message.reply_text(f"❌ Gofile আপলোড ফেইল হয়েছে ({temp_name})")

        # ৪. Stream আপলোড
        s_link = await upload_to_stream(file_path, status_msg)
        if s_link:
            convo["links"].append({"label": f"📺 Play Online: {temp_name}", "url": s_link})
        else:
            await message.reply_text(f"❌ Stream আপলোড ফেইল হয়েছে ({temp_name})")

        # ৫. ক্লিনআপ
        if os.path.exists(file_path): os.remove(file_path)
        await status_msg.edit_text(f"✅ **{temp_name}** এর কাজ শেষ!")
                
    except Exception as e:
        logger.error(f"Final Patch Error: {e}")
        await status_msg.edit_text(f"❌ এরর: {str(e)}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

async def register(bot: Client):
    __main__.patched_process_file_upload = patched_process_file_upload
    __main__.process_file_upload = patched_process_file_upload
    print("🚀 [Plugin] Fixed Multi-Server Uploader Activated!")
