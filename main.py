import os
import time
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from PyPDF2 import PdfReader

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
user_cooldown = {}

def search_web(query):
    """Search pake DuckDuckGo pakai httpx, nggak nambah dependency"""
    try:
        url = f"https://api.duckgo.com/?q={query}&format=json&no_html=1"
        with httpx.Client(timeout=5) as client:
            r = client.get(url)
            data = r.json()

        if data.get("AbstractText"):
            return data["AbstractText"]
        if data.get("Answer"):
            return data["Answer"]
        if data.get("RelatedTopics"):
            topics = [t["Text"] for t in data["RelatedTopics"] if "Text" in t]
            return "\n".join(topics[:3])
        return ""
    except:
        return ""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot jalan. Sekarang udah bisa cari info 2025-2026.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 10:
            await update.message.reply_text("Tunggu 10 detik dulu bro")
            return
    user_cooldown[user_id] = now

    user_msg = update.message.text

    keywords = ["2024", "2025", "2026", "terbaru", "sekarang", "hari ini", "kemarin", "harga", "berita", "juara"]
    needs_search = any(k in user_msg.lower() for k in keywords)

    context_text = user_msg
    if needs_search:
        search_result = search_web(user_msg)
        if search_result:
            context_text = f"Info terbaru dari web:\n{search_result}\n\nPertanyaan user: {user_msg}"

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": context_text}],
            max_tokens=1024
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 10:
            await update.message.reply_text("Tunggu 10 detik dulu bro")
            return
    user_cooldown[user_id] = now

    file = await update.message.document.get_file()
    file_path = f"/tmp/{update.message.document.file_name}"
    await file.download_to_drive(file_path)

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if len(text) > 8000:
            text = text[:8000]

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"Rangkum ini: {text}"}],
            max_tokens=1024
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Gagal baca PDF: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    print("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
