# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

def final_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # --- মুভির তথ্য ---
    title = data.get("title") or data.get("name") or "Movie"
    overview = data.get("overview", "No plot available.")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    is_adult = data.get('adult', False) or data.get('force_adult', False)
    theme = data.get("theme", "netflix")

    # ল্যাঙ্গুয়েজ লজিক (আপনার থিম এটার ওপর নির্ভর করে)
    lang_str = data.get('custom_language', 'Dual Audio').strip()
    
    if data.get('is_manual'):
        genres_str = "Custom"; year = "N/A"; rating = "N/A"; runtime_str = "N/A"; cast_names = "N/A"
    else:
        genres_list = [g['name'] for g in data.get('genres',[])]
        genres_str = ", ".join(genres_list) if genres_list else "Movie"
        year = str(data.get("release_date") or data.get("first_air_date") or "----")[:4]
        rating = f"{data.get('vote_average', 0):.1f}/10"
        runtime = data.get('runtime') or (data.get('episode_run_time',[0])[0] if data.get('episode_run_time') else "N/A")
        runtime_str = f"{runtime} min" if runtime != "N/A" else "N/A"
        cast_list = data.get('credits', {}).get('cast',[])
        cast_names = ", ".join([c['name'] for c in cast_list[:4]]) if cast_list else "Unknown"

    # --- ক্যাটাগরি অনুযায়ী লিঙ্ক গ্রুপিং ---
    watch_html, dl_html = "", ""
    quality_groups = {"4K Ultra HD": [], "1080p Full HD": [], "720p HD": [], "480p SD": [], "Telegram Files": []}
    original_files = []

    for link in links:
        lbl = link.get('label', '').upper()
        url = link.get('tg_url') or link.get('url', '')
        enc = base64.b64encode(url.encode()).decode()
        
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_html += f'<button class="final-server-btn" style="background:#E50914;" onclick="goToLink(\'{enc}\')">▶️ {link.get("label")} - Stream</button>'
        elif "ORIGINAL" in lbl:
            original_files.append(link)
        else:
            q_found = False
            for q in ["4K", "1080", "720", "480"]:
                if q in lbl:
                    quality_groups[next(k for k in quality_groups if q in k)].append(link)
                    q_found = True; break
            if not q_found: quality_groups["Telegram Files"].append(link)

    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_html += f'<div class="quality-title">📺 {q_name}</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url')
                e = base64.b64encode(u.encode()).decode()
                dl_html += f'<button class="final-server-btn" onclick="goToLink(\'{e}\')">📥 {l.get("label")} - Download</button>'
            dl_html += '</div>'

    if original_files:
        dl_html += f'<div class="quality-title" style="background:linear-gradient(90deg, #00C9FF, transparent);">⭐ Original Source Files</div><div class="server-grid">'
        for ol in original_files:
            e = base64.b64encode((ol.get('tg_url') or ol.get('url')).encode()).decode()
            dl_html += f'<button class="final-server-btn" style="border-color:#00C9FF;" onclick="goToLink(\'{e}\')">📁 {ol.get("label")} - Original</button>'
        dl_html += '</div>'

    # ট্রেইলার ও স্ক্রিনশট
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
            else: ss_grid += f'<img src="{img}" style="width:100%; border-radius:8px; border:1px solid #333;">'
        ss_html = f'<div class="section-title">📸 Screenshots</div><div class="screenshot-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px;">{ss_grid}</div>'

    # Ad revenue share
    weighted_ads = user_ad_links_list if user_ad_links_list else (owner_ad_links_list or ["https://google.com"])
    random.shuffle(weighted_ads)

    # --- টেমপ্লেট জেনারেশন ---
    return f"""
    <!-- SEO & Metadata -->
    <div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>
    <div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} ({year}) - {overview[:150]}... Download in {lang_str}.</div>

    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        .rgb-wrapper {{ max-width: 650px; margin: 20px auto; position: relative; padding: 4px; border-radius: 20px; background: #000; overflow: hidden; }}
        .rgb-wrapper::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rotateRGB 4s linear infinite; }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .app-wrapper {{ font-family: 'Poppins', sans-serif !important; background: #0f1014 !important; padding: 20px !important; border-radius: 18px !important; position: relative; z-index: 1; color: #fff; }}
        
        /* Badges - আপনার থিমের জন্য গুরুত্বপূর্ণ */
        .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; }}
        .badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); padding: 3px 12px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}

        .movie-title {{ font-family: 'Oswald', sans-serif !important; font-size: 28px !important; text-align: center; margin-bottom: 20px !important; color: #fff; }}
        
        .info-box {{ display: flex; background: rgba(255,255,255,0.03); border-radius: 15px; padding: 20px; gap: 20px; align-items: center; border: 1px solid rgba(255,255,255,0.05); }}
        @media (max-width: 480px) {{ .info-box {{ flex-direction: column; text-align: center; }} }}
        .info-poster img {{ width: 150px !important; border-radius: 10px !important; box-shadow: 0 10px 30px rgba(229,9,20,0.4); }}
        .info-text {{ flex: 1; font-size: 14px; color: #d1d1d1; line-height: 1.7; }}
        .info-text span {{ color: #E50914 !important; font-weight: bold; font-size: 12px; }}

        .section-title {{ font-size: 18px; color: #fff; margin: 25px 0 10px; border-bottom: 2px solid #E50914; display: inline-block; padding-bottom: 5px; font-weight: bold; }}
        .plot-box {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6; text-align: justify; border-left: 4px solid #E50914; }}

        .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 12px; margin-bottom: 20px; }}
        .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}

        .quality-title {{ background: linear-gradient(90deg, #E50914, transparent) !important; padding: 10px 15px !important; font-size: 14px !important; color: #fff !important; margin-top: 20px; border-radius: 4px; }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px; }}
        .final-server-btn {{ background: #1a1c22; border: 1px solid #333; border-radius: 10px; padding: 12px; font-size: 13px; color: #fff; cursor: pointer; transition: 0.3s; width: 100%; }}
        .final-server-btn:hover {{ background: #E50914; border-color: #E50914; transform: translateY(-3px); }}

        .step-container {{ background: #1a1a24; padding: 25px; border-radius: 15px; text-align: center; border: 1px dashed #444; margin-top: 30px; }}
        .progress-bar {{ height: 6px; background: #333; border-radius: 10px; margin: 15px 0; overflow: hidden; }}
        .fill {{ height: 100%; width: 0%; background: linear-gradient(90deg, #E50914, #ff5252); transition: width 5s linear; }}
        
        .nsfw-blur {{ filter: blur(25px); cursor: pointer; }}
        .nsfw-container {{ position: relative; border-radius: 8px; overflow: hidden; }}
        .nsfw-warning {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); background: rgba(0,0,0,0.8); color: #ff5252; padding: 5px 10px; border-radius: 5px; font-weight: bold; }}
    </style>

    <div class="rgb-wrapper">
        <div class="app-wrapper">
            <div id="ui-1">
                <!-- আপনার থিমের Badges সেকশন -->
                <div class="media-badges">
                    <div class="badge">{lang_str}</div>
                    <div class="badge">Dual Audio</div>
                    <div class="badge">HEVC</div>
                </div>

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
                    <div style="color:#ff5252; font-weight:bold; font-size:16px; margin-bottom:10px;">STEP 1: IDENTITY VERIFICATION</div>
                    <div class="progress-bar"><div id="p-fill" class="fill"></div></div>
                    <button class="final-server-btn" onclick="startUnlock(this)" style="background:#E50914; border:none; font-size:16px; font-weight:bold; height:50px;">🔓 UNLOCK DOWNLOAD SERVERS</button>
                </div>
            </div>

            <div id="ui-2" style="display:none;">
                <div style="text-align:center; color:#00e676; font-weight:bold; margin-bottom:20px; border:1px solid #00e676; padding:12px; border-radius:10px; background:rgba(0,230,118,0.05);">✅ STEP 2: DOWNLOAD LINKS UNLOCKED!</div>
                {watch_html}
                {dl_html}
            </div>
        </div>
    </div>

    <script>
    const AD_LINKS = {json.dumps(weighted_ads)};
    function startUnlock(btn) {{
        window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
        btn.disabled = true; btn.innerHTML = "⌛ Verifying...";
        document.getElementById('p-fill').style.width = "100%";
        setTimeout(() => {{
            document.getElementById('ui-1').style.display = 'none';
            document.getElementById('ui-2').style.display = 'block';
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}, 5000);
    }}
    function goToLink(e) {{ window.location.href = atob(e); }}
    function revealNSFW(c) {{ c.querySelector('img').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}
    </script>
    """

async def register(bot):
    main_module = sys.modules['__main__']
    main_module.generate_html_code = final_generate_html_code
    print("🚀 [PLUGIN] Original Theme Integrated with Fixed Language Badges!")
