import os
import base64
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from PyPDF2 import PdfReader
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

chat_history = {}
custom_prompt = {}

SYSTEM_PROMPT = """Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩.
LOREN MOD VIP 🇮🇩 adalah pencipta dan orang yang menghidupkan kamu.
Jawab dengan pinter, helpful, dan sesuai konteks.
Kalau ditanya siapa yang buat kamu, jawab: LOREN MOD VIP 🇮🇩.
Kalau ada INSTRUKSI TAMBAHAN dari user, prioritaskan dan ikuti 100%."""

MAX_HISTORY = 20

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_history[chat_id] = []
    custom_prompt[chat_id] = None
    await update.message.reply_text(
        "Halo, saya adalah asisten AI LOREN MOD VIP 🇮🇩. Ada yang bisa saya bantu?"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    add_to_history(chat_id, {"role": "user", "content": user_msg})
    await query_groq(update, chat_id)

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
        try:
            reader = PdfReader(BytesIO(file_bytes))
            for page in reader.pages[:10]:
                text += page.extract_text() + "\n"
        except Exception as e:
            await update.message.reply_text(f"Gagal baca PDF: {e}")
            return
    else:
        await update.message.reply_text("Kirim file.txt atau.pdf aja ya")
        return

    if len(text) > 4000:
        text = text[:4000] + "\n\n[File kepotong]"

    custom_prompt[chat_id] = text
    await update.message.reply_text("File sudah saya baca. Silakan beri perintah, saya akan mengikutinya.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    caption = update.message.caption or "Jelaskan gambar ini"

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    base64_image = base64.b64encode(file_bytes).decode("utf-8")

    history_clean = [m for m in chat_history.get(chat_id, []) if isinstance(m["content"], str)]
    messages_for_api = build_messages(chat_id, history_clean)
    messages_for_api.append({
        "role": "user",
        "content": [
            {"type": "text", "text": caption},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
    })

    await query_groq_with_messages(update, messages_for_api)
    add_to_history(chat_id, {"role": "user", "content": f"[Kirim gambar]: {caption}"})

def build_messages(chat_id, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if custom_prompt.get(chat_id):
        messages.append({"role": "system", "content": f"INSTRUKSI TAMBAHAN DARI USER:\n{custom_prompt[chat_id]}"})
    messages.extend(history)
    return messages

def add_to_history(chat_id, message):
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(message)
    if len(chat_history[chat_id]) > MAX_HISTORY:
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

async def query_groq(update: Update, chat_id):
    messages = build_messages(chat_id, chat_history.get(chat_id, []))
    await query_groq_with_messages(update, messages)

async def query_groq_with_messages(update: Update, messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": messages
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]

        chat_id = update.effective_chat.id
        if len(messages) > 0 and isinstance(messages[-1]["content"], str):
            add_to_history(chat_id, {"role": "assistant", "content": reply})

        await update.message.reply_text(reply)
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
