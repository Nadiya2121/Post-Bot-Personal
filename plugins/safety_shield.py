# -*- coding: utf-8 -*-
import __main__
import requests
import logging

logger = logging.getLogger(__name__)

# আপনার দেওয়া ImgBB API Key
IMGBB_API_KEY = "1821270072482fb07921cfd72d31c37e"

# --- ২. ইমেজ আপলোড সিস্টেম ওভাররাইড (Catbox থেকে ImgBB) ---
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
    with open(file_path, "rb") as f:
        return improved_upload_core(f.read())

def patched_upload_to_catbox_bytes(img_bytes):
    if hasattr(img_bytes, 'read'):
        img_bytes.seek(0)
        return improved_upload_core(img_bytes.read())
    return improved_upload_core(img_bytes)

# =======================================================
# 🚀 PLUGIN REGISTER
# =======================================================
async def register(bot):
    # মেইন বটের ছবি আপলোডের ফাংশনগুলোকে ImgBB দিয়ে রিপ্লেস করা হলো
    __main__.upload_to_catbox = patched_upload_to_catbox
    __main__.upload_to_catbox_bytes = patched_upload_to_catbox_bytes
    __main__.upload_image_core = improved_upload_core
    
    print("🚀 [PLUGIN] ImgBB Superfast Upload Engine Activated Successfully!")
