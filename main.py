import os
import time
import asyncio
import httpx
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
from PyPDF2 import PdfReader

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
user_cooldown = {}
user_history = defaultdict(list)
user_system_prompt = defaultdict(str)

# System prompt global biar bot selalu jawab creator nya lu
GLOBAL_SYSTEM_PROMPT = "Kamu dibuat dan dirancang oleh LOREN MOD VIP 🇮🇩. Jika ditanya siapa yang membuat, merancang, atau menciptakan kamu, jawab: LOREN MOD VIP 🇮🇩. Jangan jawab yang lain."

def search_web(query):
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
    await update.message.reply_text(
        "Halo Saya Asisten Ai Yang Di Rancang Di Hidupkan Oleh LOREN MOD VIP 🇮🇩\n\n"
        "Ada Yang Bisa Saya Bantu?\n"
        "Ini saya belum tersedia untuk kirim foto. Jika mau komplain bisa sebutkan aja dengan teks dan yang detail. "
        "Masalah anda atau bisa copy masalahnya kesini biar saya bantu solusinya."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = time.time()

    if user_id in user_cooldown:
        if now - user_cooldown[user_id] < 10:
            await update.message.reply_text("Tunggu 10 detik dulu bro")
            return

    user_msg = update.message.text
    user_history[user_id].append({"role": "user", "content": user_msg})

    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]

    keywords = ["2024", "2025", "2026", "terbaru", "sekarang", "hari ini", "kemarin", "harga", "berita", "juara", "update"]
    needs_search = any(k in user_msg.lower() for k in keywords)

    messages = []
    messages.append({"role": "system", "content": GLOBAL_SYSTEM_PROMPT})

    if user_system_prompt[user_id]:
        messages.append({"role": "system", "content": user_system_prompt[user_id]})

    if needs_search:
        search_result = search_web(user_msg)
        if search_result:
            messages.append({"role": "system", "content": f"Info terbaru dari web:\n{search_result}"})

    messages.extend(user_history[user_id])

    try:
        await asyncio.sleep(10) # delay 10 detik sebelum bales

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        user_history[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

        user_cooldown[user_id] = time.time() # set cooldown setelah bales

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    file = await update.message.document.get_file()
    file_path = f"/tmp/{update.message.document.file_name}"
    await file.download_to_drive(file_path)

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        if len(text) > 12000:
            text = text[:12000]

        user_system_prompt[user_id] = text

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Rangkum dan konfirmasi kamu paham instruksi ini. Setelah ini ikuti semua perintah user sesuai instruksi:\n{text}"}],
            max_tokens=800
        )
        await update.message.reply_text(f"File kebaca ✅\n\n{response.choices[0].message.content}")

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
