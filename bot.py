import os
import re
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import yt_dlp

# --- BOT TOKENI ---
BOT_TOKEN = "5852918966:AAGuRsYVMm07_3vaZ6oCs_7M2648Zsg9amU"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YOUTUBE_REGEX = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
INSTAGRAM_REGEX = r'(https?://)?(www\.)?instagram\.com/(p|reel|tv)/.+'

def download_media(url: str, download_type: str = "video", user_id: int = 0) -> str:
    output_template = os.path.join(DOWNLOAD_DIR, f"{user_id}_%(id)s.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    if download_type == "audio":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if download_type == "audio":
            filename = os.path.splitext(filename)[0] + ".mp3"
        return filename

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Xush kelibsiz! 👋\n\n"
        "Menga Instagram yoki YouTube havolasini (link) yuboring.\n"
        "Men videoni yoki qo'shiq (audio) ko'rinishida yuklab beraman!"
    )

@dp.message(F.text.regexp(YOUTUBE_REGEX))
async def handle_youtube(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Video", callback_data="yt_video"),
            InlineKeyboardButton(text="🎵 Audio (MP3)", callback_data="yt_audio")
        ]
    ])
    await message.answer("YouTube havolasi qabul qilindi. Formatni tanlang:", reply_markup=keyboard)

@dp.message(F.text.regexp(INSTAGRAM_REGEX))
async def handle_instagram(message: types.Message):
    url = message.text
    msg = await message.answer("📥 Instagram video yuklanmoqda...")
    try:
        file_path = await asyncio.to_thread(download_media, url, "video", message.from_user.id)
        await message.answer_video(video=FSInputFile(file_path), caption="✅ Video yuklab olindi!")
        await msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {str(e)}")

@dp.callback_query(F.data.in_({"yt_video", "yt_audio"}))
async def process_yt_download(callback: CallbackQuery):
    await callback.answer()
    url = callback.message.reply_to_message.text if callback.message.reply_to_message else None
    if not url:
        await callback.message.edit_text("❌ Havola topilmadi.")
        return

    download_type = "audio" if callback.data == "yt_audio" else "video"
    await callback.message.edit_text("🎵 Yuklanmoqda..." if download_type == "audio" else "🎬 Yuklanmoqda...")

    try:
        file_path = await asyncio.to_thread(download_media, url, download_type, callback.from_user.id)
        file_to_send = FSInputFile(file_path)
        if download_type == "audio":
            await callback.message.answer_audio(audio=file_to_send, caption="✅ Audio yuklab olindi!")
        else:
            await callback.message.answer_video(video=file_to_send, caption="✅ Video yuklab olindi!")
        await callback.message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {str(e)}")

async def main():
    print("Bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
