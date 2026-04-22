# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

def new_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # --- মুভির তথ্য (মেইন কোড থেকে) ---
    title = data.get("title") or data.get("name") or "Movie"
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    is_adult = data.get('adult', False) or data.get('force_adult', False)
    
    genres_str = ", ".join([g['name'] for g in data.get('genres', [])]) if data.get('genres') else "N/A"
    year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
    rating = f"{data.get('vote_average', 0):.1f}/10"
    runtime = f"{data.get('runtime', 'N/A')} min"
    lang_str = data.get('custom_language', 'Dual Audio').strip()
    cast_names = ", ".join([c['name'] for c in data.get('credits', {}).get('cast', [])[:4]]) if data.get('credits') else "Unknown"

    # --- লিঙ্ক গ্রুপিং লজিক (আপনার থিমের সাথে সামঞ্জস্য রেখে) ---
    watch_btns_html = ""
    download_sections_html = ""
    quality_groups = {"4K Ultra HD": [], "1080p Full HD": [], "720p HD": [], "480p SD": [], "Telegram Files": []}
    original_files = []

    for link in links:
        lbl = link.get('label', '').upper()
        url = link.get('tg_url') or link.get('url', '')
        enc = base64.b64encode(url.encode()).decode()
        
        # বাটন টাইপ নির্ধারণ
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_btns_html += f'<button class="final-server-btn" style="background:#E50914;" onclick="goToLink(\'{enc}\')">▶️ {link.get("label")} - Stream</button>'
        elif "ORIGINAL" in lbl:
            original_files.append(link)
        else:
            q_found = False
            for q in ["4K", "1080", "720", "480"]:
                if q in lbl:
                    quality_groups[next(k for k in quality_groups if q in k)].append(link)
                    q_found = True; break
            if not q_found: quality_groups["Telegram Files"].append(link)

    # ডাউনলোড সেকশন জেনারেট
    for q_name, q_links in quality_groups.items():
        if q_links:
            download_sections_html += f'<div class="quality-title">📺 {q_name}</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url')
                e = base64.b64encode(u.encode()).decode()
                download_sections_html += f'<button class="final-server-btn" onclick="goToLink(\'{e}\')">📥 {l.get("label")} - Download</button>'
            download_sections_html += '</div>'

    if original_files:
        download_sections_html += f'<div class="quality-title" style="background:linear-gradient(90deg, #00C9FF, transparent);">⭐ Original Source Files</div><div class="server-grid">'
        for ol in original_files:
            e = base64.b64encode((ol.get('tg_url') or ol.get('url')).encode()).decode()
            download_sections_html += f'<button class="final-server-btn" style="border-color:#00C9FF;" onclick="goToLink(\'{e}\')">📁 {ol.get("label")} - Original</button>'
        download_sections_html += '</div>'

    # --- ট্রেইলার ও স্ক্রিনশট ---
    trailer_html = ""
    videos = data.get('videos', {}).get('results',[])
    tk = next((v['key'] for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube'), None)
    if tk: trailer_html = f'<div class="section-title">🎬 Official Trailer</div><div class="video-container"><iframe src="https://www.youtube.com/embed/{tk}" allowfullscreen></iframe></div>'

    screenshots = data.get('manual_screenshots', [])
    if not screenshots and not data.get('is_manual'):
        screenshots = [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in data.get('images', {}).get('backdrops', [])[:6]]
    
    ss_html = ""
    if screenshots:
        ss_grid = ""
        for img in screenshots:
            if is_adult: ss_grid += f'<div class="nsfw-container" onclick="revealNSFW(this)"><img src="{img}" class="nsfw-blur"><div class="nsfw-warning">🔞 18+</div></div>'
            else: ss_grid += f'<img src="{img}" alt="Screenshot">'
        ss_html = f'<div class="section-title">📸 Screenshots</div><div class="screenshot-grid">{ss_grid}</div>'

    # Ad revenue share
    weighted_ads = []
    if not user_ad_links_list: weighted_ads = owner_ad_links_list if owner_ad_links_list else ["https://google.com"]
    else:
        for _ in range(int(admin_share_percent)): weighted_ads.append(random.choice(owner_ad_links_list))
        for _ in range(100 - int(admin_share_percent)): weighted_ads.append(random.choice(user_ad_links_list))
    random.shuffle(weighted_ads)

    # --- ফাইনাল টেমপ্লেট (আপনার টেমপ্লেটের হুবহু ক্লাস বজায় রেখে) ---
    return f"""
    <!-- SEO & Metadata -->
    <div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>
    <div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} - {overview[:150]}... Download now.</div>

    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        /* RGB Border Container */
        .rgb-container {{
            max-width: 650px; margin: 20px auto; position: relative; padding: 4px; border-radius: 20px; background: #000; overflow: hidden;
        }}
        .rgb-container::before {{
            content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
            background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            animation: rotateRGB 4s linear infinite;
        }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .app-wrapper {{
            font-family: 'Poppins', sans-serif !important; background: #0f1014 !important; border: none !important; border-radius: 18px !important; padding: 20px !important; position: relative; z-index: 1; color: #fff;
        }}
        .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; }}
        .badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
        
        .movie-title {{ font-family: 'Oswald', sans-serif !important; font-size: 30px !important; text-align: center; color: #fff; margin-bottom: 20px !important; }}
        
        .info-box {{ display: flex; background: rgba(255,255,255,0.03) !important; border-radius: 15px !important; padding: 20px !important; gap: 20px; align-items: center; border: 1px solid rgba(255,255,255,0.05) !important; }}
        .info-poster img {{ width: 150px !important; border-radius: 10px !important; box-shadow: 0 10px 30px rgba(229, 9, 20, 0.4) !important; }}
        .info-text {{ flex: 1; font-size: 14px; color: #d1d1d1; }}
        .info-text span {{ color: #E50914 !important; font-weight: bold; font-size: 12px; }}

        .section-title {{ font-size: 18px; color: #fff; margin: 25px 0 10px; border-bottom: 2px solid #E50914; display: inline-block; padding-bottom: 5px; font-weight: bold; }}
        .plot-box {{ background: rgba(0,0,0,0.2); padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6; text-align: justify; border-left: 4px solid #E50914; }}

        .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 10px; margin-bottom: 20px; }}
        .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}
        
        .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }}
        .screenshot-grid img {{ width: 100%; border-radius: 8px; border: 1px solid #333; }}

        .quality-title {{ background: linear-gradient(90deg, #E50914, transparent) !important; border-radius: 5px !important; padding: 10px 15px !important; font-size: 14px !important; color: #fff !important; margin-top: 20px; }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px; }}
        
        .final-server-btn {{ background: #1a1c22 !important; border: 1px solid #333 !important; border-radius: 10px !important; padding: 12px !important; font-size: 13px !important; color: #fff; cursor: pointer; transition: 0.3s; }}
        .final-server-btn:hover {{ background: #E50914 !important; border-color: #E50914 !important; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(229, 9, 20, 0.4); }}

        /* Unlock Step UI */
        .step-container {{ background: #1a1a24; padding: 25px; border-radius: 15px; text-align: center; border: 1px dashed #444; margin-top: 20px; }}
        .progress-bar {{ height: 6px; background: #333; border-radius: 10px; margin: 15px 0; overflow: hidden; position: relative; }}
        .progress-fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, #E50914, #ff5252); transition: width 5s linear; }}

        .action-btns {{ display: flex; flex-direction: column; gap: 15px; margin-top: 20px; }}
        .main-btn {{ width: 100%; padding: 16px; font-size: 16px; font-weight: bold; color: #fff; border: none; border-radius: 10px; cursor: pointer; transition: 0.3s; }}
        .btn-red {{ background: linear-gradient(90deg, #E50914, #ff5252); box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4); }}
        .btn-green {{ background: linear-gradient(90deg, #00C9FF, #92FE9D); color: #000; }}

        .nsfw-blur {{ filter: blur(25px); cursor: pointer; }}
    </style>

    <div class="rgb-container">
        <div class="app-wrapper">
            <div id="step-1-ui">
                <div class="media-badges"><div class="badge">Dual Audio</div><div class="badge">HEVC</div><div class="badge">{lang_str}</div></div>
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
                    <div id="step-txt" style="color:#ff5252; font-weight:bold; font-size:16px;">STEP 1: UNLOCK DOWNLOAD SERVERS</div>
                    <div class="progress-bar"><div id="fill" class="progress-fill"></div></div>
                    <div class="action-btns">
                        <button class="main-btn btn-red" onclick="startUnlock(this)">🔓 CLICK TO UNLOCK LINKS</button>
                    </div>
                </div>
            </div>

            <div id="step-2-ui" style="display:none;">
                <div style="text-align:center; background:rgba(0,255,100,0.1); padding:10px; border-radius:8px; color:#00e676; font-weight:bold; margin-bottom:20px; border:1px solid #00e676;">✅ STEP 2: LINKS UNLOCKED SUCCESSFULLY</div>
                {watch_btns_html}
                {download_sections_html}
            </div>
        </div>
    </div>

    <script>
    const AD_LINKS = {json.dumps(weighted_ads)};
    function startUnlock(btn) {{
        window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
        btn.disabled = true;
        btn.innerHTML = "⌛ Verifying Request...";
        document.getElementById('fill').style.width = "100%";
        
        let timeLeft = 5;
        let timer = setInterval(function() {{
            timeLeft--;
            if (timeLeft < 0) {{
                clearInterval(timer);
                document.getElementById('step-1-ui').style.display = 'none';
                document.getElementById('step-2-ui').style.display = 'block';
                window.scrollTo({{top: 0, behavior: 'smooth'}});
            }}
        }}, 1000);
    }}
    function goToLink(enc) {{ window.location.href = atob(enc); }}
    function revealNSFW(c) {{ c.querySelector('img').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}
    </script>
    """

async def register(bot):
    main_module = sys.modules['__main__']
    main_module.generate_html_code = new_generate_html_code
    print("🚀 [PLUGIN] Original Theme Integrated with RGB & Smart Grouping!")
