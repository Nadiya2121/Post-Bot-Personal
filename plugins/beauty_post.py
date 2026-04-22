import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- সুন্দর ডিজাইনের জন্য কিছু কনস্ট্যান্ট ---
TOP_BORDER = "╔════════════════════════╗"
MID_BORDER = "╠════════════════════════╝"
BTM_BORDER = "╚════════════════════════╝"
BULLET = "╟"

async def register(bot: Client):
    # এই ফাংশনটি বট স্টার্ট হওয়ার সময় অটোমেটিক রান হবে
    print("🎨 Beauty Post Plugin Loaded!")

# --- ১. সুন্দর ক্যাপশন জেনারেটর (এটি একটি হেল্পার ফাংশন) ---
def get_beauty_caption(details, pid=None):
    title = details.get("title") or details.get("name") or "N/A"
    year = (details.get("release_date") or details.get("first_air_date") or "----")[:4]
    rating = f"⭐ {details.get('vote_average', 0):.1f}/10"
    genre = details.get("genres", "Movie")
    if isinstance(genre, list):
        genre = ", ".join([g['name'] for g in genre[:3]])
    
    lang = details.get("custom_language", "Dual Audio")
    quality = details.get("custom_quality", "HD")
    
    # ডিজাইন শুরু
    caption = f"✨ **{TOP_BORDER}**\n"
    caption += f"🎬 **{title.upper()} ({year})**\n"
    caption += f"**{MID_BORDER}**\n\n"
    
    caption += f"{BULLET} 🎭 **Genre:** {genre}\n"
    caption += f"{BULLET} 🗣️ **Language:** {lang}\n"
    caption += f"{BULLET} 💿 **Quality:** {quality}\n"
    caption += f"{BULLET} {rating}\n\n"
    
    if details.get("overview"):
        plot = details.get("overview")[:150] + "..."
        caption += f"📝 **Storyline:** _{plot}_\n\n"
    
    caption += f"**{BTM_BORDER}**\n"
    caption += f"✨ _Powered by @{bot.me.username}_"
    
    return caption

# --- ২. এপিসোড বাটনগুলো সুন্দরভাবে সাজানো (Grid Style) ---
def get_series_buttons(links):
    buttons = []
    row = []
    
    # লিংকগুলোকে প্রসেস করে বাটনে রূপান্তর
    for i, link in enumerate(links):
        label = link.get('label', f'EP {i+1}')
        # বাটন লেবেল সুন্দর করা
        if "1080p" in label.lower(): btn_text = f"💎 {label}"
        elif "720p" in label.lower(): btn_text = f"💿 {label}"
        elif "480p" in label.lower(): btn_text = f"📱 {label}"
        else: btn_text = f"🚀 {label}"
        
        url = link.get('url') or link.get('tg_url')
        row.append(InlineKeyboardButton(btn_text, url=url))
        
        # প্রতি লাইনে ২টা করে বাটন
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)

# --- ৩. কাস্টম কমান্ড যা আপনার পোস্টকে প্রিভিউ করবে ---
@bot.on_message(filters.command("preview") & filters.private)
async def preview_beauty_post(client, message):
    # এটি শুধু চেক করার জন্য যে ডিজাইন কেমন হয়েছে
    dummy_details = {
        "title": "Sample Movie",
        "release_date": "2024-01-01",
        "vote_average": 8.5,
        "genres": [{"name": "Action"}, {"name": "Sci-Fi"}],
        "custom_language": "Hindi-English",
        "custom_quality": "1080p Bluray",
        "overview": "This is a beautiful preview of how your post will look with the new beauty plugin."
    }
    
    cap = get_beauty_caption(dummy_details)
    test_links = [
        {"label": "Episode 01", "url": "https://t.me/google"},
        {"label": "Episode 02", "url": "https://t.me/google"},
        {"label": "Episode 03", "url": "https://t.me/google"},
        {"label": "Episode 04", "url": "https://t.me/google"}
    ]
    
    await message.reply_text(cap, reply_markup=get_series_buttons(test_links))
