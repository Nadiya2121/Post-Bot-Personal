# plugins/bangla_guide.py
import __main__
import re

# --- 🎨 BANGLA GUIDE UI (কালারফুল বক্স ডিজাইন) ---
def get_bangla_guide_ui():
    return """
    <style>
        .guide-container {
            background: rgba(229, 9, 20, 0.05);
            border: 2px dashed #E50914;
            border-radius: 15px;
            padding: 20px;
            margin: 25px 0;
            font-family: 'Poppins', sans-serif;
            text-align: left;
            color: var(--text-main);
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.1);
        }
        .guide-header {
            color: #ff5252;
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
        }
        .step {
            display: flex;
            gap: 15px;
            margin-bottom: 12px;
            align-items: flex-start;
        }
        .step-num {
            background: #E50914;
            color: #fff;
            min-width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            flex-shrink: 0;
            margin-top: 2px;
            box-shadow: 0 0 10px rgba(229,9,20,0.5);
        }
        .step-text { font-size: 14px; line-height: 1.5; color: var(--text-muted); }
        .step-text b { color: #ffeb3b; }
        
        /* এনিমেশন */
        .guide-container { animation: borderPulse 2s infinite; }
        @keyframes borderPulse {
            0% { border-color: #E50914; }
            50% { border-color: #ff5252; }
            100% { border-color: #E50914; }
        }
    </style>
    
    <div class="guide-container">
        <div class="guide-header">
            🎬 মুভিটি কিভাবে দেখবেন বা ডাউনলোড করবেন?
        </div>
        
        <div class="step">
            <div class="step-num">১</div>
            <div class="step-text">নিচের <b>"Watch Online"</b> বা <b>"Download"</b> বাটনে ক্লিক করুন।</div>
        </div>
        
        <div class="step">
            <div class="step-num">২</div>
            <div class="step-text">বাটনে ক্লিক করলে একটি বিজ্ঞাপন (Ad) ওপেন হতে পারে, সেটি কেটে দিয়ে <b>এই পেজেই ফিরে আসুন</b>।</div>
        </div>
        
        <div class="step">
            <div class="step-num">৩</div>
            <div class="step-text">এরপর ৫ সেকেন্ড অপেক্ষা করুন। টাইমার শেষ হলে অটোমেটিক নিচের দিকে <b>সার্ভার লিস্ট এবং প্লেয়ার</b> খুলে যাবে।</div>
        </div>
        
        <div class="step">
            <div class="step-num">৪</div>
            <div class="step-text">আপনার পছন্দের যেকোনো সার্ভারে (যেমন: <b>GoFile, Filemoon বা Telegram</b>) ক্লিক করে হাই-স্পিডে মুভি উপভোগ করুন!</div>
        </div>
        
        <div style="font-size: 12px; color: #888; margin-top: 10px; text-align: center; font-style: italic;">
            ⚠️ যদি কোনো লিংক কাজ না করে, তবে টেলিগ্রাম গ্রুপে রিপোর্ট করুন।
        </div>
    </div>
    """

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (INJECT BANGLA GUIDE)
# ==========================================================

# ⚠️ Prevent infinite recursion (বট রিস্টার্ট বা ডাবল লোড হলে যাতে ক্র্যাশ না করে)
if not hasattr(__main__, "_bangla_guide_patched"):
    original_html_code_func = __main__.generate_html_code

    def bangla_guide_injector(data, links, user_ads, owner_ads, share):
        # অরিজিনাল কোডটি নেওয়া
        html = original_html_code_func(data, links, user_ads, owner_ads, share)
        
        # নতুন বাংলা গাইড বক্স তৈরি করা
        bangla_guide = get_bangla_guide_ui()
        
        # স্মার্ট Regex: পুরনো ইংরেজি বক্সটি যেকোনো স্পেস বা ইনডেন্টেশনে থাকলেও খুঁজে বের করবে
        pattern = re.compile(r'<div style="background: rgba\(0,0,0,0\.1\)[^>]*>.*?unlock automatically\.\s*</div>', re.DOTALL)
        
        if pattern.search(html):
            html = pattern.sub(bangla_guide, html) # পুরনোটা সরিয়ে নতুনটা বসাবে
        else:
            # ফলব্যাক: কোনো কারণে প্যাটার্ন না মিললে action-grid এর ঠিক আগে বসাবে
            html = html.replace('<div class="action-grid">', bangla_guide + '\n            <div class="action-grid">')
            
        return html

    # মেইন জেনারেটর রিপ্লেস করা
    __main__.generate_html_code = bangla_guide_injector
    __main__._bangla_guide_patched = True # ফ্ল্যাগ সেট করা হলো

async def register(bot):
    print("🚀 Bangla Download Guide Plugin: Activated Successfully!")
