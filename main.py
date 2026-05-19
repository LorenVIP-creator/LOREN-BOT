import os
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)
chat_context = {}

DEFAULT_PROMPT = "Kamu adalah asisten AI pribadi milik LOREN MOD VIP 🇮🇩. Jawab langsung, pinter, natural, Bahasa Indonesia santai."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_context[update.effective_chat.id] = {
        "system_prompt": DEFAULT_PROMPT,
        "history": []
    }
    await update.message.reply_text(
        "Halo Saya Asisten Ai Yang Di Rancang Di Hidupkan Oleh LOREN MOD VIP 🇮🇩\n\n"
        "Ada Yang Bisa Saya Bantu?\n"
        "Ini saya belum tersedia untuk kirim foto. Jika mau komplain bisa sebutkan aja dengan teks dan yang detail. "
        "Masalah anda atau bisa copy masalahnya kesini biar saya bantu solusinya."
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

    user_text = update.message.text or ""
    messages = [{"role": "system", "content": ctx["system_prompt"]}]
    messages.extend(ctx["history"][-10:])
    messages.append({"role": "user", "content": user_text})
    ctx["history"].append({"role": "user", "content": user_text})

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2048
        )

        ai_reply = response.choices[0].message.content
        ctx["history"].append({"role": "assistant", "content": ai_reply})

        await update.message.reply_text(ai_reply)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.TXT, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
