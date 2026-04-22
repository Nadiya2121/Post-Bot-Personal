# plugins/ultra_pro_ux.py
import __main__
import base64
import json
import re

# --- 🎭 CINEMATIC ULTRA UX V2 (BEAUTY & STORAGE FIX) ---
def get_ux_footer_code(data):
    backdrop = data.get('backdrop_path')
    if backdrop and not data.get('is_manual'):
        bg_url = f"https://image.tmdb.org/t/p/original{backdrop}"
        bg_css = f"background-image: linear-gradient(to bottom, rgba(5,6,10,0.85), #05060a), url('{bg_url}') !important;"
    else:
        bg_css = "background-image: linear-gradient(to bottom, #111, #000) !important;"
    
    return f"""
    <style>
        body {{ 
            background: #05060a !important; 
            {bg_css}
            background-attachment: fixed !important;
            background-size: cover !important;
            background-position: center !important;
            color: #eee;
        }}
        
        /* 💎 গ্লাস-মরফিজম কন্টেইনার */
        .app-wrapper {{
            background: rgba(20, 20, 30, 0.7) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.1) !important;
            box-shadow: 0 20px 50px rgba(0,0,0,0.8) !important;
        }}

        /* 📋 ইনফরমেশন টেবিল (Year, Lang, Quality) */
        .info-table {{
            width: 100%; border-collapse: collapse; margin: 15px 0;
            font-size: 13px; background: rgba(0,0,0,0.3); border-radius: 8px; overflow: hidden;
        }}
        .info-table td {{
            padding: 10px; border: 1px solid rgba(255,255,255,0.05);
        }}
        .info-label {{ color: #ff5252; font-weight: bold; text-transform: uppercase; width: 35%; }}
        .info-val {{ color: #fff; }}

        /* 🏷️ ব্যাজগুলো আরও প্রিমিয়াম */
        .media-badges {{ display: flex; gap: 6px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }}
        .badge {{ 
            background: linear-gradient(45deg, #222, #333); 
            border: 1px solid rgba(255,255,255,0.1); 
            color: #fff; font-size: 10px; padding: 4px 12px; border-radius: 20px; 
            font-weight: 600; text-transform: uppercase;
        }}
        .badge-vip {{ background: linear-gradient(45deg, #f39c12, #e67e22); color: #000; }}

        /* 📁 সুন্দর এপিসোড গ্রিড */
        .server-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)) !important;
            gap: 10px !important;
        }}
        .tg-btn {{
            background: rgba(0, 136, 204, 0.2) !important;
            border: 1px solid #0088cc !important;
            padding: 10px 5px !important;
            font-size: 12px !important;
            border-radius: 6px !important;
            transition: 0.3s;
        }}
        .tg-btn:hover {{ background: #0088cc !important; transform: translateY(-3px); }}

        #unlock-timer {{ 
            width: 0%; height: 4px; background: linear-gradient(90deg, #00c8ff, #0088cc); 
            position: absolute; bottom: 0; left: 0; transition: width 5s linear; 
        }}
    </style>
    """

# ==========================================================
# 🔥 IMPROVED PATCH: HTML GENERATOR
# ==========================================================

if not hasattr(__main__, '_ultra_pro_ux_patched'):
    original_html_generator = __main__.generate_html_code

    def blogger_friendly_generator(data, links, user_ads, owner_ads, share):
        # অরিজিনাল কোড থেকে ডেটা নেওয়া
        title = data.get("title") or data.get("name", "Movie")
        year = (data.get("release_date") or data.get("first_air_date") or "----")[:4]
        lang = data.get('custom_language', 'Dual Audio')
        quality = data.get('custom_quality', 'HD')
        rating = f"{data.get('vote_average', 0):.1f}/10"
        poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}"

        # ১. ইনফরমেশন টেবিল তৈরি (যা তুমি চেয়েছিলে)
        info_table = f"""
        <table class="info-table">
            <tr><td class="info-label">📅 Release</td><td class="info-val">{year}</td></tr>
            <tr><td class="info-label">🗣️ Language</td><td class="info-val">{lang}</td></tr>
            <tr><td class="info-label">💿 Quality</td><td class="info-val">{quality}</td></tr>
            <tr><td class="info-label">⭐ Rating</td><td class="info-val">{rating}</td></tr>
        </table>
        """

        # ২. অরিজিনাল জেনারেটর কল করা
        html = original_html_generator(data, links, user_ads, owner_ads, share)

        # ৩. টেবিল এবং ব্যাজ বসানো (টাইটেলের নিচে)
        badges = f'<div class="media-badges"><div class="badge badge-vip">PREMIUM</div><div class="badge">{quality}</div><div class="badge">HEVC</div></div>'
        
        # ৪. মুভি ইনফো বক্স রিপ্লেস করা (পুরান ডিজাইন সরিয়ে নতুন টেবিল দেওয়া)
        if '<div class="info-text">' in html:
            # পুরানো টেক্সট সরিয়ে নতুন টেবিল ইনজেক্ট করা
            html = re.sub(r'<div class="info-text">.*?</div>', f'<div class="info-text">{info_table}</div>', html, flags=re.DOTALL)

        # ৫. ব্যাজ ইনজেক্ট করা
        html = html.replace('<div class="movie-title">', badges + '<div class="movie-title">')

        # এসইও এবং থাম্বনেইল ফিক্স
        thumbnail_fix = f'<div style="display:none;"><img src="{poster}" /></div>'
        footer_code = get_ux_footer_code(data)

        return f"{thumbnail_fix}\n{html}\n{footer_code}"

    __main__.generate_html_code = blogger_friendly_generator
    __main__._ultra_pro_ux_patched = True

async def register(bot):
    print("💎 Ultra UX V2 (Table Design & Glassmorphism) Activated!")
