#!/usr/bin/env python3
import os
import logging
import asyncio
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.error import BadRequest

# ✅ Logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ✅ Load token and check
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REQUIRED_CHANNEL = '@bigboss_community_kh'

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in environment variables!")

# ✅ Create download folder
os.makedirs('downloads', exist_ok=True)

# ✅ Check if user joined channel
async def is_user_subscribed(chat_member):
    return chat_member.status in ['member', 'administrator', 'creator']

# ✅ Download with yt_dlp
def download_video(url, is_audio=False):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestaudio/best' if is_audio else 'best',
        'quiet': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if is_audio else [],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if is_audio:
            filename = filename.rsplit('.', 1)[0] + ".mp3"
        title = info.get("title", "Untitled")
        return filename, title

# ✅ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        chat_member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if await is_user_subscribed(chat_member):
            await update.message.reply_text("✅ សូមផ្ញើ Link YouTube / TikTok / Facebook មកខ្ញុំ")
        else:
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}")]]
            await update.message.reply_text("🚫 សូមចូលរួមក្នុង Channel មុនសិន!", reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest:
        await update.message.reply_text("⚠️ មិនអាចពិនិត្យបានទេ។")

# ✅ Receive URL
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.effective_user.id

    try:
        chat_member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if not await is_user_subscribed(chat_member):
            keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}")]]
            await update.message.reply_text("🚫 សូមចូលរួមក្នុង Channel មុន!", reply_markup=InlineKeyboardMarkup(keyboard))
            return
    except BadRequest:
        await update.message.reply_text("⚠️ មិនអាចពិនិត្យបានទេ។")
        return

    if not url.startswith("http"):
        await update.message.reply_text("❗ សូមផ្ញើ Link ត្រឹមត្រូវ...")
        return

    # ⚠️ Store per-user context with `chat_data` instead of `user_data` (safer)
    context.chat_data[update.effective_chat.id] = url

    keyboard = [
        [InlineKeyboardButton("🎧 Download MP3", callback_data="download_mp3")],
        [InlineKeyboardButton("📹 Download MP4", callback_data="download_mp4")]
    ]
    await update.message.reply_text("🔽 សូមជ្រើសទាញយក:", reply_markup=InlineKeyboardMarkup(keyboard))

# ✅ Button clicked (MP3 or MP4)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.chat_data.get(query.message.chat.id)
    if not url:
        await query.edit_message_text("❗ សូមផ្ញើ link ម្តងទៀត។")
        return

    is_audio = query.data == "download_mp3"
    kind = "MP3" if is_audio else "MP4"

    await query.edit_message_text(f"📥 កំពុងទាញយក {kind}...")

    try:
        filepath, title = download_video(url, is_audio)
        caption = f"✅ Title: {title}\n📁 Format: {kind}"
        with open(filepath, 'rb') as f:
            if is_audio:
                await query.message.reply_audio(audio=f, caption=caption)
            else:
                await query.message.reply_video(video=f, caption=caption)
        os.remove(filepath)
    except Exception as e:
        await query.message.reply_text(f"❌ បញ្ហា៖ {e}")

# ✅ Run bot
if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    logging.info("🤖 Bot is running...")
    app.run_polling()
