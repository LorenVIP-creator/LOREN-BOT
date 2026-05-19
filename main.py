import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
chat_context = {}

SYSTEM_PROMPT = """Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩.
Paham semua konteks percakapan dan file. Ikuti perintah user 100% tanpa nanya balik.
Jawab langsung, pinter, natural, Bahasa Indonesia santai."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_context[update.effective_chat.id] = {"file_content": None}
    await update.message.reply_text("Halo, saya asisten AI LOREN MOD VIP 🇮🇩")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or update.message.caption or ""
    ctx = chat_context.get(chat_id, {"file_content": None})

    # Kalau ada file di message ini, baca dulu
    if update.message.document:
        doc = update.message.document
        if doc.file_name.lower().endswith((".txt", ".pdf")):
            file = await context.bot.get_file(doc.file_id)
            file_bytes = await file.download_as_bytearray()
            try:
                if doc.file_name.lower().endswith(".txt"):
                    file_text = file_bytes.decode("utf-8", errors="ignore")
                else:
                    from PyPDF2 import PdfReader
                    from io import BytesIO
                    reader = PdfReader(BytesIO(file_bytes))
                    file_text = "".join(page.extract_text() for page in reader.pages[:20])
                ctx["file_content"] = file_text[:12000]
            except:
                pass

    # Build prompt
    full_prompt = SYSTEM_PROMPT
    if ctx["file_content"]:
        full_prompt += f"\n\nKONTEKS FILE:\n{ctx['file_content']}"
    full_prompt += f"\n\nUSER: {text}"

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION | filters.Document.ALL, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
