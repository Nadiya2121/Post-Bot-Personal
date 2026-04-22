# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

def fancy_ui_final(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    # --- মুভির ডাটা সংগ্রহ ---
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
    cast = ", ".join([c['name'] for c in data.get('credits', {}).get('cast', [])[:4]]) if data.get('credits') else "Unknown"

    # --- লিঙ্ক গ্রুপিং (Watch, Download, Original) ---
    watch_btns, dl_sections = "", ""
    quality_groups = {"4K Ultra HD": [], "1080p Full HD": [], "720p HD": [], "480p SD": [], "Telegram Files": []}
    original_links = []

    for link in links:
        lbl = link.get('label', '').upper()
        url = link.get('tg_url') or link.get('url', '')
        enc = base64.b64encode(url.encode()).decode()
        
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_btns += f'<button class="final-server-btn stream-btn" onclick="goToLink(\'{enc}\')">▶️ {link.get("label")} - Stream Online</button>'
        elif "ORIGINAL" in lbl:
            original_links.append(link)
        else:
            found_q = False
            for q in ["4K", "1080", "720", "480"]:
                if q in lbl:
                    quality_groups[next(k for k in quality_groups if q in k)].append(link)
                    found_q = True; break
            if not found_q: quality_groups["Telegram Files"].append(link)

    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_sections += f'<div class="quality-title">📺 {q_name}</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
                dl_sections += f'<button class="final-server-btn" onclick="goToLink(\'{e}\')">📥 {l.get("label")} - Download</button>'
            dl_sections += '</div>'

    if original_links:
        dl_sections += f'<div class="quality-title" style="background:linear-gradient(90deg, #00d2ff, transparent);">⭐ ORIGINAL SOURCE FILES</div><div class="server-grid">'
        for ol in original_links:
            e = base64.b64encode((ol.get('tg_url') or ol.get('url')).encode()).decode()
            dl_sections += f'<button class="final-server-btn" style="border-color:#00d2ff;" onclick="goToLink(\'{e}\')">📁 {ol.get("label")} - Original</button>'
        dl_sections += '</div>'

    # ট্রেইলার ও স্ক্রিনশট
    trailer_html = ""
    tk = next((v['key'] for v in data.get('videos', {}).get('results', []) if v.get('type') == 'Trailer'), None)
    if tk: trailer_html = f'<div class="section-title">🎬 Official Trailer</div><div class="video-container"><iframe src="https://www.youtube.com/embed/{tk}" allowfullscreen></iframe></div>'

    ss_html = ""
    screenshots = data.get('manual_screenshots') or [f"https://image.tmdb.org/t/p/w780{b['file_path']}" for b in data.get('images', {}).get('backdrops', [])[:6]]
    if screenshots:
        imgs = ""
        for img in screenshots:
            if is_adult: imgs += f'<div class="nsfw-container" onclick="revealNSFW(this)"><img src="{img}" class="nsfw-blur"><div class="nsfw-warning">🔞 18+</div></div>'
            else: imgs += f'<img src="{img}" alt="Screenshot">'
        ss_html = f'<div class="section-title">📸 Screenshots</div><div class="screenshot-grid">{imgs}</div>'

    # Ad Revenue
    weighted_ads = user_ad_links_list if user_ad_links_list else (owner_ad_links_list or ["https://google.com"])
    random.shuffle(weighted_ads)

    # --- HTML টেমপ্লেট (আপনার অরিজিনাল কোডের স্ট্রাকচার বজায় রেখে) ---
    return f"""
    <div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>
    <div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} - {overview[:150]}... Download in {lang_str}.</div>

    <script>
    async function detectAdBlock() {{
      let adBlockEnabled = false; const googleAdUrl = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
      try {{ await fetch(new Request(googleAdUrl)).catch(_ => adBlockEnabled = true); }} catch (e) {{ adBlockEnabled = true; }}
      if (adBlockEnabled) {{
        document.body.innerHTML = `<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:#0f0f13;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:sans-serif;text-align:center;padding:20px;"><h1>🚫</h1><h2>Ad-Blocker Detected!</h2><p>Please disable Ad-Blocker and refresh.</p><button onclick="window.location.reload()" style="background:#E50914;color:#fff;border:none;padding:12px 25px;border-radius:5px;cursor:pointer;">Refresh Page</button></div>`;
      }}
    }}
    window.onload = function() {{ detectAdBlock(); }};
    </script>

    <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        body {{ background: #05060a !important; background-image: linear-gradient(to bottom, rgba(5,6,10,0.8), #05060a), url('{backdrop}') !important; background-attachment: fixed !important; background-size: cover !important; background-position: center !important; margin: 0; padding: 0; }}
        
        .rgb-wrapper {{ max-width: 650px; margin: 20px auto; position: relative; padding: 4px; border-radius: 20px; background: #000; overflow: hidden; }}
        .rgb-wrapper::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rotateRGB 4s linear infinite; }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .app-wrapper {{ font-family: 'Poppins', sans-serif !important; background: #0f1014 !important; border-radius: 18px !important; padding: 20px !important; position: relative; z-index: 1; color: #fff; }}
        
        /* 🏷️ আপনার থিমের Badges যা পোস্টারের ওপর দেখাবে */
        .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }}
        .badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; font-size: 11px; padding: 3px 12px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}

        .movie-title {{ font-family: 'Oswald', sans-serif !important; font-size: 32px !important; text-align: center; margin-bottom: 30px !important; color: #fff; }}
        
        .info-box {{ display: flex; background: rgba(255,255,255,0.03) !important; border-radius: 15px !important; padding: 25px !important; gap: 20px; align-items: center; border: 1px solid rgba(255,255,255,0.05) !important; }}
        @media (max-width: 480px) {{ .info-box {{ flex-direction: column; text-align: center; }} }}
        .info-poster img {{ width: 160px !important; border-radius: 12px !important; box-shadow: 0 10px 30px rgba(229, 9, 20, 0.4) !important; }}
        .info-text {{ flex: 1; font-size: 14px; color: #d1d1d1; }}
        .info-text span {{ color: #E50914 !important; font-weight: bold; font-size: 12px; }}

        .section-title {{ font-size: 18px; color: #fff; margin: 25px 0 10px; border-bottom: 2px solid #E50914; display: inline-block; padding-bottom: 5px; font-weight: bold; }}
        .plot-box {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; font-size: 14px; line-height: 1.6; text-align: justify; border-left: 4px solid #E50914; }}

        .quality-title {{ background: linear-gradient(90deg, #E50914, transparent) !important; padding: 10px 15px !important; font-size: 14px !important; color: #fff !important; margin-top: 20px; border-radius: 4px; }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px; }}
        .final-server-btn {{ background: #1a1c22 !important; border: 1px solid #333 !important; border-radius: 10px !important; padding: 12px !important; font-size: 13px !important; color: #fff; cursor: pointer; transition: 0.3s; width: 100%; }}
        .final-server-btn:hover {{ background: #E50914 !important; border-color: #E50914 !important; transform: translateY(-3px); }}

        #unlock-timer {{ width: 0%; height: 4px; background: #E50914; position: absolute; bottom: 0; left: 0; transition: width 5s linear; box-shadow: 0 0 10px #E50914; }}
        .nsfw-blur {{ filter: blur(25px); cursor: pointer; }}
    </style>

    <div class="rgb-wrapper">
        <div class="app-wrapper">
            <div id="view-details">
                <div class="media-badges">
                    <div class="badge">{lang_str}</div>
                    <div class="badge">⭐ {rating}</div>
                    <div class="badge">{year}</div>
                    <div class="badge">HEVC</div>
                </div>
                <div class="movie-title">{title} ({year})</div>
                <div class="info-box">
                    <div class="info-poster"><img src="{poster}"></div>
                    <div class="info-text">
                        <div><span>⭐ Rating:</span> {rating}</div>
                        <div><span>🎭 Genre:</span> {genres}</div>
                        <div><span>🗣️ Lang:</span> {lang_str}</div>
                        <div><span>⏱️ Time:</span> {runtime}</div>
                        <div><span>👥 Cast:</span> {cast}</div>
                    </div>
                </div>
                <div class="section-title">📖 Storyline</div>
                <div class="plot-box">{overview}</div>
                {trailer_html}
                {ss_html}
                <div style="background:#1a1a24; padding:20px; border-radius:15px; text-align:center; margin-top:25px; border:1px dashed #444;">
                    <div id="st-txt" style="color:#ff5252; font-weight:bold; font-size:16px;">STEP 1: UNLOCK DOWNLOAD SERVERS</div>
                    <div style="height:6px; background:#333; border-radius:10px; margin:15px 0; overflow:hidden; position:relative;"><div id="p-bar" style="height:100%; width:0%; background:#E50914; transition:width 5s linear;"></div></div>
                    <button class="final-server-btn" onclick="startUnlock(this)" style="background:#E50914; border:none; height:50px; font-weight:bold;">🔓 UNLOCK FILES NOW</button>
                </div>
            </div>
            <div id="view-links" style="display:none;">
                <div style="text-align:center; color:#00e676; font-weight:bold; margin-bottom:20px; border:1px solid #00e676; padding:12px; border-radius:10px; background:rgba(0,230,118,0.05);">✅ STEP 2: DOWNLOAD LINKS UNLOCKED!</div>
                {watch_btns}
                {dl_sections}
            </div>
        </div>
    </div>

    <script>
    const AD_LINKS = {json.dumps(weighted_ads)};
    function startUnlock(btn) {{
        window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
        btn.disabled = true; btn.innerHTML = "⌛ Verifying Request...";
        document.getElementById('p-bar').style.width = "100%";
        setTimeout(() => {{
            document.getElementById('view-details').style.display = 'none';
            document.getElementById('view-links').style.display = 'block';
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}, 5000);
    }}
    function goToLink(e) {{ window.location.href = atob(e); }}
    function revealNSFW(c) {{ c.querySelector('img').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}
    </script>
    """

async def register(bot):
    sys.modules['__main__'].generate_html_code = fancy_ui_final
    print("🚀 [PLUGIN] FULL ORIGINAL THEME REPLICATED WITH RGB & CATEGORIES!")
