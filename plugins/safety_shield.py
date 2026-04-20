# plugins/safety_shield.py
import __main__
import base64
import re
import os
import requests
import logging

# --- ১. কনফিগারেশন ---
logger = logging.getLogger(__name__)

# আপনার দেওয়া ImgBB API Key
IMGBB_API_KEY = "1821270072482fb07921cfd72d31c37e"

ADULT_KEYWORDS = ["erotic", "porn", "sexy", "nudity", "adult", "18+", "nsfw", "hot scenes", "erotica"]
SAFE_PLACEHOLDER = "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png"

# --- ২. ইমেজ আপলোড সিস্টেম ওভাররাইড (Catbox to ImgBB) ---
def improved_upload_core(file_content):
    """সব ইমেজ ImgBB-তে আপলোড করার মেইন ইঞ্জিন"""
    try:
        url = "https://api.imgbb.com/1/upload"
        data = {"key": IMGBB_API_KEY}
        files = {"image": ("image.png", file_content)}
        resp = requests.post(url, data=data, files=files, timeout=25)
        if resp.status_code == 200:
            return resp.json()['data']['url']
    except Exception as e:
        logger.error(f"ImgBB Upload Error: {e}")
    return None

def patched_upload_to_catbox(file_path):
    try:
        with open(file_path, "rb") as f:
            return improved_upload_core(f.read())
    except: return None

def patched_upload_to_catbox_bytes(img_bytes):
    try:
        if hasattr(img_bytes, 'read'):
            img_bytes.seek(0)
            return improved_upload_core(img_bytes.read())
        return improved_upload_core(img_bytes)
    except: return None

# মেইন বটের ইমেজ ফাংশনগুলোকে ImgBB দিয়ে রিপ্লেস করা
__main__.upload_to_catbox = patched_upload_to_catbox
__main__.upload_to_catbox_bytes = patched_upload_to_catbox_bytes
__main__.upload_image_core = improved_upload_core


# --- ৩. কন্টেন্ট চেকার ---
def is_content_adult(data):
    if data.get('adult') or data.get('force_adult'): return True
    title = (data.get("title") or "").lower()
    overview = (data.get("overview") or "").lower()
    return any(word in title or word in overview for word in ADULT_KEYWORDS)


# --- ৪. প্রিমিয়াম স্ক্রিপ্ট ইনজেক্টর (OneSignal & Base64 Reveal) ---
def get_advanced_scripts():
    # ডাবল Adblock ও Schema রিমুভ করা হয়েছে কারণ অন্য প্লাগইনে সেটি আছে। 
    # এখানে শুধুমাত্র OneSignal এবং Base64 Image রিভিলার রাখা হলো।
    return """
    <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
    <script>
      window.OneSignalDeferred = window.OneSignalDeferred || [];
      OneSignalDeferred.push(async function(OneSignal) {
        await OneSignal.init({ appId: "d8b008a1-623d-495d-b10d-8def7460f2ea" });
      });

      // Override the default revealNSFW to support Base64 Cloaking
      function revealNSFW(container) {
        let img = container.querySelector('img');
        if(img) {
            // Base64 থেকে আসল ইমেজ লোড করা
            const raw = img.getAttribute('data-raw');
            if (raw) { 
                img.src = atob(raw); 
                img.removeAttribute('data-raw'); 
            }
            img.classList.remove('nsfw-blur');
            img.style.filter = "none";
            img.style.transform = "scale(1)";
        }
        let warning = container.querySelector('.nsfw-warning');
        if(warning) warning.style.display = 'none';
        
        container.style.cursor = 'default';
        container.onclick = null;
      }
    </script>
    """

# --- ৫. মেইন HTML জেনারেটর ওভাররাইড ---
if not hasattr(__main__, '_safety_shield_patched'):
    __main__.shield_old_html = __main__.generate_html_code

    def safety_shield_generator(data, links, user_ads, owner_ads, share):
        is_adult = is_content_adult(data)
        
        # বেসিক HTML জেনারেট করা (অন্য প্লাগইন সহ)
        html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
        
        if is_adult:
            # Base64 Image Cloaking: আসল ইমেজের লিংক সোর্স কোড থেকে লুকিয়ে ফেলা
            def secure_img_tags(match):
                img_src = match.group(1)
                
                # কিছু সাধারণ ইমেজ স্কিপ করা
                if any(x in img_src.lower() for x in ["logo", "telegram", "icon", "placeholder", "youtube"]): 
                    return match.group(0)
                
                encoded_url = base64.b64encode(img_src.encode()).decode()
                # আসল লিংকের জায়গায় সেফ প্লেসহোল্ডার এবং data-raw তে আসল লিংক
                return f'src="{SAFE_PLACEHOLDER}" data-raw="{encoded_url}"'

            # HTML এর ভেতরের সব ইমেজ লিংক এনকোড করা
            html = re.sub(r'src="([^"]+)"', secure_img_tags, html)

        # OneSignal এবং JS HTML এর শেষে যুক্ত করা
        return f"{html}\n{get_advanced_scripts()}"

    __main__.generate_html_code = safety_shield_generator
    __main__._safety_shield_patched = True

async def register(bot):
    print("🚀 Ultimate Safety Shield & ImgBB Engine: Activated Successfully!")
