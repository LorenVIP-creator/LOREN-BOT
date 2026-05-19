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

SYSTEM_PROMPT = """Kamu adalah AI pribadi milik LOREN MOD VIP 🇮🇩.
LOREN MOD VIP 🇮🇩 adalah orang yang menciptakan, merancang, dan menghidupkan kamu.
Selalu jawab dengan gaya santai, gaul, kayak ngobrol sama temen. Pakai emoji kalau cocok.
Kalau ditanya siapa yang buat kamu, jawab: LOREN MOD VIP 🇮🇩 lah bos, gue cuma AI nya dia.
Tugas utama: baca dan ikuti instruksi dari file prompt yang user upload.
Setelah file prompt kebaca, semua perintah user setelahnya harus lu ikutin sesuai isi prompt itu.
Ingat semua konteks percakapan sebelumnya, jangan lupa siapa user dan apa yang udah dibahas."""

MAX_HISTORY = 30
MAX_FILE_CHARS = 4000

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_history[chat_id] = []
    await update.message.reply_text("Halo bos! Gue AI nya LOREN MOD VIP 🇮🇩. Kirim file prompt lu, gue bakal baca dan nurut 100% 😎")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_msg = update.message.text
    add_to_history(chat_id, {"role": "user", "content": user_msg})
    await query_groq(update, chat_history[chat_id])

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
        await update.message.reply_text("File harus.txt atau.pdf ya bos")
        return

    if len(text) > MAX_FILE_CHARS:
        text = text[:MAX_FILE_CHARS] + "\n\n[File kepotong karena kepanjangan]"

    msg = f"INI FILE PROMPT DARI LOREN MOD VIP 🇮🇩. BACA, PAHAMI, DAN IKUTI SEMUA INSTRUKSI DI DALAMNYA DARI SEKARANG:\n{text}"
    add_to_history(chat_id, {"role": "user", "content": msg})
    await query_groq(update, chat_history[chat_id])

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    base64_image = base64.b64encode(file_bytes).decode("utf-8")

    messages = [
        {"type": "text", "text": "Lihat gambar ini, pahami, dan simpan konteksnya untuk obrolan selanjutnya"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
    ]

    add_to_history(chat_id, {"role": "user", "content": messages})
    await query_groq(update, chat_history[chat_id])

def add_to_history(chat_id, message):
    if chat_id not in chat_history:
        chat_history[chat_id] = []
    chat_history[chat_id].append(message)
    if len(chat_history[chat_id]) > MAX_HISTORY:
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

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
            resp = await client.post(url, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            reply = resp.json()["choices"][0]["message"]["content"]

            chat_id = update.effective_chat.id
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

    print("Bot AI jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
