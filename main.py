import os
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Gue bot AI 100%.\nKirim teks, PDF, TXT, atau foto. Terus kasih perintah mau diapain.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    await reply_ai(user_msg, update)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith((".pdf", ".txt")):
        await update.message.reply_text("Cuma bisa baca PDF dan TXT.")
        return

    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()

    if doc.file_name.endswith(".txt"):
        content = file_bytes.decode("utf-8", errors="ignore")
    else:
        content = "File PDF diterima. Gue belum bisa ekstrak teks PDF di kode basic ini. Upload TXT aja dulu biar pasti kebaca."

    user_cmd = update.message.caption or "Ringkas isi file ini"
    await reply_ai(f"{user_cmd}\n\nIsi file:\n{content}", update)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()

    # Kirim ke Groq Vision
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"image": file_bytes}
    data = {"prompt": update.message.caption or "Jelaskan gambar ini"}

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json={
                    "model": "llama-3.2-90b-vision-preview",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": data["prompt"]},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{file_bytes.hex()}"}}
                        ]
                    }]
                },
                timeout=60
            )
            reply = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Gagal baca gambar: {e}"

    await update.message.reply_text(reply)

async def reply_ai(prompt, update):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(API_URL, headers=headers, json=payload, timeout=30)
            reply = r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"Error: {e}"
    await update.message.reply_text(reply)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot AI jalan...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())