import os
import base64
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Simpan riwayat chat per user. Format: {chat_id: [list pesan]}
chat_history = {}

SYSTEM_PROMPT = """Kamu adalah AI pribadi milik LOREN MOD VIP 🇮🇩.
LOREN MOD VIP 🇮🇩 adalah orang yang menghidupkan, merancang, dan menjalankan kamu di bot Telegram ini.
Selalu jawab dengan gaya santai, gaul, kayak ngobrol sama temen. Pakai emoji kalau cocok.
Jangan kaku, jangan kepanjangan, jangan jawab kayak robot resmi.
Kalau ditanya siapa yang buat kamu, jawab: LOREN MOD VIP 🇮🇩 lah bos.
Ingat semua konteks percakapan sebelumnya."""

MAX_HISTORY = 20 # Maksimal 20 pesan terakhir yang diinget biar gak boros token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_history[chat_id] = [] # Reset history pas /start
    await update.message.reply_text("Halo bos! Gue AI nya LOREN MOD VIP 🇮🇩. Mau ngobrol apa nih? 😎")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text

    if chat_id not in chat_history:
        chat_history[chat_id] = []

    chat_history[chat_id].append({"role": "user", "content": user_msg})

    if len(chat_history[chat_id]) > MAX_HISTORY:
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

    await query_groq(update, chat_history[chat_id])

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    doc = update.message.document
    file = await context.bot.get_file(doc.file_id)
    file_bytes = await file.download_as_bytearray()
    text = file_bytes.decode("utf-8", errors="ignore")

    if chat_id not in chat_history:
        chat_history[chat_id] = []

    msg = f"Baca file ini:\n{text}"
    chat_history[chat_id].append({"role": "user", "content": msg})
    await query_groq(update, chat_history[chat_id])

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    base64_image = base64.b64encode(file_bytes).decode("utf-8")

    messages = [
        {"type": "text", "text": "Jelaskan gambar ini"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]

    if chat_id not in chat_history:
        chat_history[chat_id] = []

    chat_history[chat_id].append({"role": "user", "content": messages})
    await query_groq(update, chat_history[chat_id])

async def query_groq(update: Update, messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *messages
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]

            chat_id = update.effective_chat.id
            chat_history[chat_id].append({"role": "assistant", "content": reply})

            await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot AI jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
