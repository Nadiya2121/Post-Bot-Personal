# -*- coding: utf-8 -*-
import sys
import json
import base64
import random
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram import filters
from pyrogram.errors import StopPropagation
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =======================================================
# 🎨 ১. ADVANCED PRO UI (HTML GENERATOR)
# =======================================================
def advance_pro_ui(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    title = data.get("title") or data.get("name") or "Movie"
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    backdrop = f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get('backdrop_path') else poster
    is_adult = data.get('adult', False) or data.get('force_adult', False)
    
    lang_str = data.get('custom_language', 'Dual Audio').strip()
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    rating = f"{data.get('vote_average', 0):.1f}/10"
    runtime = f"{data.get('runtime', 'N/A')} min"
    
    genres = ", ".join([g['name'] for g in data.get('genres', [])]) if data.get('genres') else "N/A"

    dl_links_html = ""
    watch_online_html = ""
    episodes_html = ""
    quality_groups = {"480p": [], "720p": [], "1080p": [], "4k": []}
    batch_files = []

    for link in links:
        lbl = link.get('label', '').strip()
        lbl_lower = lbl.lower()
        
        if lbl_lower in ["watch online", "play"]:
            u = link.get('tg_url') or link.get('url')
            e = base64.b64encode(u.encode()).decode()
            watch_online_html = f'''
            <div class="watch-online-box">
                <button class="watch-btn" onclick="goToLink('{e}')">▶ WATCH ONLINE</button>
                <div style="font-size:11px; color:#aaa; margin-top:5px;">Stream instantly in High Quality</div>
            </div>
            '''
            continue

        found_q = False
        for q in ["480", "720", "1080", "4k"]:
            if q in lbl_lower:
                quality_groups[q if "4k" in q else q+"p"].append(link)
                found_q = True
                break
        
        if not found_q:
            batch_files.append(link)

    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_links_html += f'<div class="quality-title">📺 {q_name.upper()} DOWNLOAD LINKS</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
                server_label = l.get("label", "Server").replace(q_name, "").strip() or "Telegram Server"
                btn_content = f'<div class="dl-btn-title">⬇️ Download {q_name.upper()}</div><div class="dl-btn-server">{server_label}</div>'
                dl_links_html += f'<button class="final-server-btn" onclick="goToLink(\'{e}\')">{btn_content}</button>'
            dl_links_html += '</div>'

    if batch_files:
        episodes_html += '<div class="quality-title" style="border-left-color:#00e676;">📁 EPISODES / BATCH FILES</div><div class="episode-list">'
        for idx, l in enumerate(batch_files):
            u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
            label = l.get("label", f"Episode {idx+1}")
            episodes_html += f'<button class="episode-btn" onclick="goToLink(\'{e}\')"><span class="ep-icon">🎬</span> <span class="ep-name">{label}</span> <span class="ep-dl">⬇️ Get</span></button>'
        episodes_html += '</div>'

    ss_html = ""
    screenshots = data.get('manual_screenshots') or [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in data.get('images', {}).get('backdrops', [])[:6]]
    if screenshots:
        imgs = ""
        for img in screenshots:
            if is_adult: imgs += f'<div class="nsfw-container" onclick="revealNSFW(this)"><img src="{img}" class="nsfw-blur"><div class="nsfw-warning">🔞 18+</div></div>'
            else: imgs += f'<img src="{img}" alt="Screenshot">'
        ss_html = f'<div class="section-title">📸 Screenshots</div><div class="screenshot-grid">{imgs}</div>'

    weighted_ads = user_ad_links_list if user_ad_links_list else (owner_ad_links_list or ["https://google.com"])
    random.shuffle(weighted_ads)

    return f"""
<div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title}" /></div>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    body {{ margin: 0; padding: 0; background: #05060a !important; background-image: linear-gradient(to bottom, rgba(5,6,10,0.85), #05060a), url('{backdrop}') !important; background-attachment: fixed !important; background-size: cover !important; background-position: center !important; font-family: 'Poppins', sans-serif; }}
    .rgb-box {{ max-width: 800px; margin: 20px auto; position: relative; padding: 3px; border-radius: 20px; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rotateRGB 6s linear infinite; }}
    @keyframes rotateRGB {{ 0% {{ background-position: 0% 50%; }} 100% {{ background-position: 100% 50%; }} }}
    .app-wrapper {{ background: #0f1014; border-radius: 17px; padding: 25px; color: #e0e0e0; z-index: 1; position: relative; }}
    .movie-title {{ font-family: 'Oswald', sans-serif; font-size: 30px; color: #fff; text-align: center; text-transform: uppercase; margin-bottom: 20px; }}
    .info-box {{ display: flex; gap: 20px; margin-bottom: 25px; }}
    .info-poster img {{ width: 150px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.6); }}
    .info-text {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; width: 100%; }}
    .info-item {{ background: rgba(255,255,255,0.04); padding: 10px; border-radius: 8px; border-left: 3px solid #E50914; font-size: 13px; color: #fff; }}
    .info-item span {{ display: block; color: #888; font-size: 10px; text-transform: uppercase; font-weight: 600; margin-bottom: 3px; }}
    @media (max-width: 500px) {{ .info-box {{ flex-direction: column; align-items: center; }} .info-poster img {{ width: 140px; }} }}
    .section-title {{ font-size: 16px; color: #fff; margin: 25px 0 15px; border-bottom: 2px solid #E50914; display: inline-block; padding-bottom: 4px; font-weight: 600; text-transform: uppercase; }}
    .plot-box {{ background: rgba(255,255,255,0.03); padding: 15px; border-radius: 8px; font-size: 13px; line-height: 1.7; color: #ccc; border: 1px solid rgba(255,255,255,0.05); text-align: justify; }}
    .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; margin-bottom: 20px; }}
    .screenshot-grid img {{ width: 100%; height: 85px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; cursor: pointer; }}
    .screenshot-grid img:hover {{ transform: scale(1.08); z-index: 5; border-color: #E50914; box-shadow: 0 5px 15px rgba(229,9,20,0.4); }}
    .step-container {{ background: rgba(0,0,0,0.5); padding: 25px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.05); overflow: hidden; position: relative; margin-top: 25px; }}
    .step-title {{ color: #ff5252; font-size: 14px; font-weight: 600; letter-spacing: 1px; margin-bottom: 15px; text-transform: uppercase; }}
    .unlock-btn {{ background: #E50914; color: #fff; border: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; width: 100%; box-shadow: 0 5px 15px rgba(229, 9, 20, 0.4); }}
    .unlock-btn:disabled {{ background: #555 !important; cursor: not-allowed; box-shadow: none; transform: none !important; }}
    .unlock-btn:hover:not(:disabled) {{ transform: scale(1.02); background: #f40612; }}
    #unlock-timer {{ width: 0%; height: 5px; background: linear-gradient(90deg, #E50914, #00e676); position: absolute; bottom: 0; left: 0; transition: width 5s linear; }}
    .quality-title {{ background: rgba(229, 9, 20, 0.1); border-left: 4px solid #E50914; border-radius: 4px; padding: 8px 15px; font-size: 13px; font-weight: 600; color: #fff; margin-top: 25px; text-transform: uppercase; }}
    .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 15px; }}
    .final-server-btn {{ background: #1a1c22; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 12px; cursor: pointer; transition: 0.3s; display: flex; flex-direction: column; align-items: center; width: 100%; }}
    .final-server-btn:hover {{ background: rgba(229, 9, 20, 0.1); border-color: #E50914; transform: translateY(-3px); }}
    .dl-btn-title {{ color: #fff; font-size: 13px; font-weight: 600; margin-bottom: 4px; }}
    .dl-btn-server {{ color: #888; font-size: 11px; text-transform: uppercase; background: rgba(0,0,0,0.3); padding: 2px 8px; border-radius: 4px; }}
    .watch-online-box {{ text-align: center; margin: 20px 0; background: rgba(255,255,255,0.02); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }}
    .watch-btn {{ background: #fff; color: #000; border: none; padding: 15px 40px; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.3s; box-shadow: 0 5px 20px rgba(255,255,255,0.2); display: inline-flex; align-items: center; gap: 10px; }}
    .watch-btn:hover {{ background: #E50914; color: #fff; transform: scale(1.05); box-shadow: 0 5px 20px rgba(229, 9, 20, 0.4); }}
    .episode-list {{ display: flex; flex-direction: column; gap: 8px; margin-top: 15px; }}
    .episode-btn {{ background: #1a1c22; border: 1px solid rgba(255,255,255,0.05); padding: 12px 15px; border-radius: 8px; color: #fff; display: flex; justify-content: space-between; align-items: center; cursor: pointer; transition: 0.2s; }}
    .episode-btn:hover {{ background: rgba(0, 230, 118, 0.1); border-color: #00e676; padding-left: 20px; }}
    .ep-icon {{ font-size: 16px; }}
    .ep-name {{ flex: 1; text-align: left; margin: 0 15px; font-size: 13px; font-weight: 500; color: #ccc; }}
    .ep-dl {{ font-size: 11px; background: #00e676; color: #000; padding: 3px 10px; border-radius: 12px; font-weight: bold; }}
    .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
    .badge {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #ccc; font-size: 11px; padding: 4px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase; }}
</style>

<div class="rgb-box">
    <div class="app-wrapper">
        <div id="view-details">
            <div class="media-badges"><div class="badge">{lang_str}</div><div class="badge">⭐ {rating}</div><div class="badge">{year}</div></div>
            <div class="movie-title">{title}</div>
            
            <div class="info-box">
                <div class="info-poster"><img src="{poster}" alt="Poster"></div>
                <div class="info-text">
                    <div class="info-item"><span>⭐ Rating</span> {rating}</div>
                    <div class="info-item"><span>🎭 Genre</span> {genres}</div>
                    <div class="info-item"><span>🗣️ Audio</span> {lang_str}</div>
                    <div class="info-item"><span>⏱️ Runtime</span> {runtime}</div>
                    <div class="info-item"><span>📅 Release</span> {year}</div>
                </div>
            </div>
            
            <div class="section-title">📖 Storyline</div>
            <div class="plot-box">{overview}</div>
            {ss_html}

            <div class="step-container" id="step-box">
                <div class="step-title" id="st-txt">STEP 1: VERIFICATION</div>
                <button class="unlock-btn" id="st-btn" onclick="processUnlock()">🔓 CLICK TO VERIFY (STEP 1)</button>
                <div id="unlock-timer"></div>
            </div>
        </div>

        <div id="view-links" style="display:none;">
            <div style="text-align:center; color:#00e676; font-size:15px; font-weight:bold; margin-bottom:20px; border:1px solid rgba(0,230,118,0.3); padding:15px; border-radius:8px; background:rgba(0,230,118,0.05);">✅ ALL LINKS UNLOCKED SUCCESSFULLY!</div>
            {watch_online_html}
            {dl_links_html}
            {episodes_html}
        </div>
    </div>
</div>

<script>
const AD_LINKS = {json.dumps(weighted_ads)};
let currentStep = 1;

function processUnlock() {{
    let btn = document.getElementById('st-btn');
    let title = document.getElementById('st-txt');
    let timerBar = document.getElementById('unlock-timer');
    window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
    
    if (currentStep === 1) {{
        btn.disabled = true;
        btn.innerHTML = "⏳ Verifying Step 1...";
        timerBar.style.width = "100%";
        setTimeout(() => {{
            currentStep = 2;
            btn.disabled = false;
            btn.innerHTML = "🔓 FINAL UNLOCK (STEP 2)";
            title.innerHTML = "STEP 2: FINAL VERIFICATION";
            timerBar.style.transition = 'none';
            timerBar.style.width = "0%";
            setTimeout(() => timerBar.style.transition = 'width 5s linear', 50);
        }}, 5000);
    }} else if (currentStep === 2) {{
        btn.disabled = true;
        btn.innerHTML = "⏳ Finalizing Request...";
        timerBar.style.width = "100%";
        setTimeout(() => {{
            document.getElementById('view-details').style.display = 'none';
            document.getElementById('view-links').style.display = 'block';
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}, 5000);
    }}
}}
function goToLink(e) {{ window.location.href = atob(e); }}
function revealNSFW(c) {{ c.querySelector('img').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}
</script>
"""

# =======================================================
# ⚙️ ২. BOT LOGIC INTERCEPTOR (MAGIC PLUGIN)
# =======================================================

async def intercept_finish_btn(client, cb):
    """
    ইউজার যখন Finish বাটনে ক্লিক করবে (lnk_no বা gen_edit), তখন 
    এই ফাংশনটি মেইন কোডকে থামিয়ে দিয়ে নিজে রান করবে!
    """
    try:
        import __main__
        uid = int(cb.data.split("_")[-1])
        
        if uid in __main__.user_conversations:
            convo = __main__.user_conversations[uid]
            
            # চেক করবে ইউজার আগে থেকেই Watch Online এড করেছে কিনা
            has_watch = any(l.get("label", "").strip().lower() in ["watch online", "play"] for l in convo.get("links", []))
            
            # যদি আগে এড করা না থাকে, তাহলে পপআপ দেখাবে
            if not has_watch:
                is_edit = cb.data.startswith("gen_edit")
                tag = "edit_" if is_edit else ""
                
                btns = [
                    [InlineKeyboardButton("▶️ হ্যাঁ, Watch Online এড করবো", callback_data=f"watch_yes_{tag}{uid}")],
                    [InlineKeyboardButton("⏭️ না, ফিনিশ করুন", callback_data=f"watch_no_{tag}{uid}")]
                ]
                await cb.message.edit_text("▶️ **Watch Online Link:**\n\nআপনি কি মুভিটি অনলাইনে প্লে করার জন্য ডিরেক্ট ভিডিও লিঙ্ক (Watch Online) যুক্ত করতে চান?", reply_markup=InlineKeyboardMarkup(btns))
                
                # মেইন কোড যাতে রান না করে তাই StopPropagation
                raise StopPropagation()
    except StopPropagation:
        raise
    except Exception as e:
        pass

async def watch_yes_cb(client, cb):
    try:
        import __main__
        uid = int(cb.data.split("_")[-1])
        if uid in __main__.user_conversations:
            is_edit = "edit_" in cb.data
            __main__.user_conversations[uid]["state"] = "wait_watch_url_edit" if is_edit else "wait_watch_url"
            __main__.user_conversations[uid]["temp_name"] = "Watch Online"
            
            await cb.message.edit_text("🔗 **Watch Online URL:**\n\nদয়া করে ভিডিওটির ডিরেক্ট প্লে লিঙ্ক বা ড্রাইভ লিঙ্কটি দিন:")
            raise StopPropagation()
    except StopPropagation: raise
    except: pass

async def watch_no_cb(client, cb):
    try:
        import __main__
        uid = int(cb.data.split("_")[-1])
        if uid in __main__.user_conversations:
            is_edit = "edit_" in cb.data
            if is_edit:
                await cb.answer("⏳ Generating...", show_alert=False)
                await __main__.generate_final_post(client, uid, cb.message)
            else:
                __main__.user_conversations[uid]["state"] = "wait_badge_text"
                await cb.message.edit_text("🖼️ **Badge Text?**\n\nলিখে পাঠান অথবা Skip করুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Skip", callback_data=f"skip_badge_{uid}")]]))
            raise StopPropagation()
    except StopPropagation: raise
    except: pass

async def watch_url_handler(client, message):
    try:
        import __main__
        uid = message.from_user.id
        if uid in __main__.user_conversations:
            convo = __main__.user_conversations[uid]
            state = convo.get("state")
            
            if state in ["wait_watch_url", "wait_watch_url_edit"]:
                url = message.text.strip()
                if url.startswith("http"):
                    convo["links"].append({"label": "Watch Online", "url": url, "is_grouped": False})
                    is_edit = state == "wait_watch_url_edit"
                    
                    if is_edit:
                        convo["state"] = "edit_mode"
                        await message.reply_text("✅ Watch Online Link Added!", reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("➕ Add Another Link", callback_data=f"add_lnk_edit_{uid}"), 
                             InlineKeyboardButton("✅ Generate Post", callback_data=f"gen_edit_{uid}")]
                        ]))
                    else:
                        convo["state"] = "wait_badge_text"
                        await message.reply_text("✅ Watch Online Link Added!\n\n🖼️ **Badge Text?**\n\nলিখে পাঠান অথবা Skip করুন:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Skip", callback_data=f"skip_badge_{uid}")]]))
                else:
                    await message.reply_text("⚠️ Invalid Input. URL required. Start with http/https")
                
                raise StopPropagation()
    except StopPropagation: raise
    except: pass

# =======================================================
# 🚀 ৩. PLUGIN REGISTER
# =======================================================
async def register(bot):
    # ১. মেইন কোডের HTML জেনারেটর পরিবর্তন
    import __main__
    __main__.generate_html_code = advance_pro_ui

    # ২. মেইন কোড বাইপাস করে নতুন লজিক বসানো (Group -1)
    bot.add_handler(CallbackQueryHandler(intercept_finish_btn, filters.regex("^(lnk_no|gen_edit)_")), group=-1)
    bot.add_handler(CallbackQueryHandler(watch_yes_cb, filters.regex("^watch_yes_")), group=-1)
    bot.add_handler(CallbackQueryHandler(watch_no_cb, filters.regex("^watch_no_")), group=-1)
    bot.add_handler(MessageHandler(watch_url_handler, filters.private & filters.text), group=-1)

    print("🎬 [PLUGIN] WATCH ONLINE AUTO-PROMPT & 2-STEP UI LOADED SUCCESSFULLY!")
