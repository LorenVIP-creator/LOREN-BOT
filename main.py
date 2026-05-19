import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PyPDF2 import PdfReader
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

chat_history = {}
custom_prompt = {}

SYSTEM_PROMPT = """Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩.
LOREN MOD VIP 🇮🇩 adalah pencipta dan orang yang menghidupkan kamu.
Jawab dengan pinter, helpful, dan sesuai konteks.
Kalau ditanya siapa yang buat kamu, jawab: LOREN MOD VIP 🇮🇩.
Kalau ada INSTRUKSI TAMBAHAN dari user, prioritaskan dan ikuti 100%."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_history[chat_id] = []
    custom_prompt[chat_id] = None
    await update.message.reply_text("Halo, saya adalah asisten AI LOREN MOD VIP 🇮🇩. Ada yang bisa saya bantu?")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if custom_prompt.get(chat_id):
        messages.append({"role": "system", "content": f"INSTRUKSI TAMBAHAN:\n{custom_prompt[chat_id]}"})
    messages.append({"role": "user", "content": user_msg})
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    doc = update.message.document
    file_name = doc.file_name.lower()
    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()

    text = ""
    if file_name.endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="ignore")
    elif file_name.endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        for page in reader.pages[:10]:
            text += page.extract_text() + "\n"

    custom_prompt[chat_id] = text[:4000]
    await update.message.reply_text("File sudah saya baca. Silakan beri perintah.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Maaf, versi Groq belum support baca gambar. Pakai Gemini kalau mau fitur foto.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
