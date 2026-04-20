# plugins/ultra_pro_ux.py
import __main__
import base64
import json

# --- 🎭 CLEAN ULTRA UX (NO FLOATING BUTTONS) ---
def get_ux_footer_code(data):
    backdrop = data.get('backdrop_path')
    # ব্যাকড্রপ না থাকলে শুধু কালো গ্রেডিয়েন্ট থাকবে, CSS ভাঙবে না
    if backdrop and not data.get('is_manual'):
        bg_url = f"https://image.tmdb.org/t/p/original{backdrop}"
        bg_css = f"background-image: linear-gradient(to bottom, rgba(5,6,10,0.8), #05060a), url('{bg_url}') !important;"
    else:
        bg_css = "background-image: linear-gradient(to bottom, #111, #000) !important;"
    
    return f"""
    <style>
        /* 🌌 ইমারসিভ সিনেমাটিক ব্যাকগ্রাউন্ড */
        body {{ 
            background: #05060a !important; 
            {bg_css}
            background-attachment: fixed !important;
            background-size: cover !important;
            background-position: center !important;
        }}
        
        /* 🏷️ মিডিয়া ব্যাজ ডিজাইন */
        .media-badges {{ display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }}
        .badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }}
        .badge-4k {{ color: #ffd700; border-color: #ffd700; }}
        .badge-hdr {{ color: #00d1b2; border-color: #00d1b2; }}
        
        /* ⏳ গ্লোয়িং প্রগ্রেস বার (বাটনের নিচে) */
        #unlock-timer {{ 
            width: 0%; height: 4px; background: linear-gradient(90deg, #E50914, #ff5252); 
            position: absolute; bottom: 0; left: 0; transition: width 5s linear; 
            box-shadow: 0 0 10px #E50914; 
        }}
    </style>
    
    <script>
    /* আনলক করার স্মার্ট টাইমার লজিক (Merged for Anti-Double Click) */
    function startUnlock(btn, type) {{
        if (typeof AD_LINKS !== 'undefined' && AD_LINKS.length > 0) {{
            let randomAd = AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)];
            window.open(randomAd, '_blank'); 
        }}
        
        // সব বাটন একসাথে লক করা
        let buttons = document.querySelectorAll('.main-btn');
        buttons.forEach(b => {{
            b.disabled = true;
            b.style.position = 'relative';
            b.style.overflow = 'hidden';
        }});
        
        btn.innerHTML = '<span style="position:relative; z-index:2;">⏳ UNLOCKING...</span><div id="unlock-timer"></div>';
        
        let timeLeft = 5;
        let timer = setInterval(function() {{
            timeLeft--;
            if (timeLeft < 0) {{
                clearInterval(timer);
                document.getElementById('view-details').style.display = 'none';
                document.getElementById('view-links').style.display = 'block';
                window.scrollTo({{top: 0, behavior: 'smooth'}});
            }} else {{
                btn.querySelector('span').innerText = "⏳ UNLOCKING " + timeLeft + "s";
            }}
        }}, 1000);
        
        setTimeout(() => {{ 
            let bar = document.getElementById('unlock-timer');
            if(bar) bar.style.width = '100%'; 
        }}, 50);
    }}
    </script>
    """

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (SAFE MODE)
# ==========================================================

# ⚠️ সেফটি গার্ড: অসীম লুপ ঠেকানোর জন্য
if not hasattr(__main__, '_ultra_pro_ux_patched'):
    # অরিজিনাল জেনারেটর সেভ করে রাখা
    original_html_generator = __main__.generate_html_code

    def blogger_friendly_generator(data, links, user_ads, owner_ads, share):
        # অরিজিনাল জেনারেটর কল করা
        html = original_html_generator(data, links, user_ads, owner_ads, share)
        
        title = data.get("title") or data.get("name", "Movie")
        plot = data.get("overview", "Download now")[:150]
        poster = data.get('manual_poster_url') or f"https://image.tmdb.org/t/p/w500{data.get('poster_path', '')}"
        
        # ১. 🖼️ থাম্বনেইল ফিক্স (ব্লগার ড্যাশবোর্ডের জন্য)
        thumbnail_html = f'<div style="height:0px;width:0px;overflow:hidden;visibility:hidden;display:none;float:left;"><img src="{poster}" alt="{title} Thumbnail" /></div>'
        
        # ২. 📝 ইনভিজিবল স্নিপেট (সার্চ প্রিভিউ এর জন্য)
        preview_snippet = f'<div style="display:none;font-size:1px;color:rgba(0,0,0,0);line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;">🎬 {title} - {plot}... Download now in High Quality.</div>'
        
        # ৩. 🏷️ মিডিয়া ব্যাজ (4K, HDR ইত্যাদি)
        quality = data.get('custom_quality', '').upper()
        badges_html = '<div class="media-badges">'
        badges_html += '<div class="badge">Dual Audio</div>'
        if '1080' in quality: badges_html += '<div class="badge badge-hdr">1080p Full HD</div>'
        if '4K' in quality or '2160' in quality: badges_html += '<div class="badge badge-4k">4K UHD</div>'
        badges_html += '<div class="badge">Dolby 5.1</div><div class="badge">HEVC</div></div>'
        
        # ৪. 💎 এসইও স্কিমা (গুগল র‍্যাঙ্কিং) - স্মার্ট চেকার যুক্ত করা হলো
        if 'type="application/ld+json"' not in html:
            schema_code = f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org","@type": "Movie","name": title,"image": poster,"description": plot})}</script>'
        else:
            schema_code = "" # আগে থেকেই থাকলে ডাবল করবে না
        
        # ৫. 🎨 সিএসএস এবং জেএস (যা নিচে থাকবে)
        footer_code = get_ux_footer_code(data)
        
        # ব্যাজগুলো মুভি টাইটেলের ঠিক উপরে বসানো
        html = html.replace('<div class="movie-title">', badges_html + '\n<div class="movie-title">')
        
        # ফাইনাল আউটপুট রিটার্ন করা
        return f"{thumbnail_html}\n{preview_snippet}\n{schema_code}\n{html}\n{footer_code}"

    # মেইন জেনারেটর রিপ্লেস করা
    __main__.generate_html_code = blogger_friendly_generator
    __main__._ultra_pro_ux_patched = True

async def register(bot):
    print("🚀 Ultra UX Clean Version (Cinematic Background & Blogger Fix) Activated!")
