import telebot
from telebot import types
import sqlite3

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
# 🧠 STATES
# =========================
admin_add = {}
admin_delete = {}
admin_edit = {}

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

    bot.send_message(user_id, "✨ Добро пожаловать", reply_markup=kb)

# =========================
# 📦 КАТАЛОГ
# =========================
def show_catalog(chat_id):

    if len(accounts) == 0:
        bot.send_message(chat_id, "❌ Склад пуст")
        return

    text = "📦 <b>Каталог:</b>\n\n"

    for i, acc in enumerate(accounts):
        text += f"{i+1}. {acc['item']}\n📝 {acc['desc']}\n💰 {acc['price']}₽\n\n"

    kb = types.InlineKeyboardMarkup()

    for i in range(len(accounts)):
        kb.add(types.InlineKeyboardButton(f"Купить #{i+1}", callback_data=f"buy_{i}"))

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
        bot.send_message(user_id, "👥 Реферал работает")

    elif msg.text == "🆘 Поддержка":
        bot.send_message(user_id, "💬 Поддержка")

    elif msg.text == "/admin":

        if user_id not in ADMINS:
            bot.send_message(user_id, "❌ Нет доступа")
            return

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("➕ Добавить", "➖ Удалить")
        kb.row("✏️ Редактировать", "📦 Склад")
        kb.row("🔙 Выход")

        bot.send_message(user_id, "👮 Админ панель", reply_markup=kb)

    elif msg.text == "➕ Добавить" and user_id in ADMINS:
        admin_add[user_id] = {"step": 1}
        bot.send_message(user_id, "Введи название товара")

    elif user_id in admin_add:

        state = admin_add[user_id]

        if state["step"] == 1:
            state["item"] = msg.text
            state["step"] = 2
            bot.send_message(user_id, "Введи описание товара")
            return

        if state["step"] == 2:
            state["desc"] = msg.text
            state["step"] = 3
            bot.send_message(user_id, "Введи цену")
            return

        if state["step"] == 3:

            if not msg.text.isdigit():
                bot.send_message(user_id, "❌ Введи число")
                return

            accounts.append({
                "item": state["item"],
                "desc": state["desc"],
                "price": int(msg.text)
            })

            admin_add.pop(user_id)
            bot.send_message(user_id, "✅ Добавлено")

    elif msg.text == "➖ Удалить" and user_id in ADMINS:
        admin_delete[user_id] = True
        bot.send_message(user_id, "Введи номер товара")

    elif user_id in admin_delete:

        try:
            index = int(msg.text) - 1
            accounts.pop(index)
            admin_delete.pop(user_id)
            bot.send_message(user_id, "🗑 Удалено")
        except:
            bot.send_message(user_id, "❌ Ошибка")

    elif msg.text == "✏️ Редактировать" and user_id in ADMINS:
        admin_edit[user_id] = {"step": 1}
        bot.send_message(user_id, "Введи номер товара")

    elif user_id in admin_edit:

        state = admin_edit[user_id]

        if state["step"] == 1:

            index = int(msg.text) - 1

            if index < 0 or index >= len(accounts):
                bot.send_message(user_id, "❌ Нет товара")
                admin_edit.pop(user_id)
                return

            state["index"] = index
            state["step"] = 2
            bot.send_message(user_id, "Введи новое название")
            return

        if state["step"] == 2:
            state["item"] = msg.text
            state["step"] = 3
            bot.send_message(user_id, "Введи новое описание")
            return

        if state["step"] == 3:
            state["desc"] = msg.text
            state["step"] = 4
            bot.send_message(user_id, "Введи новую цену")
            return

        if state["step"] == 4:

            if not msg.text.isdigit():
                bot.send_message(user_id, "❌ Введи число")
                return

            accounts[state["index"]] = {
                "item": state["item"],
                "desc": state["desc"],
                "price": int(msg.text)
            }

            admin_edit.pop(user_id)
            bot.send_message(user_id, "✅ Обновлено")

    elif msg.text == "📦 Склад" and user_id in ADMINS:

        text = "📦 Склад:\n\n"
        for i, a in enumerate(accounts):
            text += f"{i+1}. {a['item']} | {a['price']}₽\n"

        bot.send_message(user_id, text)

    elif msg.text == "🔙 Выход":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📦 Каталог", "👤 Профиль")
        bot.send_message(user_id, "Главное меню", reply_markup=kb)

    else:
        bot.send_message(user_id, "Используй кнопки 👇")

# =========================
# CALLBACK
# =========================
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def buy(call):

    user_id = call.from_user.id
    index = int(call.data.split("_")[1])

    item = accounts[index]

    bot.answer_callback_query(call.id, "Куплено")
    bot.send_message(user_id, f"🎁 {item['item']}\n📝 {item['desc']}\n💰 {item['price']}₽")

print("bot running...")
bot.infinity_polling()