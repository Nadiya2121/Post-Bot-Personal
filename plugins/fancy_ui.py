# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

# --- নতুন জেনারেটর যা মেইন কোডকে পুরোপুরি রিপ্লেস করবে ---
def new_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # --- মুভির বিস্তারিত তথ্য সংগ্রহ (মেইন কোড থেকে) ---
    title = data.get("title") or data.get("name") or "N/A"
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    is_adult = data.get('adult', False) or data.get('force_adult', False)
    theme = data.get("theme", "netflix")

    # মেটা ডাটা প্রসেসিং
    if data.get('is_manual'):
        genres_str = "Custom / Unknown" 
        year = "N/A"
        rating = "N/A"
        runtime_str = "N/A"
        cast_names = "N/A"
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

    # --- থিম অনুযায়ী কালার সেটআপ ---
    if theme == "netflix":
        accent = "#E50914"; glow = "rgba(229, 9, 20, 0.5)"
    elif theme == "prime":
        accent = "#00A8E1"; glow = "rgba(0, 168, 225, 0.5)"
    else:
        accent = "#6200ea"; glow = "rgba(98, 0, 234, 0.5)"

    # --- ট্রেইলার সেকশন ---
    trailer_html = ""
    videos = data.get('videos', {}).get('results',[])
    trailer_key = next((v['key'] for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube'), None)
    if trailer_key:
        trailer_html = f'''<div class="section-title">🎬 OFFICIAL TRAILER</div>
        <div class="video-container"><iframe src="https://www.youtube.com/embed/{trailer_key}" allowfullscreen></iframe></div>'''

    # --- স্ক্রিনশট সেকশন (NSFW সাপোর্ট সহ) ---
    screenshots = data.get('manual_screenshots',[])
    if not screenshots and not data.get('is_manual'):
        backdrops = data.get('images', {}).get('backdrops',[])
        screenshots = [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in backdrops[:6]] 
    
    ss_html = ""
    if screenshots:
        ss_imgs = ""
        for img in screenshots:
            if is_adult:
                ss_imgs += f'''<div class="nsfw-container" onclick="this.classList.toggle('reveal')">
                    <img src="{img}" class="blur-img"><div class="nsfw-warning">🔞 CLICK TO VIEW</div></div>'''
            else:
                ss_imgs += f'<img src="{img}" class="normal-ss">'
        ss_html = f'<div class="section-title">📸 MOVIE SCREENSHOTS</div><div class="ss-grid">{ss_imgs}</div>'

    # --- লিঙ্ক গ্রুপিং লজিক (Watch, Download, Original) ---
    watch_html, dl_html, original_html = "", "", ""
    quality_groups = {"4K ULTRA HD": [], "1080P FULL HD": [], "720P HD": [], "480P / SD": [], "TELEGRAM FILES": []}

    for link in links:
        lbl = link.get('label', '').upper()
        url = link.get('tg_url') or link.get('url', '')
        enc = base64.b64encode(url.encode()).decode()
        
        btn_code = f'<button class="rgb-btn" onclick="goToLink(\'{enc}\')">'
        
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_html += f'{btn_code}▶️ {link.get("label")} - Watch Online</button>'
        elif "ORIGINAL" in lbl:
            original_html += f'{btn_code}⭐ {link.get("label")} - Original File</button>'
        else:
            # কোয়ালিটি অনুযায়ী সর্টিং
            q_found = False
            for q in ["4K", "1080", "720", "480"]:
                if q in lbl:
                    quality_groups[next(k for k in quality_groups if q in k)].append(link)
                    q_found = True; break
            if not q_found: quality_groups["TELEGRAM FILES"].append(link)

    # ডাউনলোড বাটন জেনারেট
    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_html += f'<div class="q-header">{q_name}</div>'
            for l in q_links:
                u = l.get('tg_url') or l.get('url')
                e = base64.b64encode(u.encode()).decode()
                dl_html += f'<button class="rgb-btn dl-btn" onclick="goToLink(\'{e}\')">📥 {l.get("label")} - Download Now</button>'

    # --- অ্যাড রেভিনিউ শেয়ার লজিক (মেইন কোড থেকে) ---
    weighted_ads = []
    if not user_ad_links_list:
        weighted_ads = owner_ad_links_list if owner_ad_links_list else ["https://google.com"]
    elif not owner_ad_links_list:
        weighted_ads = user_ad_links_list
    else:
        for _ in range(int(admin_share_percent)): weighted_ads.append(random.choice(owner_ad_links_list))
        for _ in range(100 - int(admin_share_percent)): weighted_ads.append(random.choice(user_ad_links_list))
    random.shuffle(weighted_ads)

    # --- ফুল CSS এবং HTML টেমপ্লেট ---
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500;700&display=swap');
        
        :root {{ --accent: {accent}; --glow: {glow}; }}
        body {{ background: #000; margin: 0; padding: 0; font-family: 'Rajdhani', sans-serif; }}

        .app-wrapper {{
            max-width: 600px; margin: 20px auto; position: relative; padding: 4px;
            border-radius: 20px; background: #000; overflow: hidden; z-index: 1;
        }}
        /* RGB Border Animation */
        .app-wrapper::before {{
            content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
            background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            animation: rotateRGB 4s linear infinite; z-index: -1;
        }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .inner-content {{ background: #0d0d12; border-radius: 18px; padding: 20px; color: #fff; }}

        /* Info Section */
        .movie-card {{ display: flex; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 20px; }}
        .movie-card img {{ width: 150px; border-radius: 12px; border: 2px solid #333; box-shadow: 0 0 15px var(--glow); }}
        .meta-data {{ flex: 1; font-size: 15px; line-height: 1.6; }}
        .meta-data b {{ color: #00ffd5; }}

        .section-title {{
            background: linear-gradient(90deg, var(--accent), #7a00ff);
            color: #fff; padding: 10px; text-align: center; border-radius: 8px;
            font-family: 'Orbitron'; font-size: 14px; margin: 30px 0 15px;
            box-shadow: 0 0 15px var(--glow); letter-spacing: 1px;
        }}

        .plot-text {{ background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border-left: 4px solid var(--accent); color: #ccc; font-size: 14px; text-align: justify; }}

        /* Media Elements */
        .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; border: 1px solid #333; }}
        .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}
        
        .ss-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; }}
        .normal-ss {{ width: 100%; border-radius: 10px; border: 1px solid #333; transition: 0.3s; }}
        .normal-ss:hover {{ transform: scale(1.05); z-index: 2; border-color: #00ffd5; }}

        .nsfw-container {{ position: relative; cursor: pointer; border-radius: 10px; overflow: hidden; }}
        .blur-img {{ width: 100%; filter: blur(25px); transition: 0.5s; display: block; }}
        .nsfw-warning {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: rgba(0,0,0,0.8); color: #ff5252; padding: 5px 10px; border: 1px solid #ff5252; border-radius: 5px; font-weight: bold; font-size: 12px; }}
        .nsfw-container.reveal .blur-img {{ filter: blur(0); }}
        .nsfw-container.reveal .nsfw-warning {{ display: none; }}

        /* Buttons & Steps */
        .q-header {{ color: #00ffd5; font-size: 13px; font-weight: bold; margin: 15px 0 8px; border-left: 3px solid var(--accent); padding-left: 10px; text-transform: uppercase; }}
        
        .rgb-btn {{
            width: 100%; padding: 16px; margin-bottom: 12px; border: 1px solid #333;
            border-radius: 12px; background: #16161d; color: #fff; font-weight: bold;
            cursor: pointer; transition: 0.3s; display: block; font-size: 15px; font-family: 'Rajdhani';
        }}
        .rgb-btn:hover {{ transform: scale(1.02); border-color: #00ffd5; box-shadow: 0 0 15px #00ffd5; color: #00ffd5; }}
        .dl-btn {{ border-color: var(--accent); }}

        .unlock-card {{ background: #1a1a24; padding: 25px; border-radius: 15px; text-align: center; border: 1px dashed #555; }}
        .progress-bg {{ height: 10px; background: #333; border-radius: 20px; margin: 20px 0; overflow: hidden; }}
        .progress-fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, #00ffd5, var(--accent)); transition: width 1s linear; }}
    </style>

    <div class="app-wrapper">
        <div class="inner-content">
            <div id="step-1">
                <div class="movie-card">
                    <img src="{poster}">
                    <div class="meta-data">
                        <h2 style="margin:0 0 10px; font-family:'Orbitron'; font-size:20px; color:#fff;">{title} ({year})</h2>
                        <div><b>⭐ IMDB:</b> {rating}</div>
                        <div><b>🎭 Genre:</b> {genres_str}</div>
                        <div><b>🗣️ Lang:</b> {lang_str}</div>
                        <div><b>⏱️ Duration:</b> {runtime_str}</div>
                        <div><b>👥 Cast:</b> {cast_names}</div>
                    </div>
                </div>

                <div class="section-title">📖 STORYLINE / PLOT</div>
                <div class="plot-text">{overview}</div>

                {trailer_html}
                {ss_html}

                <div class="section-title">📥 DOWNLOAD LINKS</div>
                <div class="unlock-card">
                    <div id="step-info" style="color:#00ffd5; font-weight:bold; font-size:16px;">STEP 1: VERIFYING REQUEST...</div>
                    <div class="progress-bg"><div id="p-bar" class="progress-fill"></div></div>
                    <button class="rgb-btn" onclick="startUnlock(this)" style="background:var(--accent); border:none; color:white; font-size:17px; box-shadow: 0 5px 15px var(--glow);">🔓 UNLOCK FILES NOW</button>
                </div>
            </div>

            <div id="step-2" style="display:none;">
                <div style="text-align:center; color:#00ffd5; font-weight:bold; margin-bottom:20px; border:2px solid #00ffd5; padding:15px; border-radius:12px; background:rgba(0,255,213,0.05);">
                    ✅ STEP 2: DOWNLOAD LINKS UNLOCKED!
                </div>
                {watch_html}
                {dl_html}
                {original_html}
            </div>
        </div>
    </div>

    <script>
        const AD_LINKS = {json.dumps(weighted_ads)};
        function startUnlock(btn) {{
            window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
            btn.disabled = true; btn.innerHTML = "⌛ Verifying... Please Wait";
            let p = 0;
            let iv = setInterval(() => {{
                p += 20; document.getElementById('p-bar').style.width = p + "%";
                if(p >= 100) {{
                    clearInterval(iv);
                    document.getElementById('step-1').style.display = 'none';
                    document.getElementById('step-2').style.display = 'block';
                    window.scrollTo(0,0);
                }}
            }}, 1000);
        }}
        function goToLink(e) {{ window.location.href = atob(e); }}
    </script>
    """

async def register(bot):
    main_module = sys.modules['__main__']
    main_module.generate_html_code = new_generate_html_code
    print("🚀 [PLUGIN] FULL POWER RGB UI SYSTEM LOADED!")
