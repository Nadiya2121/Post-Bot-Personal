# -*- coding: utf-8 -*-
import sys
import json
import base64
import random

# --- নতুন ডিজাইন ফাংশন যা মেইন কোডকে রিপ্লেস করবে ---
def new_generate_html_code(data, links, user_ad_links_list, owner_ad_links_list, admin_share_percent=20):
    title = data.get("title") or data.get("name")
    poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}"
    
    # লিঙ্ক গ্রুপিং লজিক
    watch_online_links = []
    download_groups = {
        "💎 4K ULTRA HD": [],
        "🎬 1080P FULL HD": [],
        "📽️ 720P HD": [],
        "📀 480P / SD": [],
        "📁 TELEGRAM FILES": []
    }

    for link in links:
        lbl = link.get('label', '').upper()
        if any(x in lbl for x in ["WATCH", "ONLINE", "STREAM", "প্লে"]):
            watch_online_links.append(link)
        elif "4K" in lbl or "2160" in lbl: download_groups["💎 4K ULTRA HD"].append(link)
        elif "1080" in lbl: download_groups["🎬 1080P FULL HD"].append(link)
        elif "720" in lbl: download_groups["📽️ 720P HD"].append(link)
        elif "480" in lbl: download_groups["📀 480P / SD"].append(link)
        else: download_groups["📁 TELEGRAM FILES"].append(link)

    # জেনারেট সার্ভার লিস্ট HTML
    server_html = ""
    
    # Watch Online Section (সবার উপরে)
    if watch_online_links:
        server_html += '<div class="cat-header">🍿 WATCH ONLINE / STREAM</div>'
        for wl in watch_online_links:
            url = wl.get('url') or wl.get('tg_url')
            enc = base64.b64encode(url.encode()).decode()
            server_html += f'<button class="rgb-btn watch-btn" onclick="goToLink(\'{enc}\')">▶️ {wl.get("label")}</button>'

    # Download Sections
    for q_name, q_links in download_groups.items():
        if q_links:
            server_html += f'<div class="cat-header">{q_name}</div>'
            for dl in q_links:
                url = dl.get('tg_url') or dl.get('url')
                enc = base64.b64encode(url.encode()).decode()
                server_html += f'<button class="rgb-btn dl-btn" onclick="goToLink(\'{enc}\')">📥 {dl.get("label")}</button>'

    # Ad revenue share
    weighted_ads = []
    if not user_ad_links_list:
        weighted_ads = owner_ad_links_list if owner_ad_links_list else ["https://google.com"]
    else:
        total_slots = 100
        admin_slots = int(admin_share_percent)
        user_slots = total_slots - admin_slots
        for _ in range(admin_slots): weighted_ads.append(random.choice(owner_ad_links_list))
        for _ in range(user_slots): weighted_ads.append(random.choice(user_ad_links_list))
    random.shuffle(weighted_ads)

    # ফুল CSS এবং HTML
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500;700&display=swap');
        
        body {{ background: #000; margin: 0; padding: 0; }}
        
        /* RGB Border Animation */
        .wrapper {{
            max-width: 500px;
            margin: 20px auto;
            position: relative;
            padding: 3px;
            background: linear-gradient(0deg, #000, #222);
            border-radius: 20px;
            overflow: hidden;
            z-index: 1;
        }}
        .wrapper::before {{
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: conic-gradient(#ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            animation: rotateRGB 3s linear infinite;
            z-index: -1;
        }}
        @keyframes rotateRGB {{ 100% {{ transform: rotate(360deg); }} }}

        .content {{
            background: #0d0d12;
            border-radius: 18px;
            padding: 20px;
            font-family: 'Rajdhani', sans-serif;
            color: #fff;
        }}

        .cat-header {{
            background: linear-gradient(90deg, #ff0055, #7a00ff);
            padding: 8px;
            text-align: center;
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            border-radius: 5px;
            margin: 20px 0 12px;
            box-shadow: 0 0 10px rgba(122, 0, 255, 0.5);
            letter-spacing: 1px;
        }}

        .rgb-btn {{
            width: 100%;
            padding: 15px;
            margin-bottom: 12px;
            border: 1px solid #333;
            border-radius: 10px;
            background: #16161d;
            color: #fff;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
            display: block;
            text-decoration: none;
            text-align: center;
        }}
        .rgb-btn:hover {{
            transform: scale(1.02);
            border-color: #00ffd5;
            box-shadow: 0 0 15px #00ffd5;
            color: #00ffd5;
        }}
        
        .watch-btn {{ border-color: #ffcc00; color: #ffcc00; }}

        .step-box {{
            background: #1a1a24;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px dashed #555;
            margin-top: 15px;
        }}
        .progress-container {{
            height: 8px;
            background: #333;
            border-radius: 10px;
            margin: 15px 0;
            overflow: hidden;
        }}
        .progress-bar {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #00ffd5, #7a00ff);
            transition: width 1s linear;
        }}
    </style>

    <div class="wrapper">
        <div class="content">
            <div id="unlock-ui">
                <img src="{poster}" style="width:100%; border-radius:10px; margin-bottom:15px;">
                <h2 style="text-align:center; font-family:'Orbitron'; font-size:18px;">{title}</h2>
                
                <div class="step-box">
                    <div id="step-label" style="color:#00ffd5; font-weight:bold;">STEP 1: Verify Identity</div>
                    <div class="progress-container"><div id="bar" class="progress-bar"></div></div>
                    <button class="rgb-btn" onclick="startUnlock(this)" style="background:#ff0055; border:none; color:white;">🔓 UNLOCK DOWNLOAD FILES</button>
                </div>
            </div>

            <div id="links-ui" style="display:none;">
                {server_html}
            </div>
        </div>
    </div>

    <script>
        const AD_LIST = {json.dumps(weighted_ads)};
        function startUnlock(btn) {{
            window.open(AD_LIST[Math.floor(Math.random() * AD_LIST.length)], '_blank');
            btn.disabled = true;
            btn.innerHTML = "⌛ Waiting 5 Seconds...";
            let p = 0;
            let iv = setInterval(() => {{
                p += 20;
                document.getElementById('bar').style.width = p + "%";
                if(p >= 100) {{
                    clearInterval(iv);
                    document.getElementById('step-label').innerHTML = "✅ STEP 2: Links Unlocked!";
                    setTimeout(() => {{
                        document.getElementById('unlock-ui').style.display = 'none';
                        document.getElementById('links-ui').style.display = 'block';
                        window.scrollTo(0,0);
                    }}, 500);
                }}
            }}, 1000);
        }}
        function goToLink(e) {{ window.location.href = atob(e); }}
    </script>
    """

# --- প্লাগইন রেজিস্ট্রেশন এবং মেইন কোড ওভাররাইড ---
async def register(bot):
    # পাইথনের মেইন মডিউল (main.py) এক্সেস করা
    main_module = sys.modules['__main__']
    
    # মেইন কোডের ফাংশনটিকে আমাদের নতুন ফাংশন দিয়ে রিপ্লেস করা (Monkey Patching)
    main_module.generate_html_code = new_generate_html_code
    
    print("🚀 [PLUGIN] Fancy RGB UI Loaded & Main Core Updated Successfully!")
