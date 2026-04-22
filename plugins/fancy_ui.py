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

    # --- লিঙ্কগুলো ফিল্টার করা ---
    for link in links:
        lbl = link.get('label', '').strip()
        lbl_lower = lbl.lower()
        
        # Watch Online চেক
        if "watch online" in lbl_lower or "play" in lbl_lower:
            u = link.get('tg_url') or link.get('url')
            e = base64.b64encode(u.encode()).decode()
            watch_online_html = f'''
            <div style="margin-bottom: 25px;">
                <button class="watch-btn" onclick="goToLink('{e}')">
                    <span style="font-size: 24px;">▶</span> 
                    <div style="text-align: left;">
                        <div style="font-size: 16px; font-weight: bold;">WATCH ONLINE</div>
                        <div style="font-size: 11px; font-weight: normal; color: #ddd;">Stream instantly without downloading</div>
                    </div>
                </button>
            </div>
            '''
            continue

        # কোয়ালিটি চেক
        found_q = False
        for q in ["480", "720", "1080", "4k"]:
            if q in lbl_lower:
                quality_groups[q if "4k" in q else q+"p"].append(link)
                found_q = True
                break
        
        if not found_q:
            batch_files.append(link)

    # --- RGB ডাউনলোড বাটন তৈরি ---
    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_links_html += f'<div class="quality-title">📺 {q_name.upper()} QUALITY</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
                server_label = l.get("label", "Server").replace(q_name, "").replace(q_name.upper(), "").strip() or "Telegram Server"
                
                # বাটনের লেখা: Download 1080p ইত্যাদি
                btn_content = f'<div style="font-size:14px; font-weight:bold; color:#fff; margin-bottom:3px;">⬇️ Download {q_name.upper()}</div><div style="font-size:11px; color:#aaa; text-transform:uppercase; background:rgba(0,0,0,0.5); border-radius:4px; padding:2px 5px; display:inline-block;">{server_label}</div>'
                dl_links_html += f'<div class="rgb-btn-wrapper"><button class="rgb-btn" onclick="goToLink(\'{e}\')">{btn_content}</button></div>'
            dl_links_html += '</div>'

    # --- এপিসোড লিস্ট ---
    if batch_files:
        episodes_html += '<div class="quality-title" style="border-left-color:#00e676;">📁 EPISODES / BATCH FILES</div><div class="server-grid">'
        for idx, l in enumerate(batch_files):
            u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
            label = l.get("label", f"Episode {idx+1}")
            btn_content = f'<div style="font-size:13px; font-weight:bold; color:#fff; margin-bottom:3px;">🎬 {label}</div><div style="font-size:11px; color:#00e676;">⬇️ Get File</div>'
            episodes_html += f'<div class="rgb-btn-wrapper"><button class="rgb-btn" onclick="goToLink(\'{e}\')">{btn_content}</button></div>'
        episodes_html += '</div>'

    # --- অন্যান্য HTML ---
    ss_html = ""
    screenshots = data.get('manual_screenshots') or [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in data.get('images', {}).get('backdrops', [])[:6]]
    if screenshots:
        imgs = "".join([f'<img src="{img}" alt="Screenshot">' for img in screenshots])
        ss_html = f'<div class="section-title">📸 Screenshots</div><div class="screenshot-grid">{imgs}</div>'

    weighted_ads = user_ad_links_list if user_ad_links_list else (owner_ad_links_list or ["https://google.com"])
    random.shuffle(weighted_ads)

    return f"""
<div style="height:0px;width:0px;overflow:hidden;display:none;"><img src="{poster}" alt="{title}" /></div>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    body {{ margin: 0; padding: 0; background: #05060a !important; background-image: linear-gradient(to bottom, rgba(5,6,10,0.85), #05060a), url('{backdrop}') !important; background-attachment: fixed !important; background-size: cover !important; background-position: center !important; font-family: 'Poppins', sans-serif; }}
    .app-wrapper {{ max-width: 800px; margin: 20px auto; background: #0f1014; border-radius: 17px; padding: 25px; color: #e0e0e0; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.9); }}
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
    .screenshot-grid img {{ width: 100%; height: 85px; object-fit: cover; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1); }}
    
    /* গাইডলাইন বক্স */
    .guide-box {{ background: rgba(229, 9, 20, 0.05); border: 1px dashed #E50914; padding: 15px; border-radius: 10px; margin-top: 25px; margin-bottom: 20px; }}
    
    /* 2-Step Unlock UI */
    .step-container {{ background: rgba(0,0,0,0.5); padding: 25px; border-radius: 12px; text-align: center; border: 1px solid rgba(255,255,255,0.05); position: relative; overflow: hidden; }}
    .step-title {{ color: #ff5252; font-size: 14px; font-weight: 600; letter-spacing: 1px; margin-bottom: 15px; text-transform: uppercase; }}
    .unlock-btn {{ background: #E50914; color: #fff; border: none; padding: 15px 20px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; width: 100%; box-shadow: 0 5px 15px rgba(229, 9, 20, 0.4); }}
    .unlock-btn:disabled {{ background: #555 !important; cursor: not-allowed; box-shadow: none; }}
    #unlock-timer {{ width: 0%; height: 5px; background: linear-gradient(90deg, #E50914, #00e676); position: absolute; bottom: 0; left: 0; transition: width 5s linear; }}

    /* Watch Online Button */
    .watch-btn {{ background: linear-gradient(90deg, #E50914, #ff5252); color: #fff; border: none; padding: 12px 30px; border-radius: 50px; font-family: 'Poppins', sans-serif; cursor: pointer; transition: 0.3s; box-shadow: 0 5px 20px rgba(229, 9, 20, 0.5); display: inline-flex; align-items: center; gap: 15px; width: 100%; justify-content: center; }}
    .watch-btn:hover {{ transform: scale(1.02); box-shadow: 0 8px 25px rgba(229, 9, 20, 0.7); }}

    /* RGB Download Buttons */
    .quality-title {{ background: rgba(229, 9, 20, 0.1); border-left: 4px solid #E50914; border-radius: 4px; padding: 8px 15px; font-size: 13px; font-weight: 600; color: #fff; margin-top: 25px; text-transform: uppercase; }}
    .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 15px; }} /* Gap কমানো হয়েছে */
    
    .rgb-btn-wrapper {{ position: relative; border-radius: 8px; padding: 2px; background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; animation: glowing 20s linear infinite; }}
    .rgb-btn {{ background: #15161c; width: 100%; height: 100%; border: none; border-radius: 6px; padding: 12px; cursor: pointer; transition: 0.3s; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
    .rgb-btn:hover {{ background: #1a1c22; transform: scale(1.02); }}
    
    @keyframes glowing {{ 0% {{ background-position: 0 0; }} 50% {{ background-position: 400% 0; }} 100% {{ background-position: 0 0; }} }}
    
    .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
    .badge {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #ccc; font-size: 11px; padding: 4px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase; }}
</style>

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

        <!-- ২ স্টেপ গাইডলাইন -->
        <div class="guide-box">
            <div style="color:#E50914; font-weight:bold; font-size:15px; margin-bottom:8px;">🎬 কিভাবে ডাউনলোড করবেন?</div>
            <div style="font-size:13px; color:#aaa; line-height:1.6;">
                ১. নিচের <b>STEP 1</b> বাটনে ক্লিক করুন এবং ৫ সেকেন্ড অপেক্ষা করুন।<br>
                ২. এরপর বাটনটি সবুজ হয়ে <b>STEP 2</b> লেখা আসবে, সেখানে ক্লিক করে আবার ৫ সেকেন্ড অপেক্ষা করুন।<br>
                ৩. ব্যাস! মুভি দেখার এবং ডাউনলোড করার আসল লিংক পেয়ে যাবেন।
            </div>
        </div>

        <div class="step-container" id="step-box">
            <div class="step-title" id="st-txt">STEP 1: VERIFICATION</div>
            <button class="unlock-btn" id="st-btn" onclick="processUnlock()">🔓 UNLOCK LINK (STEP 1)</button>
            <div id="unlock-timer"></div>
        </div>
    </div>

    <div id="view-links" style="display:none;">
        <div style="text-align:center; color:#00e676; font-size:15px; font-weight:bold; margin-bottom:25px; border:1px solid rgba(0,230,118,0.3); padding:15px; border-radius:8px; background:rgba(0,230,118,0.05);">✅ ALL LINKS UNLOCKED SUCCESSFULLY!</div>
        {watch_online_html}
        {dl_links_html}
        {episodes_html}
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
        btn.innerHTML = "⏳ Verifying... Please Wait 5s";
        timerBar.style.width = "100%";
        
        setTimeout(() => {{
            currentStep = 2;
            btn.disabled = false;
            btn.style.background = "#00e676"; // বাটন সবুজ হয়ে যাবে
            btn.style.boxShadow = "0 5px 15px rgba(0, 230, 118, 0.4)";
            btn.innerHTML = "🔓 FINAL UNLOCK (STEP 2)";
            title.innerHTML = "STEP 2: FINAL VERIFICATION";
            title.style.color = "#00e676";
            
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
</script>
"""

# =======================================================
# ⚙️ ২. BOT LOGIC INTERCEPTOR (MAGIC PLUGIN)
# =======================================================

# মেইন কোডকে জোড় করে থামানোর জন্য স্পেশাল হ্যান্ডলার
async def intercept_finish_btn(client, cb):
    try:
        import __main__
        uid = int(cb.data.split("_")[-1])
        
        if uid in __main__.user_conversations:
            convo = __main__.user_conversations[uid]
            
            # চেক করবে ইউজার আগে থেকেই Watch Online এড করেছে কিনা
            has_watch = any("watch online" in l.get("label", "").lower() or "play" in l.get("label", "").lower() for l in convo.get("links", []))
            
            if not has_watch:
                is_edit = cb.data.startswith("gen_edit")
                tag = "edit_" if is_edit else ""
                
                btns = [
                    [InlineKeyboardButton("▶️ হ্যাঁ, Watch Online এড করবো", callback_data=f"watch_yes_{tag}{uid}")],
                    [InlineKeyboardButton("⏭️ না, সরাসরি ফিনিশ করুন", callback_data=f"watch_no_{tag}{uid}")]
                ]
                await cb.message.edit_text("▶️ **Watch Online Link:**\n\nআপনি কি মুভিটি অনলাইনে প্লে করার জন্য ডিরেক্ট ভিডিও লিঙ্ক (Watch Online) যুক্ত করতে চান?", reply_markup=InlineKeyboardMarkup(btns))
                raise StopPropagation() # মেইন কোড থামিয়ে দেবে
    except StopPropagation: raise
    except: pass

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
    # ১. HTML জেনারেটর রিপ্লেস
    import __main__
    __main__.generate_html_code = advance_pro_ui

    # ২. StopPropagation দিয়ে মেইন ফাইলকে বাইপাস করার পাওয়ারফুল সিস্টেম
    bot.add_handler(CallbackQueryHandler(intercept_finish_btn, filters.regex("^(lnk_no|gen_edit)_")), group=-1)
    bot.add_handler(CallbackQueryHandler(watch_yes_cb, filters.regex("^watch_yes_")), group=-1)
    bot.add_handler(CallbackQueryHandler(watch_no_cb, filters.regex("^watch_no_")), group=-1)
    bot.add_handler(MessageHandler(watch_url_handler, filters.private & filters.text), group=-1)

    print("🎬 [PLUGIN] WATCH ONLINE AUTO-PROMPT & 2-STEP UI LOADED SUCCESSFULLY!")
