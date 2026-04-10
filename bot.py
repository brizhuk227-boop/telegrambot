import logging
import sqlite3
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- База данных ---
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER,
    balance INTEGER DEFAULT 0
)
""")
conn.commit()


# --- Старт ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    # Проверка есть ли пользователь
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        referrer_id = None

        if args.startswith("ref"):
            try:
                referrer_id = int(args.replace("ref", ""))
            except:
                referrer_id = None

        cursor.execute(
            "INSERT INTO users (user_id, referrer_id) VALUES (?, ?)",
            (user_id, referrer_id)
        )
        conn.commit()

        # Начисление бонуса рефереру
        if referrer_id and referrer_id != user_id:
            cursor.execute(
                "UPDATE users SET balance = balance + 1 WHERE user_id=?",
                (referrer_id,)
            )
            conn.commit()

            try:
                await bot.send_message(
                    referrer_id,
                    "🎉 У тебя новый реферал! +1€"
                )
            except:
                pass

    await message.answer(
        "Добро пожаловать!\n\n"
        "🔗 Получи свою реферальную ссылку: /ref\n"
        "💰 Баланс: /balance"
    )


# --- Реферальная ссылка ---
@dp.message_handler(commands=['ref'])
async def get_ref(message: types.Message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/Incloudrefbot?start=ref{user_id}"

    await message.answer(
        f"🔗 Твоя реферальная ссылка:\n{ref_link}\n\n"
        "Приглашай друзей и получай бонусы 💰"
    )


# --- Баланс ---
@dp.message_handler(commands=['balance'])
async def balance(message: types.Message):
    user_id = message.from_user.id

    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    )
    result = cursor.fetchone()

    bal = result[0] if result else 0

    await message.answer(f"💰 Твой баланс: {bal}€")


# --- Список рефералов ---
@dp.message_handler(commands=['refs'])
async def refs(message: types.Message):
    user_id = message.from_user.id

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE referrer_id=?",
        (user_id,)
    )
    count = cursor.fetchone()[0]

    await message.answer(f"👥 Ты пригласил: {count} человек")


# --- Запуск ---
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
