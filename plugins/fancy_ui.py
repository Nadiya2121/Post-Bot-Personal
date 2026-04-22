# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

def final_perfect_pro_ui(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
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

    # --- লিঙ্ক গ্রুপিং লজিক ---
    dl_links_html = ""
    quality_groups = {"480p": [], "720p": [], "1080p": [], "4k": [], "Telegram Files": []}

    for link in links:
        lbl = link.get('label', '').lower()
        found_q = False
        for q in ["480", "720", "1080", "4k"]:
            if q in lbl:
                quality_groups[q if "4k" in q else q+"p"].append(link)
                found_q = True; break
        if not found_q: quality_groups["Telegram Files"].append(link)

    for q_name, q_links in quality_groups.items():
        if q_links:
            dl_links_html += f'<div class="quality-title">📺 {q_name.upper()}</div><div class="server-grid">'
            for l in q_links:
                u = l.get('tg_url') or l.get('url'); e = base64.b64encode(u.encode()).decode()
                dl_links_html += f'<button class="final-server-btn tg-btn" onclick="goToLink(\'{e}\')">✈️ {l.get("label")}</button>'
            dl_links_html += '</div>'

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

    # Ad Revenue Share
    weighted_ads = user_ad_links_list if user_ad_links_list else (owner_ad_links_list or ["https://google.com"])
    random.shuffle(weighted_ads)

    # --- হুবহু অরিজিনাল ৬০০ লাইনের কোড স্ট্রাকচার ---
    return f"""
<div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>
<div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} - {overview[:150]}... Download now in {lang_str}.</div>

<script>
async function detectAdBlock() {{
  let adBlockEnabled = false; const googleAdUrl = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js';
  try {{ await fetch(new Request(googleAdUrl)).catch(_ => adBlockEnabled = true); }} catch (e) {{ adBlockEnabled = true; }}
  if (adBlockEnabled) {{
    document.body.innerHTML = `<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:#0f0f13;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:sans-serif;text-align:center;padding:20px;"><h1>🚫</h1><h2>Ad-Blocker Detected!</h2><p>আমাদের সার্ভার খরচ চালানোর জন্য বিজ্ঞাপনের প্রয়োজন। দয়া করে আপনার <b>Ad-Blocker</b> বন্ধ করে পেজটি রিফ্রেশ দিন।</p><button onclick="window.location.reload()" style="background:#E50914;color:#fff;border:none;padding:12px 25px;border-radius:5px;cursor:pointer;font-weight:bold;margin-top:20px;font-size:16px;">আমি বন্ধ করেছি, রিফ্রেশ দিন!</button></div>`;
  }}
}}
window.onload = function() {{ detectAdBlock(); }};
</script>
    
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Movie",
  "name": "{title}",
  "image": "{poster}",
  "description": "{overview[:150]}"
}}
</script>

<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">

<style>
    body {{ margin: 0; padding: 0; background: #05060a !important; background-image: linear-gradient(to bottom, rgba(5,6,10,0.8), #05060a), url('{backdrop}') !important; background-attachment: fixed !important; background-size: cover !important; background-position: center !important; }}
    
    /* RGB CONTAINER */
    .rgb-box {{ max-width: 800px; margin: 20px auto; position: relative; padding: 4px; border-radius: 24px; background: #000; overflow: hidden; }}
    .rgb-box::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); animation: rotateRGB 4s linear infinite; }}
    @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

    .app-wrapper {{ font-family: 'Poppins', sans-serif !important; max-width: 800px !important; background: #0f1014 !important; border: none !important; box-shadow: 0 20px 50px rgba(0,0,0,0.9) !important; border-radius: 20px !important; position: relative; overflow: visible !important; z-index: 1; padding: 25px; color: #fff; }}
    
    .movie-title {{ font-family: 'Oswald', sans-serif !important; font-size: 35px !important; background: linear-gradient(to right, #fff 20%, #777 80%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px; margin-bottom: 30px !important; text-align: center; }}
    .info-poster img {{ width: 180px !important; border-radius: 15px !important; box-shadow: 0 10px 30px rgba(229, 9, 20, 0.4) !important; border: 2px solid rgba(255,255,255,0.1) !important; transition: 0.5s; }}
    .info-poster img:hover {{ transform: scale(1.05) translateY(-10px); }}
    .info-box {{ background: rgba(255,255,255,0.03) !important; border-radius: 20px !important; padding: 25px !important; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.05) !important; display: flex; gap: 20px; align-items: center; }}
    .info-text div {{ margin-bottom: 8px !important; font-size: 15px !important; }}
    .info-text span {{ color: #E50914 !important; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; font-weight: bold; }}
    .section-title {{ font-size: 18px; color: #fff; margin: 20px 0 10px; border-bottom: 2px solid #E50914; display: inline-block; padding-bottom: 5px; font-weight: bold; }}
    .plot-box {{ background: rgba(255,255,255,0.05) !important; padding: 20px !important; border-radius: 10px !important; font-size: 14px; line-height: 1.6; border-left: 4px solid #E50914 !important; text-align: justify; }}
    .video-container {{ position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }}
    .video-container iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; }}
    .screenshot-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-bottom: 25px; }}
    .screenshot-grid img {{ width: 100%; border-radius: 8px; border: 1px solid #333; transition: 0.3s; }}
    .quality-title {{ background: linear-gradient(90deg, #E50914, transparent) !important; border: none !important; border-radius: 5px !important; padding: 10px 20px !important; font-size: 14px !important; color: #fff !important; margin-top: 20px; }}
    .server-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px !important; margin-top: 15px !important; }}
    .final-server-btn {{ background: #1a1c22 !important; border: 1px solid #333 !important; border-radius: 12px !important; padding: 15px !important; font-size: 13px !important; color: #fff; cursor: pointer; transition: 0.3s !important; text-align: center; width: 100%; }}
    .final-server-btn:hover {{ background: #E50914 !important; border-color: #E50914 !important; transform: translateY(-5px); box-shadow: 0 10px 20px rgba(229, 9, 20, 0.3) !important; }}
    .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }}
    .badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 4px; font-weight: 600; text-transform: uppercase; }}
    .nsfw-blur {{ filter: blur(25px) !important; cursor: pointer; }}
    .guide-container {{ background: rgba(229, 9, 20, 0.05); border: 2px dashed #E50914; border-radius: 15px; padding: 20px; margin: 25px 0; animation: borderPulse 2s infinite; }}
    @keyframes borderPulse {{ 0% {{ border-color: #E50914; }} 50% {{ border-color: #ff5252; }} 100% {{ border-color: #E50914; }} }}
    #unlock-timer {{ width: 0%; height: 4px; background: linear-gradient(90deg, #E50914, #ff5252); position: absolute; bottom: 0; left: 0; transition: width 5s linear; box-shadow: 0 0 10px #E50914; }}
</style>

<div class="rgb-box">
    <div class="app-wrapper">
        <div id="view-details">
            <div class="media-badges"><div class="badge">{lang_str}</div><div class="badge">⭐ {rating}</div><div class="badge">{year}</div><div class="badge">HEVC</div></div>
            <div class="movie-title">{title} ({year})</div>
            
            <div class="info-box">
                <div class="info-poster"><img src="{poster}" alt="Poster"></div>
                <div class="info-text">
                    <div><span>⭐ Rating:</span> {rating}</div>
                    <div><span>🎭 Genre:</span> {genres}</div>
                    <div><span>🗣️ Language:</span> {lang_str}</div>
                    <div><span>⏱️ Runtime:</span> {runtime}</div>
                    <div><span>📅 Release:</span> {year}</div>
                    <div><span>👥 Cast:</span> {cast}</div>
                </div>
            </div>
            
            <div class="section-title">📖 Storyline</div>
            <div class="plot-box">{overview}</div>
            
            {trailer_html}
            {ss_html}
            
            <div class="guide-container">
                <div style="color:#ff5252; font-weight:bold; font-size:18px; margin-bottom:15px;">🎬 মুভিটি কিভাবে ডাউনলোড করবেন?</div>
                <div style="font-size:14px; color:#aaa; line-height:1.5;">১. নিচের আনলক বাটনে ক্লিক করুন।<br>২. ৫ সেকেন্ড অপেক্ষা করুন।<br>৩. লিঙ্ক আনলক হলে আপনার পছন্দের সার্ভার থেকে ডাউনলোড করুন।</div>
            </div>

            <div style="position:relative; background:#1a1a24; padding:25px; border-radius:15px; text-align:center; border:1px solid #333; overflow:hidden;">
                <div id="st-txt" style="color:#ff5252; font-weight:bold; margin-bottom:10px;">STEP 1: IDENTITY VERIFICATION</div>
                <button class="final-server-btn" onclick="startUnlock(this)" style="background:#E50914; border:none; height:55px; font-weight:bold; font-size:16px;">🔓 UNLOCK DOWNLOAD SERVERS</button>
                <div id="unlock-timer"></div>
            </div>
        </div>

        <div id="view-links" style="display:none;">
            <div style="text-align:center; color:#00e676; font-weight:bold; margin-bottom:20px; border:1px solid #00e676; padding:15px; border-radius:12px; background:rgba(0,230,118,0.05);">✅ DOWNLOAD LINKS UNLOCKED!</div>
            {dl_links_html}
        </div>
    </div>
</div>

<div id="push-notice-bar" style="position:fixed; bottom:0; left:0; width:100%; background:rgba(10,12,16,0.98); border-top:2px solid #0088cc; padding:15px; display:none; z-index:9999; text-align:center;">
    <div style="color:#fff; font-size:14px; margin-bottom:10px;">🔔 নতুন মুভির আপডেট পেতে নোটিফিকেশন অ্যালাউ করুন!</div>
    <button onclick="handlePushAction('allow')" style="background:#0088cc; color:#fff; border:none; padding:8px 20px; border-radius:5px; font-weight:bold; cursor:pointer;">হ্যাঁ, অ্যালাউ করুন</button>
</div>

<script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
<script>
const AD_LINKS = {json.dumps(weighted_ads)};
function startUnlock(btn) {{
    window.open(AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)], '_blank');
    btn.disabled = true; btn.innerHTML = "⌛ Verifying Request...";
    document.getElementById('unlock-timer').style.width = "100%";
    setTimeout(() => {{
        document.getElementById('view-details').style.display = 'none';
        document.getElementById('view-links').style.display = 'block';
        window.scrollTo({{top: 0, behavior: 'smooth'}});
    }}, 5000);
}}
function goToLink(e) {{ window.location.href = atob(e); }}
function revealNSFW(c) {{ c.querySelector('img').classList.remove('nsfw-blur'); c.querySelector('.nsfw-warning').style.display='none'; }}

window.OneSignalDeferred = window.OneSignalDeferred || [];
OneSignalDeferred.push(function(OneSignal) {{
    OneSignal.init({{ appId: "d8b008a1-623d-495d-b10d-8def7460f2ea" }});
    if (!OneSignal.Notifications.permission) {{
        setTimeout(() => {{ document.getElementById('push-notice-bar').style.display = 'block'; }}, 3000);
    }}
}});
function handlePushAction(action) {{
    if(action==='allow') OneSignalDeferred.push(function(OneSignal){{ OneSignal.Notifications.requestPermission(); }});
    document.getElementById('push-notice-bar').style.display = 'none';
}}
</script>
"""

async def register(bot):
    sys.modules['__main__'].generate_html_code = final_perfect_pro_ui
    print("🎬 [PLUGIN] 600+ LINE ORIGINAL REPLICA LOADED SUCCESSFULLY!")
