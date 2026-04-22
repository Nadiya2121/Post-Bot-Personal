# plugins/movie_master_pro.py
import __main__
import asyncio
import json
import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# --- 🎨 ডিজাইনের কনস্ট্যান্ট (আপনার আগের ডিজাইন অনুযায়ী) ---
TOP_BORDER = "╔════════════════════════╗"
MID_BORDER = "╠════════════════════════╝"
BTM_BORDER = "╚════════════════════════╝"
BULLET = "╟"

# ==========================================================
# 🔥 প্রো জেনারেটর ইঞ্জিন (CSS & HTML)
# ==========================================================

def get_pro_style(data):
    backdrop = data.get('backdrop_path')
    bg_url = f"https://image.tmdb.org/t/p/original{backdrop}" if backdrop else ""
    bg_css = f"background-image: linear-gradient(to bottom, rgba(5,6,10,0.85), #05060a), url('{bg_url}');" if bg_url else "background: #05060a;"
    
    return f"""
    <style>
        :root {{ --primary: #E50914; --accent: #00d2ff; }}
        body {{ background: #05060a; {bg_css} background-attachment: fixed; background-size: cover; font-family: 'Segoe UI', sans-serif; color: #eee; margin: 0; padding: 10px; }}
        .app-wrapper {{ max-width: 650px; margin: 20px auto; background: rgba(20, 20, 30, 0.8); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.9); }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; background: rgba(0,0,0,0.4); border-radius: 10px; overflow: hidden; }}
        .info-table td {{ padding: 12px; border: 1px solid rgba(255,255,255,0.05); font-size: 14px; }}
        .info-label {{ color: var(--primary); font-weight: bold; text-transform: uppercase; }}
        .batch-section {{ background: linear-gradient(135deg, rgba(229, 9, 20, 0.2), rgba(0, 0, 0, 0.6)); border: 2px dashed var(--primary); border-radius: 15px; padding: 20px; margin: 20px 0; text-align: center; }}
        .btn-batch {{ background: var(--primary) !important; color: white !important; width: 100% !important; padding: 18px !important; font-size: 18px !important; font-weight: bold !important; border-radius: 12px !important; border: none !important; cursor: pointer; text-transform: uppercase; box-shadow: 0 10px 20px rgba(229,9,20,0.4); }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; margin-top: 15px; }}
        .tg-btn {{ background: rgba(0, 136, 204, 0.2); border: 1px solid #0088cc; color: #fff; padding: 12px; border-radius: 8px; text-align: center; text-decoration: none; font-size: 13px; transition: 0.3s; font-weight: bold; }}
        .nsfw-blur {{ filter: blur(35px); transition: 0.5s; }}
        .nsfw-blur:hover {{ filter: blur(0px); }}
    </style>
    """

# ==========================================================
# 🔥 ২. মাস্টার প্লাগিন রেজিস্ট্রেশন (এটি সব হ্যান্ডেল করবে)
# ==========================================================

async def register(bot: Client):
    # বটের ডিটেইলস নেওয়া
    me = await bot.get_me()
    bot_username = me.username

    # ১. ক্যাপশন জেনারেটর রিপ্লেস করা (টেলিগ্রাম পোস্টের জন্য)
    def master_caption(details, pid=None):
        title = details.get("title") or details.get("name") or "N/A"
        year = (details.get("release_date") or details.get("first_air_date") or "----")[:4]
        rating = f"⭐ {details.get('vote_average', 0):.1f}/10"
        lang = details.get("custom_language", "Dual Audio")
        quality = details.get("custom_quality", "HD")
        is_adult = details.get('adult', False) or details.get('force_adult', False)
        
        caption = f"✨ **{TOP_BORDER}**\n"
        caption += f"🎬 **{title.upper()} ({year})**\n"
        if pid: caption += f"🆔 `ID: {pid}`\n"
        caption += f"**{MID_BORDER}**\n\n"
        
        if is_adult: caption += "🔞 **ADULT CONTENT (18+)**\n\n"
        caption += f"{BULLET} 🗣️ **Language:** {lang}\n"
        caption += f"{BULLET} 💿 **Quality:** {quality}\n"
        caption += f"{BULLET} {rating}\n\n"
        
        if details.get("overview"):
            caption += f"📝 **Story:** _{details.get('overview')[:150]}..._\n\n"
        
        caption += f"**{BTM_BORDER}**\n"
        caption += f"✨ _Join: @{bot_username}_"
        return caption

    # ২. এইচটিএমএল জেনারেটর রিপ্লেস করা (ওয়েবসাইটের জন্য)
    def master_html_generator(data, links, user_ads, owner_ads, share):
        title = data.get("title") or data.get("name", "Movie")
        year = (data.get("release_date") or data.get("first_air_date") or "----")[:4]
        lang = data.get('custom_language', 'Dual Audio')
        quality = data.get('custom_quality', 'HD')
        rating = f"{data.get('vote_average', 0):.1f}/10"
        poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}"
        is_adult = data.get('adult', False) or data.get('force_adult', False)

        info_table = f"""
        <table class="info-table">
            <tr><td class="info-label">📅 Release</td><td>{year}</td></tr>
            <tr><td class="info-label">🗣️ Language</td><td>{lang}</td></tr>
            <tr><td class="info-label">💿 Quality</td><td>{quality}</td></tr>
            <tr><td class="info-label">⭐ Rating</td><td>{rating}</td></tr>
        </table>"""

        batch_html = ""
        single_html = ""
        for lnk in links:
            lbl, url = lnk.get('label', 'Download'), lnk.get('tg_url') or lnk.get('url', '#')
            if lnk.get('is_batch'):
                batch_html += f'<div class="batch-section"><span style="color:#fff;font-weight:bold;display:block;margin-bottom:10px;">📦 {lbl}</span><button class="btn-batch" onclick="startUnlock(this)">📥 DOWNLOAD FULL BATCH</button></div>'
            else:
                single_html += f'<a href="{url}" class="tg-btn">🚀 {lbl}</a>'

        poster_img = f'<div style="text-align:center;margin-bottom:20px;"><img src="{poster}" class="{"nsfw-blur" if is_adult else ""}" style="width:200px;border-radius:10px;box-shadow:0 10px 30px #000;"></div>'

        return f"""
        {get_pro_style(data)}
        <div class="app-wrapper">
            <div class="movie-title" style="font-size:24px;color:#00d2ff;font-weight:bold;text-align:center;margin-bottom:15px;">{title} ({year})</div>
            {poster_img}
            {info_table}
            <div style="border-left:4px solid #E50914;padding-left:15px;margin:20px 0;color:#ccc;font-size:14px;">{data.get('overview','')}</div>
            <div style="font-weight:bold;color:#E50914;margin-bottom:10px;">📥 DOWNLOAD LINKS</div>
            {batch_html}
            <div class="server-grid">{single_html}</div>
        </div>"""

    # মেইন জেনারেটরগুলো প্যাচ করা
    __main__.generate_formatted_caption = master_caption
    __main__.generate_html_code = master_html_generator

    # --- হ্যান্ডলারগুলো register ফাংশনের ভেতর নিয়ে আসা হয়েছে এরর এড়াতে ---
    
    @bot.on_callback_query(filters.regex("^setlname_batch_"))
    async def start_batch(client, cb):
        uid = cb.from_user.id
        if uid not in __main__.user_conversations: return
        __main__.user_conversations[uid]["state"] = "wait_s_num"
        await cb.message.edit_text("🔢 কত নম্বর **Season**? (যেমন: Season 01)")

    @bot.on_message(filters.private & ~filters.command(["start", "cancel"]))
    async def handle_inputs(client, message: Message):
        uid = message.from_user.id
        if uid not in __main__.user_conversations: return
        convo = __main__.user_conversations[uid]
        state = convo.get("state")

        if state == "wait_s_num":
            convo["temp_s"] = message.text
            convo["state"] = "wait_b_title"
            await message.reply_text(f"✅ সিজন: {message.text}\n📝 ব্যাচের টাইটেল দিন (যেমন: Episodes 01-10):")
        elif state == "wait_b_title":
            convo["temp_bt"] = message.text
            convo["state"] = "collect_b_files"
            convo["b_files"] = []
            await message.reply_text("🚀 **ব্যাচ মোড!** সব ফাইল ফরোয়ার্ড করুন। শেষ হলে `/done` লিখুন।")
        elif state == "collect_b_files":
            if message.text == "/done":
                if not convo.get("b_files"): return await message.reply_text("⚠️ ফাইল দিন!")
                b_id = str(uuid.uuid4())[:8]
                convo["links"].append({"label": f"{convo['temp_s']} | {convo['temp_bt']}", "tg_url": f"https://t.me/{bot_username}?start=batch_{b_id}", "is_batch": True, "f_ids": convo["b_files"]})
                convo["state"] = "ask_links"
                await message.reply_text("✅ ব্যাচ সম্পন্ন!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]]))
            elif message.video or message.document:
                cp = await message.copy(chat_id=__main__.DB_CHANNEL_ID)
                convo["b_files"].append(cp.id)
                await message.reply_text(f"✅ ফাইল {len(convo['b_files'])} যুক্ত হয়েছে।", quote=True)

    @bot.on_message(filters.command("start") & filters.private)
    async def delivery(client, message: Message):
        if len(message.command) > 1 and message.command[1].startswith("batch_"):
            ref = message.command[1].split("_")[1]
            post = await __main__.posts_col.find_one({"links.tg_url": {"$regex": ref}})
            if not post: return await message.reply_text("❌ ব্যাচ পাওয়া যায়নি।")
            target = next((l for l in post["links"] if ref in l.get("tg_url", "")), None)
            if target and "f_ids" in target:
                await message.reply_text(f"📦 **{target['label']}** পাঠানো হচ্ছে...")
                for fid in target["f_ids"]:
                    try:
                        await client.copy_message(message.chat.id, __main__.DB_CHANNEL_ID, fid)
                        await asyncio.sleep(0.5)
                    except: continue
    
    print("🚀 MASTER PRO (FINAL STABLE VERSION) Activated!")
