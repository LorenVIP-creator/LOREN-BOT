import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

custom_prompt = {}

SYSTEM_PROMPT = """Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩.
Jawab dengan pinter, helpful, dan sesuai konteks.
Kalau ada INSTRUKSI TAMBAHAN dari user, prioritaskan dan ikuti 100%."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    custom_prompt[chat_id] = None
    await update.message.reply_text("Halo, saya adalah asisten AI LOREN MOD VIP 🇮🇩. Kirim teks atau file PDF/TXT.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    
    prompt = SYSTEM_PROMPT
    if custom_prompt.get(chat_id):
        prompt += f"\n\nINSTRUKSI TAMBAHAN DARI USER:\n{custom_prompt[chat_id]}"
    prompt += f"\n\nUser: {user_msg}"
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile"
        )
        await update.message.reply_text(chat_completion.choices[0].message.content)
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
            from PyPDF2 import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(file_bytes))
            for page in reader.pages[:15]:
                text += page.extract_text() + "\n"
        
        custom_prompt[chat_id] = text[:4000]
        await update.message.reply_text("File udah kebaca. Sekarang kirim perintahnya.")
    except Exception as e:
        await update.message.reply_text(f"Gagal baca file: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()
