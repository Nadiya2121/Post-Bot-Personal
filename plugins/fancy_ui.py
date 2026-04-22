# -*- coding: utf-8 -*-
import sys
import json
import base64
import random
from pyrogram.errors import MessageNotModified

# --- ফাইনাল জেনারেটর ফাংশন ---
def final_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # --- মুভির তথ্য প্রসেসিং (মেইন কোড লজিক) ---
    title = data.get("title") or data.get("name") or "Movie"
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    is_adult = data.get('adult', False) or data.get('force_adult', False)
    theme = data.get("theme", "netflix")

    if data.get('is_manual'):
        genres_str = "Unknown / Custom"; year = "N/A"; rating = "N/A"; runtime_str = "N/A"; cast_names = "N/A"
    else:
        genres_list = [g['name'] for g in data.get('genres',[])]
        genres_str = ", ".join(genres_list) if genres_list else "Movie"
        year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
        rating = f"{data.get('vote_average', 0):.1f}/10"
        runtime = data.get('runtime') or (data.get('episode_run_time',[0])[0] if data.get('episode_run_time') else "N/A")
        runtime_str = f"{runtime} min" if runtime != "N/A" else "N/A"
        cast_list = data.get('credits', {}).get('cast',[])
        cast_names = ", ".join([c['name'] for c in cast_list[:4]]) if cast_list else "Unknown"

    lang_str = data.get('custom_language', 'Dual Audio').strip()

    # --- থিম অনুযায়ী অ্যাকসেন্ট কালার ---
    accent = "#E50914" if theme == "netflix" else "#00A8E1" if theme == "prime" else "#6200ea"
    
    # --- ট্রেইলার সেকশন ---
    trailer_html = ""
    videos = data.get('videos', {}).get('results',[])
    tk = next((v['key'] for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube'), None)
    if tk:
        trailer_html = f'<div class="section-title">🎬 OFFICIAL TRAILER</div><div class="video-container"><iframe src="https://www.youtube.com/embed/{tk}" allowfullscreen></iframe></div>'

    # --- স্ক্রিনশট সেকশন (NSFW সাপোর্ট সহ) ---
    screenshots = data.get('manual_screenshots',[])
    if not screenshots and not data.get('is_manual'):
        screenshots = [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in data.get('images', {}).get('backdrops', [])[:6]]
    
    ss_html = ""
    if screenshots:
        ss_grid = ""
        for img in screenshots:
            if is_adult:
                ss_grid += f'<div class="nsfw-box" onclick="this.classList.toggle(\'reveal\')"><img src="{img}" class="blur-img"><div class="nsfw-tag">🔞 18+ Click to View</div></div>'
            else:
                ss_grid += f'<img src="{img}" class="ss-img">'
        ss_html = f'<div class="section-title">📸 SCREENSHOTS</div><div class="ss-grid">{ss_grid}</div>'

    # --- লিঙ্ক গ্রুপিং লজিক (Watch, Download, Original) ---
    watch_html, dl_html = "", ""
    quality_groups = {"💎 4K ULTRA HD": [], "🎬 1080P FULL HD": [], "📽️ 720P HD": [], "📀 480P SD": [], "📁 TELEGRAM FILES": []}
    original_files = []

    for link in links:
        lbl = link.get('label', '').upper()
        url = link.get('tg_url') or link.get('url', '')
        enc = base64.b64encode(url.encode()).decode()
        
        btn_tag = f'<button class="final-btn" onclick="goToLink(\'{enc}\')">'
        
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_html += f'{btn_tag}▶️ {link.get("label")} - Stream Online</button>'
        elif "ORIGINAL" in lbl:
            original_files.append(link)
        else:
            found = False
            for q in ["4K", "1080", "720", "480"]:
                if q in lbl:
                    quality_groups[next(k for k in quality_groups if q in k)].append(link)
                    found = True; break
            if not found: quality_groups["TELEGRAM FILES"].append(link)

    # ডাউনলোড লিঙ্ক সাজানো
    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_html += f'<div class="q-header">{q_name}</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url')
                e = base64.b64encode(u.encode()).decode()
                dl_html += f'<button class="final-btn dl-btn" onclick="goToLink(\'{e}\')">📥 {l.get("label")} - Download</button>'
            dl_html += '</div>'

    if original_files:
        dl_html += f'<div class="q-header" style="color:#00ffd5; border-color:#00ffd5;">⭐ ORIGINAL SOURCE FILES</div><div class="server-grid">'
        for ol in original_files:
            e = base64.b64encode((ol.get('tg_url') or ol.get('url')).encode()).decode()
            dl_html += f'<button class="final-btn" style="border-color:#00ffd5;" onclick="goToLink(\'{e}\')">📁 {ol.get("label")} - Original</button>'
        dl_html += '</div>'

    # --- অ্যাড রেভিনিউ লজিক ---
    weighted_ads = []
    if not user_ad_links_list: weighted_ads = owner_ad_links_list or ["https://google.com"]
    else:
        for _ in range(int(admin_share_percent)): weighted_ads.append(random.choice(owner_ad_links_list))
        for _ in range(100 - int(admin_share_percent)): weighted_ads.append(random.choice(user_ad_links_list))
    random.shuffle(weighted_ads)

    # --- ফাইনাল HTML টেমপ্লেট ---
    return f"""
    <!-- SEO & Metadata -->
    <div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>
    <div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} ({year}) - {overview[:150]}... Download in High Quality.</div>

    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        .rgb-box {{ max-width: 650px; margin: 20px auto; position: relative; padding: 4px; border-radius: 20px; background: #000; overflow: hidden; }}
        .rgb-box::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rotateRGB 4s linear infinite; }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .app-wrapper {{ font-family: 'Poppins', sans-serif !important; background: #0f1014 !important; border-radius: 18px !important; padding: 20px !important; position: relative; z-index: 1; color: #fff; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); }}
        
        .movie-title {{ font-family: 'Oswald', sans-serif !important; font-size: 30px !important; text-align: center; color: #fff; margin-bottom: 20px !important; text-shadow: 0 0 10px {accent}; }}
        
        .info-box {{ display: flex; background: rgba(255,255,255,0.03) !important; border-radius: 15px !important; padding: 20px !important; gap: 20px; align-items: center; border: 1px solid rgba(255,255,255,0.05) !important; }}
        @media (max-width: 480px) {{ .info-box {{ flex-direction: column; text-align: center; }} }}
        .info-poster img {{ width: 160px !important; border-radius: 10px !important; box-shadow: 0 10px 30px {accent}44 !important; border: 1px solid #444; }}
        .info-text {{ flex: 1; font-size: 14px; color: #d1d1d1; line-height: 1.7; }}
        .info-text span {{ color: {accent} !important; font-weight: bold; text-transform: uppercase; font-size: 12px; }}

        .section-title {{ font-size: 18px; color: #fff; margin: 30px 0 10px; border-bottom: 2px solid {accent}; display: inline-block; padding-bottom: 5px; font-weight: bold; }}
        .plot-box {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6; text-align: justify; border-left: 4px solid {accent}; }}

        .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333; }}
        .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}
        
        .ss-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }}
        .ss-img, .blur-img {{ width: 100%; border-radius: 8px; border: 1px solid #333; }}
        .nsfw-box {{ position: relative; cursor: pointer; border-radius: 8px; overflow: hidden; }}
        .blur-img {{ filter: blur(20px); transition: 0.5s; }}
        .nsfw-box.reveal .blur-img {{ filter: blur(0); }}
        .nsfw-tag {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: rgba(0,0,0,0.8); color: #ff5252; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 11px; border: 1px solid #ff5252; }}
        .nsfw-box.reveal .nsfw-tag {{ display: none; }}

        .q-header {{ color: {accent}; font-size: 13px; font-weight: bold; margin: 25px 0 10px; border-left: 3px solid {accent}; padding-left: 10px; text-transform: uppercase; }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }}
        
        .final-btn {{ background: #1a1c22 !important; border: 1px solid #333 !important; border-radius: 10px !important; padding: 12px !important; font-size: 13px !important; color: #fff; cursor: pointer; transition: 0.3s; width: 100%; }}
        .final-btn:hover {{ background: {accent} !important; border-color: {accent} !important; transform: translateY(-3px); box-shadow: 0 5px 15px {accent}66; }}
        .dl-btn {{ border-color: {accent}; }}

        .step-container {{ background: #1a1a24; padding: 25px; border-radius: 15px; text-align: center; border: 1px dashed #555; margin-top: 30px; }}
        .progress {{ height: 8px; background: #333; border-radius: 10px; margin: 15px 0; overflow: hidden; }}
        .fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, {accent}, #fff); transition: width 5s linear; }}
    </style>

    <div class="rgb-box">
        <div class="app-wrapper">
            <div id="ui-1">
                <div class="movie-title">{title} ({year})</div>
                <div class="info-box">
                    <div class="info-poster"><img src="{poster}"></div>
                    <div class="info-text">
                        <div><span>⭐ Rating:</span> {rating}</div>
                        <div><span>🎭 Genre:</span> {genres_str}</div>
                        <div><span>🗣️ Lang:</span> {lang_str}</div>
                        <div><span>⏱️ Runtime:</span> {runtime_str}</div>
                        <div><span>👥 Cast:</span> {cast_names}</div>
                    </div>
                </div>

                <div class="section-title">📖 Storyline</div>
                <div class="plot-box">{overview}</div>

                {trailer_html}
                {ss_html}

                <div class="step-container">
                    <div id="step-label" style="color:#00ffd5; font-weight:bold; font-size:16px;">STEP 1: IDENTITY VERIFICATION</div>
                    <div class="progress"><div id="p-fill" class="fill"></div></div>
                    <button class="final-btn" onclick="startUnlock(this)" style="background:{accent}; border:none; font-size:16px; height:55px;">🔓 UNLOCK DOWNLOAD FILES</button>
                </div>
            </div>

            <div id="ui-2" style="display:none;">
                <div style="text-align:center; color:#00ffd5; font-weight:bold; margin-bottom:20px; border:2px solid #00ffd5; padding:15px; border-radius:12px; background:rgba(0,255,213,0.05);">✅ STEP 2: DOWNLOAD LINKS UNLOCKED!</div>
                {watch_html}
                {dl_html}
            </div>
        </div>
    </div>

    <script>
    const AD_LIST = {json.dumps(weighted_ads)};
    function startUnlock(btn) {{
        window.open(AD_LIST[Math.floor(Math.random() * AD_LIST.length)], '_blank');
        btn.disabled = true; btn.innerHTML = "⌛ Verifying Request...";
        document.getElementById('p-fill').style.width = "100%";
        setTimeout(() => {{
            document.getElementById('ui-1').style.display = 'none';
            document.getElementById('ui-2').style.display = 'block';
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}, 5000);
    }}
    function goToLink(e) {{ window.location.href = atob(e); }}
    </script>
    """

# --- প্লাগইন রেজিস্ট্রেশন ---
async def register(bot):
    main_module = sys.modules['__main__']
    
    # মেইন কোডের ফাংশন ওভাররাইড করা
    main_module.generate_html_code = final_generate_html_code
    
    # ৪০০ এরর (MessageNotModified) হ্যান্ডেল করার জন্য মেকানিজম
    print("🎬 [PLUGIN] FINAL RGB UI SYSTEM ACTIVATED!")
