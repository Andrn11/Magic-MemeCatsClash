from aiogram import Dispatcher, types
from aiogram.types import ParseMode
import logging
from CheckName import check_name



logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
if not cursor.fetchone():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            rarity TEXT,
            username TEXT,
            points INTEGER DEFAULT 0,
            highest_rarity TEXT,
            cat_coins INTEGER DEFAULT 0,
            last_cat_time INTEGER DEFAULT 0,
            last_bonus_time INTEGER DEFAULT 0,
            last_put_time INTEGER DEFAULT 0,
            has_scratcher INTEGER DEFAULT 0,
            has_companion INTEGER DEFAULT 0,
            booster_end_time INTEGER DEFAULT 0,
            has_time_watch INTEGER DEFAULT 0,
            magic_coins INTEGER DEFAULT 0,
            has_magic_medallion INTEGER DEFAULT 0,
            has_magic_luck_scroll INTEGER DEFAULT 0,
            last_magic_time INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    logging.info("Таблица users создана в ledersboard.py.")
else:
    logging.info("Таблица users уже существует в ledersboard.py.")
cursor.execute("SELECT user_id, username, cat_coins, magic_coins, points FROM users;")
result = cursor.fetchall()
print(result)

async def show_leaderboard(message: types.Message, leaderboard_type: str):
    if leaderboard_type == "points":
        column = "points"
        title = "🏆 Лидерборд по очкам 🏆"
    elif leaderboard_type == "cat_coins":
        column = "cat_coins"
        title = "🐱 Лидерборд по котокоинам 🐱"
    elif leaderboard_type == "magic_coins":
        column = "magic_coins"
        title = "🔮 Лидерборд по магическим коинам 🔮"
    else:
        await message.answer("Неверный тип лидерборда.")
        return


    cursor.execute(f"""
        SELECT user_id, {column} 
        FROM users 
        WHERE ({column} IS NOT NULL AND {column} > 0) OR {column} = 0
        ORDER BY {column} DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()


    logging.info(f"Запрошен лидерборд типа: {leaderboard_type}")
    logging.info(f"Результат запроса: {leaderboard}")

    if not leaderboard:
        await message.answer("Лидерборд пуст.")
        return

    leaderboard_text = f"{title}\n\n"
    for index, (user_id, value) in enumerate(leaderboard, start=1):

        cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        db_username = user_data[0] if user_data else None


        try:
            user = await message.bot.get_chat(user_id)
            tg_username = user.username
            tg_first_name = user.first_name
        except Exception as e:

            tg_username = None
            tg_first_name = None


        if db_username:
            display_name = db_username
        elif tg_username:
            display_name = f"@{tg_username}"
        elif tg_first_name:
            display_name = tg_first_name
        else:
            display_name = f"Пользователь {user_id}"

        leaderboard_text += f"{index}. {display_name}: {value}\n"


    keyboard = types.InlineKeyboardMarkup(row_width=2)

    if leaderboard_type != "points":
        keyboard.add(types.InlineKeyboardButton("🏆 По очкам", callback_data="leaderboard_points"))
    if leaderboard_type != "cat_coins":
        keyboard.add(types.InlineKeyboardButton("🐱 По котокоинам", callback_data="leaderboard_cat_coins"))
    if leaderboard_type != "magic_coins":
        keyboard.add(types.InlineKeyboardButton("🔮 По магическим коинам", callback_data="leaderboard_magic_coins"))


    if message.from_user.id == message.chat.id:
        await message.edit_text(leaderboard_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(leaderboard_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

async def leders_command(message: types.Message):
    if not await check_name(message):
        return
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🏆 По очкам", callback_data="leaderboard_points"),
        types.InlineKeyboardButton("🐱 По котокоинам", callback_data="leaderboard_cat_coins"),
        types.InlineKeyboardButton("🔮 По магическим коинам", callback_data="leaderboard_magic_coins"),
    )

    await message.answer(
        "Выберите тип лидерборда:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN,
    )

async def leaderboard_callback(callback: types.CallbackQuery):
    await callback.message.delete()
    leaderboard_type = callback.data.replace("leaderboard_", "")
    await callback.answer()
    await show_leaderboard(callback.message, leaderboard_type)

def register_leaderboard_handlers(dp: Dispatcher):
    dp.register_message_handler(leders_command, commands=["leaders"])
    dp.register_callback_query_handler(leaderboard_callback, lambda c: c.data.startswith("leaderboard_"))