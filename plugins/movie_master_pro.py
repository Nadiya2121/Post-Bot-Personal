# plugins/movie_master_pro.py
import __main__
import asyncio
import json
import re
import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# ==========================================================
# 🔥 ১. সিনেমাটিক HTML ও স্টাইল জেনারেটর (UX ENGINE)
# ==========================================================

def get_pro_css(data):
    backdrop = data.get('backdrop_path')
    bg_url = f"https://image.tmdb.org/t/p/original{backdrop}" if backdrop else ""
    bg_css = f"background-image: linear-gradient(to bottom, rgba(5,6,10,0.85), #05060a), url('{bg_url}');" if bg_url else "background: #05060a;"
    
    return f"""
    <style>
        :root {{ --primary: #E50914; --accent: #00d2ff; --glass: rgba(255, 255, 255, 0.05); }}
        body {{ background: #05060a; {bg_css} background-attachment: fixed; background-size: cover; font-family: 'Segoe UI', sans-serif; color: #eee; margin: 0; padding: 10px; }}
        .app-wrapper {{ max-width: 650px; margin: 20px auto; background: rgba(20, 20, 30, 0.7); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }}
        
        /* 📋 ইনফো টেবিল ডিজাইন */
        .info-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: rgba(0,0,0,0.3); border-radius: 10px; overflow: hidden; }}
        .info-table td {{ padding: 12px; border: 1px solid rgba(255,255,255,0.05); font-size: 14px; }}
        .info-label {{ color: var(--primary); font-weight: bold; text-transform: uppercase; width: 35%; }}
        
        /* 📦 ব্যাচ/সিজন বাটন স্টাইল */
        .batch-section {{ background: linear-gradient(135deg, rgba(229, 9, 20, 0.15), rgba(0, 0, 0, 0.5)); border: 2px dashed var(--primary); border-radius: 15px; padding: 15px; margin: 20px 0; text-align: center; }}
        .batch-title {{ color: #fff; font-size: 18px; font-weight: bold; margin-bottom: 10px; display: block; }}
        .btn-batch {{ background: var(--primary) !important; color: white !important; width: 100% !important; padding: 15px !important; font-size: 16px !important; font-weight: bold !important; border-radius: 10px !important; border: none !important; cursor: pointer; box-shadow: 0 10px 20px rgba(229,9,20,0.4); text-transform: uppercase; }}
        
        /* 🔗 রেগুলার গ্রিড বাটন */
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 15px; }}
        .tg-btn {{ background: rgba(0, 136, 204, 0.2); border: 1px solid #0088cc; color: #fff; padding: 10px; border-radius: 8px; text-align: center; text-decoration: none; font-size: 13px; transition: 0.3s; }}
        .tg-btn:hover {{ background: #0088cc; transform: translateY(-2px); }}
    </style>
    """

# জেনারেটর প্যাচ (Monkey Patch)
if not hasattr(__main__, '_pro_master_patched'):
    original_html_generator = __main__.generate_html_code

    def pro_master_generator(data, links, user_ads, owner_ads, share):
        # ডেটা সংগ্রহ
        title = data.get("title") or data.get("name", "Movie")
        year = (data.get("release_date") or data.get("first_air_date") or "----")[:4]
        lang = data.get('custom_language', 'Dual Audio')
        quality = data.get('custom_quality', 'HD')
        rating = f"{data.get('vote_average', 0):.1f}/10"
        
        # ইনফো টেবিল তৈরি
        info_html = f"""
        <table class="info-table">
            <tr><td class="info-label">📅 Release</td><td>{year}</td></tr>
            <tr><td class="info-label">🗣️ Language</td><td>{lang}</td></tr>
            <tr><td class="info-label">💿 Quality</td><td>{quality}</td></tr>
            <tr><td class="info-label">⭐ Rating</td><td>{rating}</td></tr>
        </table>"""

        # লিঙ্ক বিভাজন (Batch vs Single)
        batch_html = ""
        single_links_html = ""
        
        for lnk in links:
            lbl = lnk.get('label', 'Download')
            url = lnk.get('tg_url') or lnk.get('url', '#')
            
            if lnk.get('is_batch'):
                batch_html += f"""
                <div class="batch-section">
                    <span class="batch-title">📦 {lbl}</span>
                    <button class="btn-batch" onclick="startUnlock(this)">📥 DOWNLOAD FULL BATCH</button>
                    <script>var batch_url = "{url}";</script>
                </div>"""
            else:
                single_links_html += f'<a href="{url}" class="tg-btn">🚀 {lbl}</a>'

        # মেইন বডির পার্টগুলো সাজানো
        html_output = f"""
        {get_pro_css(data)}
        <div class="app-wrapper">
            <div id="view-details">
                <div style="text-align:center;">
                    <div class="movie-title" style="font-size:24px; color:var(--accent); font-weight:bold;">{title} ({year})</div>
                </div>
                {info_html}
                <div class="section-title">📖 Storyline</div>
                <div class="plot-box" style="font-size:14px; line-height:1.6; color:#ccc; text-align:justify;">{data.get('overview', '')}</div>
                
                <div class="section-title">📥 Download Links</div>
                {batch_html}
                <div class="server-grid">{single_links_html}</div>
            </div>
        </div>
        """
        return html_output

    __main__.generate_html_code = pro_master_generator
    __main__._pro_master_patched = True

# ==========================================================
# 🔥 ২. ব্যাচ আপলোড লজিক (CONVERSATION ENGINE)
# ==========================================================

async def register(bot: Client):
    print("💎 PRO Master Plugin (UX + Batch + Table) Registered!")

@bot.on_callback_query(filters.regex("^setlname_batch_"))
async def start_batch(client, cb):
    uid = int(cb.data.split("_")[-1])
    if uid not in __main__.user_conversations: return
    __main__.user_conversations[uid]["state"] = "pro_wait_season"
    await cb.message.edit_text("🔢 কত নম্বর **Season**? (যেমন: Season 01)")

@bot.on_message(filters.private & ~filters.command(["start", "cancel"]))
async def handle_pro_inputs(client, message: Message):
    uid = message.from_user.id
    if uid not in __main__.user_conversations: return
    convo = __main__.user_conversations[uid]
    state = convo.get("state")

    if state == "pro_wait_season":
        convo["temp_season"] = message.text
        convo["state"] = "pro_wait_title"
        await message.reply_text(f"✅ সিজন: **{message.text}**\n\n📝 ব্যাচের টাইটেল দিন (যেমন: Episodes 01-10):")

    elif state == "pro_wait_title":
        convo["temp_batch_title"] = message.text
        convo["state"] = "pro_collect_files"
        convo["pro_batch_files"] = []
        await message.reply_text("🚀 **ব্যাচ মোড অ্যাক্টিভ!**\nসব ফাইল ফরোয়ার্ড করুন। শেষ হলে `/done` লিখুন।")

    elif state == "pro_collect_files":
        if message.text == "/done":
            if not convo.get("pro_batch_files"): return await message.reply_text("⚠️ ফাইল দিন!")
            
            b_id = str(uuid.uuid4())[:8]
            b_label = f"{convo['temp_season']} | {convo['temp_batch_title']}"
            
            convo["links"].append({
                "label": b_label,
                "tg_url": f"https://t.me/{(await client.get_me()).username}?start=batch_{b_id}",
                "is_batch": True,
                "file_ids": convo["pro_batch_files"]
            })
            convo["state"] = "ask_links"
            await message.reply_text(f"✅ ব্যাচ সম্পন্ন! ফাইল সংখ্যা: {len(convo['pro_batch_files'])}\nআর কি লিঙ্ক অ্যাড করবেন?", 
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Another", callback_data=f"lnk_yes_{uid}"), InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]]))
        
        elif message.video or message.document:
            try:
                copied = await message.copy(chat_id=__main__.DB_CHANNEL_ID)
                convo["pro_batch_files"].append(copied.id)
                await message.reply_text(f"✅ ফাইল {len(convo['pro_batch_files'])} যুক্ত হয়েছে।", quote=True)
            except: pass

# ==========================================================
# 🔥 ৩. মাল্টি-ফাইল ডেলিভারি (DELIVERY ENGINE)
# ==========================================================

@bot.on_message(filters.command("start") & filters.private)
async def pro_delivery_handler(client, message: Message):
    if len(message.command) > 1 and message.command[1].startswith("batch_"):
        b_ref = message.command[1].split("_")[1]
        post = await __main__.posts_col.find_one({"links.tg_url": {"$regex": b_ref}})
        
        if not post: return await message.reply_text("❌ ব্যাচ পাওয়া যায়নি।")
        
        target = next((l for l in post["links"] if b_ref in l.get("tg_url", "")), None)
        if target and "file_ids" in target:
            await message.reply_text(f"📦 **{target['label']}** এর সব ফাইল পাঠানো হচ্ছে...")
            for f_id in target["file_ids"]:
                try:
                    await client.copy_message(message.chat.id, __main__.DB_CHANNEL_ID, f_id)
                    await asyncio.sleep(0.5)
                except: continue
            await message.reply_text("✅ সব ফাইল পাঠানো শেষ।")
