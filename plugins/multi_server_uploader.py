import os
import asyncio
import aiohttp
import logging
import __main__  # মেইন ফাইলের ভ্যারিয়েবল এক্সেস করার জন্য
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# --- CONFIGURATION (আপনার ইচ্ছা মতো পরিবর্তন করুন) ---
# Stream সার্ভারের জন্য API Key থাকলে এখানে দিন (না থাকলে শুধু Gofile কাজ করবে)
STREAMWISH_API_KEY = "" # উদাহরণ: "4233...your_key" (Streamwish.com এ ফ্রিতে পাবেন)

# --- UPLOADER FUNCTIONS ---

async def upload_to_gofile(file_path):
    """Gofile: No login, supports 5GB+"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gofile.io/getServer") as resp:
                data = await resp.json()
                server = data["data"]["server"] if data["status"] == "ok" else "store1"
            
            url = f"https://{server}.gofile.io/uploadFile"
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f)
                async with session.post(url, data=form) as resp:
                    res = await resp.json()
                    if res["status"] == "ok":
                        return res["data"]["downloadPage"]
    except Exception as e:
        logger.error(f"Gofile Error: {e}")
    return None

async def upload_to_streamwish(file_path):
    """StreamWish: For Streaming experience (Needs API Key)"""
    if not STREAMWISH_API_KEY:
        return None
    try:
        url = "https://streamwish.com/api/upload/server"
        params = {"key": STREAMWISH_API_KEY}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                res = await resp.json()
                upload_url = res.get("result")
                
            if upload_url:
                with open(file_path, 'rb') as f:
                    form = aiohttp.FormData()
                    form.add_field('key', STREAMWISH_API_KEY)
                    form.add_field('file', f)
                    async with session.post(upload_url, data=form) as resp:
                        res = await resp.json()
                        if res.get("msg") == "OK":
                            # Stream লিঙ্ক সাধারণত এভাবে হয়
                            file_code = res['result'][0]['filecode']
                            return f"https://streamwish.com/{file_code}"
    except Exception as e:
        logger.error(f"StreamWish Error: {e}")
    return None

# --- NEW PROCESS FUNCTION (This replaces the one in main.py) ---

async def patched_process_file_upload(client, message, uid, temp_name):
    # মেইন ফাইলের গ্লোবাল ভ্যারিয়েবল গুলো এক্সেস করা
    convo = __main__.user_conversations.get(uid)
    db_channel = __main__.DB_CHANNEL_ID
    upload_semaphore = __main__.upload_semaphore
    
    if not convo: return
    
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text(f"⏳ **প্রসেসিং শুরু:** {temp_name}\n\n1️⃣ টেলিগ্রাম ডিবিতে সেভ হচ্ছে...", quote=True)
    
    try:
        async with upload_semaphore:
            # ১. টেলিগ্রাম চ্যানেলে সেভ (আপনার আগের সিস্টেম)
            copied_msg = await message.copy(chat_id=db_channel)
            bot_username = (await client.get_me()).username
            tg_link = f"https://t.me/{bot_username}?start=get-{copied_msg.id}"
            
            convo["links"].append({
                "label": f"✈️ Telegram: {temp_name}", 
                "tg_url": tg_link, 
                "is_grouped": False
            })
            
            await status_msg.edit_text(f"✅ টেলিগ্রাম সেভ ডান!\n\n2️⃣ এখন ক্লাউড সার্ভারে আপলোড হচ্ছে (Gofile & Stream)...")

            # ২. ফাইল ডাউনলোড করা (সার্ভারে আপলোডের জন্য)
            file_path = await message.download()
            
            # ৩. মাল্টিপল সার্ভারে আপলোড (Parallel Upload)
            gofile_task = upload_to_gofile(file_path)
            stream_task = upload_to_streamwish(file_path)
            
            g_link, s_link = await asyncio.gather(gofile_task, stream_task)
            
            # ৪. লিঙ্কগুলো কনভারসেশনে যুক্ত করা
            if g_link:
                convo["links"].append({
                    "label": f"🚀 High Speed: {temp_name}", 
                    "url": g_link, 
                    "is_grouped": False
                })
            
            if s_link:
                convo["links"].append({
                    "label": f"📺 Play Online: {temp_name}", 
                    "url": s_link, 
                    "is_grouped": False
                })

            # ৫. লোকাল ফাইল ডিলিট
            if os.path.exists(file_path):
                os.remove(file_path)

            await status_msg.edit_text(f"✅ **সব সার্ভারে আপলোড সফল!**\n📦 ফাইল: {temp_name}\n\nআপনি চাইলে আরও ফাইল দিতে পারেন বা Finish এ ক্লিক করুন।")
                
    except Exception as e:
        logger.error(f"Patch Upload Error: {e}")
        await status_msg.edit_text(f"❌ এরর হয়েছে: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

# --- PLUGIN REGISTRATION ---

async def register(bot: Client):
    # মেইন ফাইলের ফাংশনকে রিপ্লেস বা প্যাচ করা (Magic Bypass)
    __main__.process_file_upload = patched_process_file_upload
    print("🔥 [Plugin] process_file_upload has been patched with Multi-Server Support!")
