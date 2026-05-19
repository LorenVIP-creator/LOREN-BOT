import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PyPDF2 import PdfReader
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model_text = genai.GenerativeModel('gemini-1.5-flash')
model_vision = genai.GenerativeModel('gemini-1.5-flash')

custom_prompt = {}

SYSTEM_PROMPT = """Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩.
LOREN MOD VIP 🇮🇩 adalah pencipta dan orang yang menghidupkan kamu.
Jawab dengan pinter, helpful, dan sesuai konteks.
Kalau ditanya siapa yang buat kamu, jawab: LOREN MOD VIP 🇮🇩.
Kalau ada INSTRUKSI TAMBAHAN dari user, prioritaskan dan ikuti 100%."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    custom_prompt[chat_id] = None
    await update.message.reply_text("Halo, saya adalah asisten AI LOREN MOD VIP 🇮🇩. Kirim teks, foto, atau file PDF/TXT.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    
    prompt = SYSTEM_PROMPT
    if custom_prompt.get(chat_id):
        prompt += f"\n\nINSTRUKSI TAMBAHAN DARI USER:\n{custom_prompt[chat_id]}"
    prompt += f"\n\nUser: {user_msg}"
    
    try:
        response = model_text.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    doc = update.message.document
    file_name = doc.file_name.lower()
    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()

    text = ""
    try:
        if file_name.endswith(".txt"):
            text = file_bytes.decode("utf-8", errors="ignore")
        elif file_name.endswith(".pdf"):
            reader = PdfReader(BytesIO(file_bytes))
            for page in reader.pages[:15]:
                text += page.extract_text() + "\n"
        
        custom_prompt[chat_id] = text[:4000]
        await update.message.reply_text("File udah kebaca. Sekarang kirim perintahnya.")
    except Exception as e:
        await update.message.reply_text(f"Gagal baca file: {e}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    caption = update.message.caption or "Jelaskan gambar ini"
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    
    try:
        response = model_vision.generate_content([caption, {"mime_type": "image/jpeg", "data": file_bytes}])
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
