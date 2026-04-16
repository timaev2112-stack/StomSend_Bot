import telebot
from telebot import types
import sqlite3

# 🔥 ANTI-SLEEP
from flask import Flask
import threading

token = "8581481992:AAFg_5N4KnUyWwp-p4KX9fiR5AoUtPabcHY"
bot = telebot.TeleBot(token)

ADMINS = [7625739284, 94243852]

# =========================
# 💾 DATABASE
# =========================
conn = sqlite3.connect("shop.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item TEXT,
    price INTEGER
)
""")

conn.commit()

# =========================
# 📦 СКЛАД
# =========================
accounts = []

# =========================
# 🔥 ANTI-SLEEP SERVER
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "bot is alive"

def run():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run).start()

# =========================
# HELPERS
# =========================
def get_user(user_id):
    cur.execute("SELECT user_id, balance, invited_by FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()

    if not row:
        cur.execute(
            "INSERT INTO users (user_id, balance, invited_by) VALUES (?, ?, ?)",
            (user_id, 0, None)
        )
        conn.commit()
        return {"balance": 0, "invited_by": None}

    return {"balance": row[1], "invited_by": row[2]}

def update_balance(user_id, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

# =========================
# START
# =========================
@bot.message_handler(commands=['start'])
def start(msg):

    user_id = msg.from_user.id
    get_user(user_id)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📦 Каталог")
    kb.add("🆘 Поддержка", "👥 Реферал")
    kb.add("👤 Профиль")

    bot.send_message(
        user_id,
        "✨ Добро пожаловать!\n\n"
        "🛍 Каталог доступен\n"
        "⚡ Быстрая выдача\n"
        "💰 Баланс и рефералы\n\n"
        "👇 Выбери действие",
        reply_markup=kb
    )

# =========================
# 📦 КАТАЛОГ
# =========================
def show_catalog(chat_id):

    if len(accounts) == 0:
        bot.send_message(chat_id, "❌ Склад пуст")
        return

    text = "📦 <b>Каталог:</b>\n\n"

    for i, acc in enumerate(accounts):
        text += f"{i+1}. {acc['item']} | 💰 {acc['price']}₽\n"

    kb = types.InlineKeyboardMarkup()

    for i in range(len(accounts)):
        kb.add(
            types.InlineKeyboardButton(
                text=f"Купить #{i+1}",
                callback_data=f"buy_{i}"
            )
        )

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

# =========================
# TEXT HANDLER
# =========================
@bot.message_handler(content_types=['text'])
def text(msg):

    user_id = msg.from_user.id
    user = get_user(user_id)

    if msg.text == "📦 Каталог":
        show_catalog(user_id)

    elif msg.text == "👤 Профиль":

        cur.execute("SELECT COUNT(*) FROM purchases WHERE user_id=?", (user_id,))
        count = cur.fetchone()[0]

        bot.send_message(
            user_id,
            f"👤 Профиль\n\n🆔 {user_id}\n🛒 Покупок: {count}\n💳 Баланс: {user['balance']}"
        )

    elif msg.text == "👥 Реферал":
        bot.send_message(user_id, "👥 Реферальная система работает")

    elif msg.text == "🆘 Поддержка":
        bot.send_message(user_id, "💬 Поддержка")

# =========================
# CALLBACKS
# =========================
@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    user_id = call.from_user.id
    data = call.data

    if data.startswith("buy_"):

        index = int(data.split("_")[1])

        if index >= len(accounts):
            bot.answer_callback_query(call.id, "❌ Ошибка")
            return

        item = accounts.pop(index)

        bot.answer_callback_query(call.id, "✅ Куплено")
        bot.send_message(user_id, f"🎁 {item['item']}")

    elif data == "topup":
        bot.send_message(user_id, "💰 Пополнение скоро")

    elif data == "mybuy":
        bot.send_message(user_id, "📦 История покупок")

print("bot running...")
bot.infinity_polling()