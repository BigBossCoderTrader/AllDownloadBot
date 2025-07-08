import os
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.error import BadRequest

# ⚙️ Bot Token and Channel
BOT_TOKEN = '7687165517:AAFU23-OuQvHYJZq7iBpyCuN0YdI7Z2zvi8'
REQUIRED_CHANNEL = '-1002580419003'  # ✅ Use numeric ID for private channel

# 📁 Ensure download directory
os.makedirs('downloads', exist_ok=True)

# ✅ Check subscription status
async def is_user_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# 📥 Download video or MP3
def download_video(url, is_audio=False):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',
        'format': 'bestaudio/best' if is_audio else 'best',
        'noplaylist': True,
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }] if is_audio else [],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        title = info.get("title", "Untitled")
        if is_audio:
            filename = filename.rsplit('.', 1)[0] + ".mp3"
        return filename, title

# ▶️ /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if await is_user_subscribed(context.bot, user_id):
        await update.message.reply_text("✅ សូមផ្ញើ Link YouTube / TikTok / Facebook មកខ្ញុំ")
    else:
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/bigboss_community_kh")]]
        await update.message.reply_text(
            "🚫 សូមចូលរួមក្នុង Channel មុនសិន!", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 💬 Handle messages (URLs)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()

    if not await is_user_subscribed(context.bot, user_id):
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/bigboss_community_kh")]]
        await update.message.reply_text("🚫 សូមចូលរួមក្នុង Channel មុន!", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if not url.startswith("http"):
        await update.message.reply_text("❗ សូមផ្ញើ Link ត្រឹមត្រូវ...")
        return

    context.user_data['url'] = url
    keyboard = [
        [InlineKeyboardButton("🎧 Download MP3", callback_data="download_mp3")],
        [InlineKeyboardButton("📹 Download MP4", callback_data="download_mp4")]
    ]
    await update.message.reply_text("🔽 សូមជ្រើសរើស:", reply_markup=InlineKeyboardMarkup(keyboard))

# 🔘 Handle download button
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = context.user_data.get('url')

    if not url:
        await query.edit_message_text("❗ សូមផ្ញើ link ម្តងទៀត។")
        return

    is_audio = query.data == "download_mp3"
    kind = "MP3" if is_audio else "MP4"

    await query.edit_message_text(f"📥 កំពុងទាញយក {kind}...")

    try:
        filepath, title = download_video(url, is_audio=is_audio)
        caption = f"✅ Title: {title}\n📁 Format: {kind}"
        if is_audio:
            await query.message.reply_audio(audio=open(filepath, 'rb'), caption=caption)
        else:
            await query.message.reply_video(video=open(filepath, 'rb'), caption=caption)
        os.remove(filepath)
    except Exception as e:
        await query.message.reply_text(f"❌ បញ្ហា៖ {e}")

# ▶️ Run bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Bot is running...")
    app.run_polling()
