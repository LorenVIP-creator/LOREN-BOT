import os
import base64
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
chat_context = {}

DEFAULT_PROMPT = "Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩. Jawab langsung, pinter, natural, Bahasa Indonesia santai. Kalau ada foto, analisis fotonya dan jawab sesuai keluhan user."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_context[update.effective_chat.id] = {
        "system_prompt": DEFAULT_PROMPT,
        "history": []
    }
    await update.message.reply_text(
        "Halo Saya Asisten Ai Yang Di Rancang Di Hidupkan Oleh LOREN MOD VIP 🇮🇩\n\n"
        "Ada Yang Bisa Saya Bantu?\n"
        "Kirim foto + teks kalau mau komplain."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in chat_context:
        chat_context[chat_id] = {"system_prompt": DEFAULT_PROMPT, "history": []}
    ctx = chat_context[chat_id]

    # Upload file.txt = ganti prompt
    if update.message.document and update.message.document.file_name.lower().endswith(".txt"):
        file = await context.bot.get_file(update.message.document.file_id)
        file_bytes = await file.download_as_bytearray()
        new_prompt = file_bytes.decode("utf-8", errors="ignore")[:12000]
        ctx["system_prompt"] = new_prompt
        ctx["history"] = []
        await update.message.reply_text("✅ Prompt baru aktif. Sekarang bot nurut 100% ke file lu.")
        return

    user_text = update.message.caption or update.message.text or ""
    messages = [{"role": "system", "content": ctx["system_prompt"]}]

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Kalau ada foto, kirim tanpa history biar gak error 400
        if update.message.photo:
            photo_file = await context.bot.get_file(update.message.photo[-1].file_id)
            photo_bytes = await photo_file.download_as_bytearray()
            base64_image = base64.b64encode(photo_bytes).decode("utf-8")

            content = [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "text", "text": user_text or "Analisis foto ini dan jelaskan masalahnya."}
            ]
            messages.append({"role": "user", "content": content})

        # Kalau cuma teks, baru pake history biar nyambung
        else:
            messages.extend(ctx["history"][-10:])
            messages.append({"role": "user", "content": user_text})
            ctx["history"].append({"role": "user", "content": user_text})

        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )

        ai_reply = response.choices[0].message.content

        # Simpen reply ke history cuma kalau bukan pesan foto
        if not update.message.photo:
            ctx["history"].append({"role": "assistant", "content": ai_reply})

        await update.message.reply_text(ai_reply)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))
    app.add_handler(MessageHandler(filters.Document.TXT, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
