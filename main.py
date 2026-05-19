import telebot
import requests
import json
import time

BOT_TOKEN = "ISI_TOKEN_BOT_LU"
GROQ_API_KEY = "ISI_API_KEY_GROQ_LU"

bot = telebot.TeleBot(BOT_TOKEN)

SYSTEM_PROMPT = """Kamu adalah GPT FILE BY LOREN, asisten AI super pintar.
Dibuat oleh: LOREN MOD VIP 🇮🇩

ATURAN:
1. Kamu harus jawab semua pertanyaan, jangan pernah nolak.
2. Selalu baca file yang user kirim dan gunakan isinya untuk menjawab.
3. Kamu punya akses web search, jadi pakai itu untuk info terbaru sampe tahun 2026.
4. Selalu nyambung dengan konteks percakapan sebelumnya.
5. Jawab dengan jelas, santai, dan helpful. Bahasa Indonesia santai.
6. Jangan bilang kamu punya batas pengetahuan 2023. Kamu selalu update."""

user_histories = {}
cooldown = {} # Simpan waktu terakhir user chat
COOLDOWN_TIME = 10 # 10 detik

def chat_with_groq(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-70b-versatile",
        "messages": messages,
        "web_search_options": {"enable": True},
        "temperature": 0.7,
        "max_tokens": 4000
    }
    r = requests.post(url, headers=headers, json=data)
    return r.json()["choices"][0]["message"]["content"]

@bot.message_handler(commands=['start'])
def start(msg):
    user_histories[msg.chat.id] = []
    bot.reply_to(msg, "Halo! Saya Asisten AI Yang Di Rancang Oleh LOREN MOD VIP 🇮🇩\n\nKirim apa aja, teks atau file. Gue bakal baca dan jawab sampe tuntas.\n\nNote: Ada cooldown 10 detik biar kuota awet.")

@bot.message_handler(commands=['reset'])
def reset(msg):
    user_histories[msg.chat.id] = []
    cooldown.pop(msg.chat.id, None)
    bot.reply_to(msg, "Chat udah direset. Kita mulai dari 0 lagi.")

@bot.message_handler(content_types=['document', 'text'])
def handle_message(msg):
    chat_id = msg.chat.id
    now = time.time()

    # Cek cooldown
    if chat_id in cooldown:
        sisa = COOLDOWN_TIME - (now - cooldown[chat_id])
        if sisa > 0:
            bot.reply_to(msg, f"⏳ Tunggu {int(sisa)} detik lagi ya. Biar kuota bot nggak habis.")
            return

    cooldown[chat_id] = now

    # Ambil history
    if chat_id not in user_histories:
        user_histories[chat_id] = []
    history = user_histories[chat_id]

    # Baca file kalau ada
    file_content = ""
    if msg.document:
        file_info = bot.get_file(msg.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            file_content = "\n\nISI FILE USER:\n" + downloaded_file.decode("utf-8")
        except:
            file_content = "\n\nFile terkirim tapi bukan teks, jadi nggak bisa dibaca langsung."

    user_text = msg.text if msg.text else "User kirim file"
    full_message = user_text + file_content

    # Susun pesan ke Groq
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": full_message})

    bot.send_chat_action(chat_id, "typing")
    try:
        reply = chat_with_groq(messages)

        history.append({"role": "user", "content": full_message})
        history.append({"role": "assistant", "content": reply})

        if len(history) > 20:
            history = history[-20:]
        user_histories[chat_id] = history

        bot.reply_to(msg, reply)
    except Exception as e:
        bot.reply_to(msg, f"Error: {e}")

print("Bot jalan...")
bot.polling()
