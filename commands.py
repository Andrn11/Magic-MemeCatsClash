import logging
from aiogram import Dispatcher, types
import random
import time
import sqlite3
import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from advanced_logger import log_operation_async
from data import cats, rarity_weights
from lecsicon import cat_synonyms
from aiogram.types import ParseMode
from Magicsends import jujitsu_command
from quests import update_quest_progress, load_user_progress
from shop import shop_command
from ledersboard import leders_command
from ValutionTrade import exchange_command
from CheckName import check_name
from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

def add_wishing_fountain_column():
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        if "has_wishing_fountain" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE users ADD COLUMN has_wishing_fountain INTEGER DEFAULT 0")
            conn.commit()
            logging.info("Столбец has_wishing_fountain добавлен в таблицу users.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении столбца has_wishing_fountain: {e}")

def create_magic_cards_table():
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS magic_cards (
                user_id INTEGER,
                card_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (card_id) REFERENCES magic(id),
                PRIMARY KEY (user_id, card_id)
            );
        ''')
        conn.commit()
        logging.info("Таблица magic_cards создана или уже существует.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при создании таблицы magic_cards: {e}")



def add_nyan_mp3_column():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN has_nyan_mp3 INTEGER DEFAULT 0")
        conn.commit()
        logging.info("Столбец has_nyan_mp3 добавлен в таблицу users.")
    except sqlite3.OperationalError as e:
        logging.warning(f"Столбец has_nyan_mp3 уже существует: {e}")

add_nyan_mp3_column()


async def nyan_mp3_command(message: types.Message):
    user_id = message.from_user.id

    # Логирование для отладки
    logging.info(f"Пользователь {user_id} использует команду /nyan.mp3")

    # Проверяем, существует ли пользователь в таблице
    cursor.execute("SELECT user_id, has_nyan_mp3, note_coins FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        # Если пользователя нет в базе, добавляем его
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, magic_coins, has_nyan_mp3, note_coins) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0, 0),
        )
        conn.commit()
        logging.info(f"Пользователь {user_id} добавлен в таблицу users.")
        has_nyan_mp3 = 0
        note_coins = 0
    else:
        user_id, has_nyan_mp3, note_coins = user_data

    # Проверяем, использовал ли пользователь команду ранее
    if has_nyan_mp3:
        await message.answer("Ты уже использовал эту команду! Она одноразовая. 😉")
        return

    # Выдаём 5000 нотокоинов
    cursor.execute(
        "UPDATE users SET note_coins = note_coins + 5000, has_nyan_mp3 = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()

    # Логирование для отладки
    logging.info(f"Пользователь {user_id} получил 5000 нотокоинов. Текущий баланс: {note_coins + 5000}")

    await message.answer(
        "Ты нашёл секретную команду! 🎉\n\n"
        "Ты получил 5000 нотокоинов! Используй их с умом.\n\n"
        "Эта команда одноразовая, так что больше ты её не сможешь использовать. 😉"
    )



async def initndr_command(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT user_id, has_initndr FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, magic_coins, has_initndr) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0),
        )
        conn.commit()
        has_initndr = 0
    else:
        user_id, has_initndr = user_data

    if has_initndr:
        await message.answer("Ты уже использовал эту команду! Она одноразовая. 😉")
        return

    cursor.execute(
        "UPDATE users SET magic_coins = magic_coins + 5000, has_initndr = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()

    await message.answer(
        "Ты нашёл секретную команду! 🎉\n\n"
        "Ты получил 5000 магических коинов! Используй их с умом.\n\n"
        "Эта команда одноразовая, так что больше ты её не сможешь использовать. 😉"
    )

async def MrLololoshka_command(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT user_id, has_MrLololoshka FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, magic_coins, has_MrLololoshka) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0),
        )
        conn.commit()
        has_MrLololoshka = 0
    else:
        user_id, has_MrLololoshka = user_data

    if has_MrLololoshka:
        await message.answer("Ты уже использовал эту команду! Она одноразовая. 😉")
        return

    cursor.execute(
        "UPDATE users SET points = points + 40000, has_MrLololoshka = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()

    await message.answer(
        "Ты нашёл секретную команду! 🎉\n\n"
        "Ты получил 40000 очков! Используй их с умом.\n\n"
        "Эта команда одноразовая, так что больше ты её не сможешь использовать. 😉"
    )

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

async def on_bot_added_to_group(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member' and event.new_chat_member.user.id == event.bot.id:
        await event.bot.send_message(
            event.chat.id,
            "Привет! Я новый карточный бот в вашей группе, напишите 'кот' и получите коллекционную карточку мемного кота! Используйте /bonus для получения бонуса. Напишите Магическая битва и получите магическую карточку."
        )

try:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
except sqlite3.Error as e:
    logging.error(f"Ошибка подключения к базе данных: {e}")
    raise

def check_and_add_magic_scroll_column():
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        if "has_magic_scroll" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE users ADD COLUMN has_magic_scroll INTEGER DEFAULT 0")
            conn.commit()
            logging.info("Столбец has_magic_scroll добавлен в таблицу users.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке/добавлении столбца has_magic_scroll: {e}")



check_and_add_magic_scroll_column()

def create_user_cards_table():
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_cards (
                user_id INTEGER,
                card_id TEXT,
                username,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (card_id) REFERENCES cards(cat_id),
                PRIMARY KEY (user_id, card_id)
            );
        ''')
        conn.commit()
        logging.info("Таблица user_cards создана или уже существует.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при создании таблицы user_cards: {e}")

create_user_cards_table()

def add_initndr_column():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN has_initndr INTEGER DEFAULT 0")
        conn.commit()
        logging.info("Столбец has_initndr добавлен в таблицу users.")
    except sqlite3.OperationalError as e:
        logging.warning(f"Столбец has_initndr уже существует: {e}")

add_initndr_column()

def add_HiTmaN_VadIM_column():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN has_HiTmaN_VadIM INTEGER DEFAULT 0")
        conn.commit()
        logging.info("Столбец HiTmaN_VadIM добавлен в таблицу users.")
    except sqlite3.OperationalError as e:
        logging.warning(f"Столбец HiTmaN_VadIM уже существует: {e}")

add_HiTmaN_VadIM_column()

def add_MrLololoshka_column():
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN has_MrLololoshka INTEGER DEFAULT 0")
        conn.commit()
        logging.info("Столбец has_MrLololoshka добавлен в таблицу users.")
    except sqlite3.OperationalError as e:
        logging.warning(f"Столбец has_MrLololoshka уже существует: {e}")

add_MrLololoshka_column()

async def HiTmaN_VadIM_command(message: types.Message):
    user_id = message.from_user.id

    cursor.execute("SELECT user_id, has_HiTmaN_VadIM FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, magic_coins, has_HiTmaN_VadIM) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0),
        )
        conn.commit()
        has_HiTmaN_VadIM = 0
    else:
        user_id, has_HiTmaN_VadIM = user_data

    if has_HiTmaN_VadIM:
        await message.answer("Ты уже использовал эту команду! Она одноразовая. 😉")
        return

    cursor.execute(
        "UPDATE users SET cat_coins = cat_coins + 5000, has_HiTmaN_VadIM = 1 WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()

    await message.answer(
        "Ты нашёл секретную команду! 🎉\n\n"
        "Ты получил 5000 Котокоинов! Используй их с умом.\n\n"
        "Эта команда одноразовая, так что больше ты её не сможешь использовать. 😉"
    )

try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            rarity TEXT,
            username TEXT,
            points INTEGER DEFAULT 0,
            highest_rarity TEXT DEFAULT 'обычный',
            cat_coins INTEGER DEFAULT 0,
            last_cat_time INTEGER DEFAULT 0,
            last_bonus_time INTEGER DEFAULT 0,
            last_put_time INTEGER DEFAULT 0,
            has_scratcher INTEGER DEFAULT 0,
            has_companion INTEGER DEFAULT 0,
            booster_end_time INTEGER DEFAULT 0,
            has_time_watch INTEGER DEFAULT 0,
            magic_coins INTEGER DEFAULT 0,
            medallion_end_time INTEGER DEFAULT 0,
            has_magic_luck_scroll INTEGER DEFAULT 0,
            last_magic_time INTEGER DEFAULT 0,
            has_wishing_fountain INTEGER DEFAULT 0
            );
        ''')
        conn.commit()
        logging.info("Таблица users создана в ledersboard.py.")
    else:
        logging.info("Таблица users уже существует в ledersboard.py.")
except:
    cursor.execute("SELECT user_id, username, cat_coins, magic_coins, points FROM users;")
    result = cursor.fetchall()
    print(result)

def check_and_create_tables():
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username,
                    user_id INTEGER,
                    cat_id TEXT,
                    cat_image TEXT,
                    rarity TEXT,
                    points INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, cat_id)
                );
            ''')
            conn.commit()
            print("Таблица cards создана.")
        else:
            print("Таблица cards уже существует.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке/создании таблицы cards: {e}")

check_and_create_tables()

rarities = [
    "обычный",
    "редкий",
    "сверхредкий",
    "эпический",
    "мифический",
    "легендарный",
    "хромотический",
    "особый"
]

cooldown_cat = config['cooldowns']['cat']
cooldown_bonus = config['cooldowns']['bonus']
cooldown_put = config['cooldowns']['put']

cooldowns = {}
bonus_cooldowns = {}

def get_random_cat(cats, has_magic_luck_scroll=False):
    weighted_cats = []
    for cat in cats:
        if has_magic_luck_scroll:
            if cat["rarity"] in ["сверхредкий", "эпический", "мифический", "легендарный", "хромотический", "особый"]:
                weight = rarity_weights.get(cat["rarity"], 1)
                weighted_cats.extend([cat] * weight)
        else:
            weight = rarity_weights.get(cat["rarity"], 1)
            weighted_cats.extend([cat] * weight)
    return random.choice(weighted_cats)

def get_user_points(user_id):
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_user_cat_coins(user_id):
    cursor.execute("SELECT cat_coins FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_user_magic_coins(user_id):
    cursor.execute("SELECT magic_coins FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

async def help_command(message: types.Message):
    if not await check_name(message):
        return
    await message.answer(
        "✨ Список команд: ✨\n\n"
        "———————————————————————————-\n"
        "👋 /start - Начать работу с ботом\n"
        "———————————————————————————-\n"
        "🐱 кот - Получить случайную карточку кота (кулдаун: 3 часа, писать в чат)\n"
        "———————————————————————————-\n"
        "🎁 /bonus - Получить бонусную карточку кота (кулдаун: 6 часов)\n"
        "———————————————————————————-\n"
        "🛒 /shop - Магазин \n"
        "———————————————————————————-\n"
        "👤 /profile - Ваш профиль\n"
        "———————————————————————————-\n"
        "🤗 /put - Погладить котика и получить 1000 очков и 500 котокоинов (требуется Чесалка, кулдаун: 2 часа)\n"
        "———————————————————————————-\n"
        "📚 /collection - Просмотреть вашу коллекцию карточек\n"
        "———————————————————————————-\n"
        "🐾 /cat - Получить случайную карточку кота (кулдаун: 3 часа)\n"
        "———————————————————————————-\n"
        "⚔️ Битва - Получить магическую карту (Писать в чат)\n"
        "———————————————————————————-\n"
        "🪄 /jujitsu - Получить магическую карту\n"
        "———————————————————————————-\n"
        "👤 /avatar - Установка аватара\n"
        "———————————————————————————-\n"
        "🎵 /melody - Игра угадай мем\n"
        "———————————————————————————-\n"
        "🎁 /daily - ежедневные награды\n"
        "———————————————————————————-\n"
        "🎁 /daily_strike - Ваш страйк по ежедневным наградам\n"
        "———————————————————————————-\n"
        "🏆 /leders - Просмотреть лидерборд\n"
        "———————————————————————————-\n"
        "🔄 /exchange - Обмен валют\n"
        "———————————————————————————-\n"
        "🖋 /name и /rename - Выбор и изменение никнейма\n"
        "———————————————————————————-\n"
        "https://t.me/MagicAndMemeCatsClash - Наш канал бота\n"
    )

async def cat_command(message: types.Message):
    if message.text.lower() not in ["кот"] + cat_synonyms:
        return
    if not await check_name(message):
        return
    user_id = message.from_user.id
    current_time = time.time()

    cursor.execute(
        "SELECT has_time_watch, has_magic_luck_scroll, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3 FROM users WHERE user_id = ?",
        (user_id,)
    )
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0, 0),
        )
        conn.commit()
        has_time_watch = 0
        has_magic_luck_scroll = 0
        has_initndr = 0
        has_HiTmaN_VadIM = 0
        has_MrLololoshka = 0
        has_nyan_mp3 = 0
    else:
        has_time_watch, has_magic_luck_scroll, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3 = user_data

    if has_time_watch:
        cooldowns[user_id] = 0
        cursor.execute("UPDATE users SET has_time_watch = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    if user_id in cooldowns:
        remaining_time = config['cooldowns']['cat'] - (current_time - cooldowns[user_id])
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await message.answer(
                f"Вы осмотрелись, но не нашли кота на диване. Попробуйте через {hours} часов {minutes} минут."
            )
            return

    cooldowns[user_id] = current_time

    if random.random() < 0.1 and not has_initndr:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /init... 😉"
        )
        return

    if random.random() < 0.1 and not has_nyan_mp3:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /nyan... 😉"
        )
        return

    if random.random() < 0.1 and not has_HiTmaN_VadIM:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /HiTmaN_... 😉"
        )
        return

    if random.random() < 0.1 and not has_MrLololoshka:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /MrLolo... 😉"
        )
        return

    cursor.execute("SELECT booster_end_time FROM users WHERE user_id = ?", (user_id,))
    booster_end_time = cursor.fetchone()[0]
    is_booster_active = booster_end_time and booster_end_time > current_time

    if is_booster_active:
        points_multiplier = 1.5
        coins_multiplier = 1.5
    else:
        points_multiplier = 1.0
        coins_multiplier = 1.0

    cursor.execute("SELECT has_companion FROM users WHERE user_id = ?", (user_id,))
    has_companion = cursor.fetchone()[0]

    if has_companion:
        num_cards = 2
        cursor.execute("UPDATE users SET has_companion = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
    else:
        num_cards = 1

    for _ in range(num_cards):
        cat = get_random_cat(cats, has_magic_luck_scroll)

        cat["points"] = int(cat["points"] * points_multiplier)
        cat["cat_coins"] = int(cat["cat_coins"] * coins_multiplier)

        rarities_str = ", ".join(rarities)

        try:
            rarities_str = "обычный,редкий,сверхредкий,эпический,мифический,легендарный,хромотический,особый"
            cursor.execute(
                f"""
                INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    rarity = excluded.rarity, 
                    points = points + excluded.points, 
                    highest_rarity = CASE 
                        WHEN highest_rarity IS NULL THEN excluded.rarity
                        WHEN INSTR('{rarities_str}', excluded.rarity) > INSTR('{rarities_str}', highest_rarity) THEN excluded.rarity 
                        ELSE highest_rarity 
                    END,
                    cat_coins = cat_coins + excluded.cat_coins
                """,
                (
                    user_id,
                    cat["rarity"],
                    cat["points"],
                    cat["rarity"],
                    cat["cat_coins"],
                ),
            )
            conn.commit()

            cursor.execute(
                "SELECT id FROM cards WHERE user_id = ? AND cat_id = ?",
                (user_id, cat["id"]),
            )
            existing_card = cursor.fetchone()

            if existing_card:
                cursor.execute(
                    "DELETE FROM cards WHERE user_id = ? AND cat_id = ?",
                    (user_id, cat["id"]),
                )
                conn.commit()

            cursor.execute(
                "INSERT INTO cards (user_id, cat_id, cat_image, rarity, points) VALUES (?, ?, ?, ?, ?)",
                (user_id, cat["id"], cat["photo"], cat["rarity"], cat["points"]),
            )
            conn.commit()

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

            message_text = (
                f"👤 {display_name}, успех! Вы нашли карточку. \n"
                f"🌟 Карточка «{cat['catname']}» 🐱\n"
                "--------------------------\n"
                f"💎 Редкость: {cat['rarity']}\n"
                f"✨ Очки: +{cat['points']} (Всего: {get_user_points(user_id)})\n"
                f"🐱 Котокоины: +{cat['cat_coins']} (Всего: {get_user_cat_coins(user_id)})\n"
                f"🧧 Описание: {cat['catinfo']}\n"
            )

            if is_booster_active:
                message_text += "🚀 Активен Кот-бустер: +50% очков и котокоинов!\n"

            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🔄 Получить еще карточку", callback_data="get_another_card"),
                InlineKeyboardButton("📚 Просмотреть коллекцию", callback_data="view_collection")
            )

            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=cat["photo"],
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id,
                reply_markup=keyboard,
            )


            user_progress = await load_user_progress(user_id)
            if user_progress and not user_progress["completed"]:
                if user_progress["category"] == "cat":

                    await update_quest_progress(user_id, "cat")


                    if cat["rarity"] in ["редкий", "сверхредкий", "эпический", "мифический", "легендарный",
                                         "хромотический"]:
                        await update_quest_progress(user_id, "cat_rare")


        except sqlite3.Error as e:
            logging.error(f"Ошибка базы данных: {e}")
            await message.answer("Произошла ошибка.")


    if has_magic_luck_scroll:
        cursor.execute("UPDATE users SET has_magic_luck_scroll = 0 WHERE user_id = ?", (user_id,))
        conn.commit()



async def send_cat(message: types.Message):
    if message.text.lower() not in ["кот"] + cat_synonyms:
        return
    if not await check_name(message):
        return
    user_id = message.from_user.id
    current_time = time.time()

    cursor.execute(
        "SELECT has_time_watch, has_magic_luck_scroll, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3 FROM users WHERE user_id = ?",
        (user_id,)
    )
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0, 0, 0),
        )
        conn.commit()
        has_time_watch = 0
        has_magic_luck_scroll = 0
        has_initndr = 0
        has_HiTmaN_VadIM = 0
        has_MrLololoshka = 0
        has_nyan_mp3 = 0
    else:
        has_time_watch, has_magic_luck_scroll, has_initndr, has_HiTmaN_VadIM, has_MrLololoshka, has_nyan_mp3 = user_data

    if has_time_watch:
        cooldowns[user_id] = 0
        cursor.execute("UPDATE users SET has_time_watch = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    if user_id in cooldowns:
        remaining_time = config['cooldowns']['cat'] - (current_time - cooldowns[user_id])
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await message.answer(
                f"Вы осмотрелись, но не нашли кота на диване. Попробуйте через {hours} часов {minutes} минут."
            )
            return

    cooldowns[user_id] = current_time

    if random.random() < 0.1 and not has_initndr:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /init... 😉"
        )
        return

    if random.random() < 0.1 and not has_nyan_mp3:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /nyan... 😉"
        )
        return

    if random.random() < 0.1 and not has_HiTmaN_VadIM:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /HiTmaN_... 😉"
        )
        return

    if random.random() < 0.1 and not has_MrLololoshka:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда начинается с /MrLolo... 😉"
        )
        return

    cursor.execute("SELECT booster_end_time FROM users WHERE user_id = ?", (user_id,))
    booster_end_time = cursor.fetchone()[0]
    is_booster_active = booster_end_time and booster_end_time > current_time

    if is_booster_active:
        points_multiplier = 1.5
        coins_multiplier = 1.5
    else:
        points_multiplier = 1.0
        coins_multiplier = 1.0

    cursor.execute("SELECT has_companion FROM users WHERE user_id = ?", (user_id,))
    has_companion = cursor.fetchone()[0]

    if has_companion:
        num_cards = 2
        cursor.execute("UPDATE users SET has_companion = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
    else:
        num_cards = 1

    for _ in range(num_cards):
        cat = get_random_cat(cats, has_magic_luck_scroll)

        cat["points"] = int(cat["points"] * points_multiplier)
        cat["cat_coins"] = int(cat["cat_coins"] * coins_multiplier)

        rarities_str = ", ".join(rarities)

        try:
            rarities_str = "обычный,редкий,сверхредкий,эпический,мифический,легендарный,хромотический,особый"
            cursor.execute(
                f"""
                INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    rarity = excluded.rarity, 
                    points = points + excluded.points, 
                    highest_rarity = CASE 
                        WHEN highest_rarity IS NULL THEN excluded.rarity
                        WHEN INSTR('{rarities_str}', excluded.rarity) > INSTR('{rarities_str}', highest_rarity) THEN excluded.rarity 
                        ELSE highest_rarity 
                    END,
                    cat_coins = cat_coins + excluded.cat_coins
                """,
                (
                    user_id,
                    cat["rarity"],
                    cat["points"],
                    cat["rarity"],
                    cat["cat_coins"],
                ),
            )
            conn.commit()

            cursor.execute(
                "SELECT id FROM cards WHERE user_id = ? AND cat_id = ?",
                (user_id, cat["id"]),
            )
            existing_card = cursor.fetchone()

            if existing_card:
                cursor.execute(
                    "DELETE FROM cards WHERE user_id = ? AND cat_id = ?",
                    (user_id, cat["id"]),
                )
                conn.commit()

            cursor.execute(
                "INSERT INTO cards (user_id, cat_id, cat_image, rarity, points) VALUES (?, ?, ?, ?, ?)",
                (user_id, cat["id"], cat["photo"], cat["rarity"], cat["points"]),
            )
            conn.commit()

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

            message_text = (
                f"👤 {display_name}, успех! Вы нашли карточку. \n"
                f"🌟 Карточка «{cat['catname']}» 🐱\n"
                "--------------------------\n"
                f"💎 Редкость: {cat['rarity']}\n"
                f"✨ Очки: +{cat['points']} (Всего: {get_user_points(user_id)})\n"
                f"🐱 Котокоины: +{cat['cat_coins']} (Всего: {get_user_cat_coins(user_id)})\n"
                f"🧧 Описание: {cat['catinfo']}\n"
            )

            if is_booster_active:
                message_text += "🚀 Активен Кот-бустер: +50% очков и котокоинов!\n"

            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                InlineKeyboardButton("🔄 Получить еще карточку", callback_data="get_another_card"),
                InlineKeyboardButton("📚 Просмотреть коллекцию", callback_data="view_collection")
            )

            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=cat["photo"],
                caption=message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id,
                reply_markup=keyboard,
            )


            user_progress = await load_user_progress(user_id)
            if user_progress and not user_progress["completed"]:
                if user_progress["category"] == "cat":

                    await update_quest_progress(user_id, "cat")


                    if cat["rarity"] in ["редкий", "сверхредкий", "эпический", "мифический", "легендарный",
                                         "хромотический"]:
                        await update_quest_progress(user_id, "cat_rare")


        except sqlite3.Error as e:
            logging.error(f"Ошибка базы данных: {e}")
            await message.answer("Произошла ошибка.")


    if has_magic_luck_scroll:
        cursor.execute("UPDATE users SET has_magic_luck_scroll = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
async def bonus_command(message: types.Message):
    logging.info("Команда /bonus вызвана")
    if not await check_name(message):
        logging.warning("Проверка имени не пройдена")
        return

    user_id = message.from_user.id
    current_time = time.time()

    if user_id in bonus_cooldowns:
        remaining_time = 21600 - (current_time - bonus_cooldowns[user_id])
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await message.answer(
                f"Вы осмотрелись, но не нашли бонус на полке. Попробуйте через {hours} часов {minutes} минут."
            )
            return

    bonus_cooldowns[user_id] = current_time

    cursor.execute("SELECT has_initndr FROM users WHERE user_id = ?", (user_id,))
    has_initndr = cursor.fetchone()[0]

    cursor.execute("SELECT has_HiTmaN_VadIM FROM users WHERE user_id = ?", (user_id,))
    has_HiTmaN_VadIM = cursor.fetchone()[0]

    cursor.execute("SELECT has_MrLololoshka FROM users WHERE user_id = ?", (user_id,))
    has_MrLololoshka = cursor.fetchone()[0]

    cursor.execute("SELECT has_nyan_mp3 FROM users WHERE user_id = ?", (user_id,))
    has_nyan_mp3 = cursor.fetchone()[0]

    if random.random() < 0.1 and not has_initndr:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана вторая часть секретной команды.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда кончается на /...ndr 😉"
        )
        return

    if random.random() < 0.1 and not has_HiTmaN_VadIM:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда кончается на /...VadIM 😉"
        )
        return

    if random.random() < 0.1 and not has_nyan_mp3:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда кончается на ...mp3 😉"
        )
        return

    if random.random() < 0.1 and not has_MrLololoshka:
        await message.answer(
            "Ты нашёл что-то странное... 🤔\n\n"
            "Кажется, где-то в этом боте спрятана секретная команда.\n"
            "Попробуй найти её, и ты получишь награду! 🎁\n\n"
            "Подсказка: команда кончается на /...loshka 😉"
        )
        return

    bonus_cooldowns[user_id] = current_time

    cat = get_random_cat(cats)

    rarities_str = ", ".join(rarities)

    try:
        rarities_str = "обычный,редкий,сверхредкий,эпический,мифический,легендарный,хромотический,особый"
        cursor.execute(
            f"""
            INSERT INTO users (user_id, rarity, points, highest_rarity, cat_coins) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET 
                rarity = excluded.rarity, 
                points = points + excluded.points, 
                highest_rarity = CASE 
                    WHEN highest_rarity IS NULL THEN excluded.rarity
                    WHEN INSTR('{rarities_str}', excluded.rarity) > INSTR('{rarities_str}', highest_rarity) THEN excluded.rarity 
                    ELSE highest_rarity 
                END,
                cat_coins = cat_coins + excluded.cat_coins
            """,
            (
                user_id,
                cat["rarity"],
                cat["points"],
                cat["rarity"],
                cat["cat_coins"],
            ),
        )
        conn.commit()

        cursor.execute(
            "SELECT id FROM cards WHERE user_id = ? AND cat_id = ?",
            (user_id, cat["id"]),
        )
        existing_card = cursor.fetchone()

        if existing_card:
            cursor.execute(
                "DELETE FROM cards WHERE user_id = ? AND cat_id = ?",
                (user_id, cat["id"]),
            )
            conn.commit()

        cursor.execute(
            "INSERT INTO cards (user_id, cat_id, cat_image, rarity, points) VALUES (?, ?, ?, ?, ?)",
            (user_id, cat["id"], cat["photo"], cat["rarity"], cat["points"]),
        )
        conn.commit()

        # Получаем имя пользователя
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

        # Определяем display_name
        if db_username:
            display_name = db_username
        elif tg_username:
            display_name = f"@{tg_username}"
        elif tg_first_name:
            display_name = tg_first_name
        else:
            display_name = f"Пользователь {user_id}"

        message_text = (
            f"👤 {display_name}, успех! Вы нашли бонусную карточку. \n"
            f"🌟 Карточка: «{cat['catname']}» 🐱\n"
            "--------------------------\n"
            f"💎 Редкость: {cat['rarity']}\n"
            f"✨ Очки: +{cat['points']} (Всего: {get_user_points(user_id)})\n"
            f"🐱 Котокоины: +{cat['cat_coins']} (Всего: {get_user_cat_coins(user_id)})\n"
            f"🧧 Описание: {cat['catinfo']}"
        )

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🔄 Получить еще карточку", callback_data="get_bonus_card"),
            InlineKeyboardButton("📚 Просмотреть коллекцию", callback_data="view_collection")
        )

        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=cat["photo"],
            caption=message_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
            reply_to_message_id=message.message_id,
        )
    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных: {e}")
        await message.answer("Произошла ошибка.")

        await log_operation_async(
            "Bonus Reward",
            f"User {message.from_user.id} claimed bonus (Rarity: {cat['rarity']})",
            "SUCCESS"
        )


async def put_command(message: types.Message):
    if not await check_name(message):
        return
    user_id = message.from_user.id
    current_time = time.time()

    cursor.execute("SELECT has_scratcher, last_put_time FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if not result or not result[0]:
        await message.answer("У вас нет Чесалки! Купите её в магазине, чтобы гладить котика.")
        return

    has_scratcher, last_put_time = result

    if last_put_time and (current_time - last_put_time) < 7200:
        remaining_time = 7200 - (current_time - last_put_time)
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        await message.answer(
            f"Вы уже гладили котика недавно. Попробуйте снова через {hours} часов {minutes} минут."
        )
        return

    cursor.execute("UPDATE users SET last_put_time = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()

    cursor.execute("UPDATE users SET points = points + 1000, cat_coins = cat_coins + 500 WHERE user_id = ?", (user_id,))
    conn.commit()

    await message.answer(
        "Вы погладили котика и получили 1000 очков и 500 котокоинов! 🐾\n"
        "Котик доволен и мурлычет от удовольствия!"
    )

async def collection_command(message: types.Message):
    if not await check_name(message):
        return
    user_id = message.from_user.id

    cursor.execute("SELECT cat_image, rarity, points, cat_id FROM cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()

    if not cards:
        await message.answer("У вас пока нет карточек в коллекции.")
        return

    await show_card(message, cards, 0)

async def show_card(message: types.Message, cards: list, index: int):
    if not await check_name(message):
        return
    if index >= len(cards) or index < 0:
        await message.answer("Это все ваши карточки!")
        return

    cat_image, rarity, points, cat_id = cards[index]

    cat = next((cat for cat in cats if cat["id"] == cat_id), None)
    cat_name = cat["catname"] if cat else "Неизвестный кот"

    keyboard = InlineKeyboardMarkup(row_width=2)

    if index > 0:
        keyboard.insert(InlineKeyboardButton("⬅️", callback_data=f"prev_card_{index - 1}"))

    if index < len(cards) - 1:
        keyboard.insert(InlineKeyboardButton("➡️", callback_data=f"next_card_{index + 1}"))

    await message.bot.send_photo(
        chat_id=message.chat.id,
        photo=cat_image,
        caption=f"🐱 Имя: {cat_name}\n💎 Редкость: {rarity}\n✨ Очки: {points}\n",
        reply_markup=keyboard,
    )

async def next_card_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[2])

    cursor.execute("SELECT cat_image, rarity, points, cat_id FROM cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()

    await callback.message.delete()

    await show_card(callback.message, cards, index)

async def prev_card_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[2])

    cursor.execute("SELECT cat_image, rarity, points, cat_id FROM cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()

    await callback.message.delete()

    await show_card(callback.message, cards, index)

async def get_another_card_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    current_time = time.time()

    if user_id in cooldowns:
        remaining_time = 10800 - (current_time - cooldowns[user_id])
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await callback.answer(
                f"Вы можете получить еще карточку кота через {hours} часов {minutes} минут."
            )
            return

    await callback.answer("Получение карточки...")
    await send_cat(callback.message)

async def get_bonus_card_callback(callback: types.CallbackQuery):
    current_user_id = callback.from_user.id
    current_time = time.time()

    if current_user_id in bonus_cooldowns:
        bonus_remaining_time = 21600 - (current_time - bonus_cooldowns[current_user_id])
        if bonus_remaining_time > 0:
            hours = int(bonus_remaining_time // 3600)
            minutes = int((bonus_remaining_time % 3600) // 60)
            await callback.answer(
                f"Вы можете получить еще бонусную карточку через {hours} часов {minutes} минут."
            )
            return

    await callback.answer("Получение бонусной карточки...")
    bonus_cooldowns[current_user_id] = current_time

async def view_collection_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    cursor.execute("SELECT cat_image, rarity, points, cat_id FROM cards WHERE user_id = ?", (user_id,))
    cards = cursor.fetchall()

    if not cards:
        await callback.answer("У вас пока нет карточек в коллекции.")
        return

    await show_card(callback.message, cards, 0)

def register_commands_handlers(dp: Dispatcher):
    dp.register_message_handler(help_command, commands=["help"])
    dp.register_message_handler(cat_command, commands=["cat"])
    dp.register_message_handler(send_cat, lambda message: message.text.lower() == "кот")
    dp.register_message_handler(bonus_command, commands=["bonus"])
    dp.register_message_handler(put_command, commands=["put"])
    dp.register_message_handler(collection_command, commands=["collection"])
    dp.register_callback_query_handler(next_card_callback, lambda c: c.data.startswith("next_card_"))
    dp.register_callback_query_handler(prev_card_callback, lambda c: c.data.startswith("prev_card_"))
    dp.register_callback_query_handler(get_another_card_callback, lambda c: c.data == "get_another_card")
    dp.register_message_handler(send_cat, lambda message: message.text.lower() in cat_synonyms)
    dp.register_callback_query_handler(get_bonus_card_callback, lambda c: c.data == "get_bonus_card")
    dp.register_callback_query_handler(view_collection_callback, lambda c:c.data == "view_collection")
    dp.register_callback_query_handler(send_cat, lambda c: c.data == "send_cat")
    dp.register_callback_query_handler(bonus_command, lambda c: c.data == "bonus_command")
    dp.register_callback_query_handler(shop_command, lambda c: c.data == "shop_command")
    dp.register_callback_query_handler(put_command, lambda c: c.data == "put_command")
    dp.register_callback_query_handler(collection_command, lambda c: c.data == "collection_command")
    dp.register_callback_query_handler(jujitsu_command, lambda c: c.data == "jujitsu_command")
    dp.register_callback_query_handler(leders_command, lambda c: c.data == "leders_command")
    dp.register_callback_query_handler(exchange_command, lambda c: c.data == "exchange_command")
    dp.register_my_chat_member_handler(on_bot_added_to_group)
    dp.register_message_handler(initndr_command, commands=["initndr"])
    dp.register_message_handler(HiTmaN_VadIM_command, commands=["HiTmaN_VadIM"])
    dp.register_message_handler(MrLololoshka_command, commands=["MrLololoshka"])
    dp.register_message_handler(nyan_mp3_command, commands=["nyan_mp3"])
    create_magic_cards_table()
    add_wishing_fountain_column()


