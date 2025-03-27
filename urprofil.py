import logging
import os
import sqlite3
import time
from aiogram import types, Dispatcher
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton

from advanced_logger import log_operation_async
from database import get_db_connection
from CheckName import check_name
from data import cats  # Импортируем список cats из data.py

conn = get_db_connection()
cursor = conn.cursor()

def add_note_coins_column():
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        if "note_coins" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE users ADD COLUMN note_coins INTEGER DEFAULT 0")
            conn.commit()
            logging.info("Столбец note_coins добавлен в таблицу users.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении столбца note_coins: {e}")


add_note_coins_column()


def add_catname_column():
    try:
        cursor.execute("PRAGMA table_info(cards)")
        columns = cursor.fetchall()
        if "catname" not in [column[1] for column in columns]:
            cursor.execute("ALTER TABLE cards ADD COLUMN catname TEXT")
            conn.commit()
            logging.info("Столбец catname добавлен в таблицу cards.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении столбца catname: {e}")

def update_catname_in_cards():
    try:
        cursor.execute("SELECT cat_id FROM cards")
        cards = cursor.fetchall()
        for card in cards:
            cat_id = card[0]
            cat = next((cat for cat in cats if cat["id"] == cat_id), None)
            if cat:
                cursor.execute(
                    "UPDATE cards SET catname = ? WHERE cat_id = ?",
                    (cat["catname"], cat_id),
                )
                conn.commit()
        logging.info("Столбец catname обновлён в таблице cards.")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при обновлении столбца catname: {e}")




# Создаем папку для аватаров, если её нет
if not os.path.exists('avatars'):
    os.makedirs('avatars')

# Создаем таблицу avatar_waiting, если её нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS avatar_waiting (
    user_id INTEGER PRIMARY KEY,
    start_time INTEGER
)
''')
conn.commit()

# Создаем таблицу для хранения любимой карты, если её нет
cursor.execute('''
CREATE TABLE IF NOT EXISTS favorite_cards (
    user_id INTEGER PRIMARY KEY,
    card_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
''')
conn.commit()

async def avatar_command(message: types.Message):
    user_id = message.from_user.id
    start_time = int(time.time())

    cursor.execute(
        "INSERT OR REPLACE INTO avatar_waiting (user_id, start_time) VALUES (?, ?)",
        (user_id, start_time),
    )
    conn.commit()

    await message.answer("Пожалуйста, отправьте ваше фото в течение 30 секунд.")

async def handle_avatar(message: types.Message):
    user_id = message.from_user.id

    # Получаем время начала ожидания фотографии из базы данных
    cursor.execute(
        "SELECT start_time FROM avatar_waiting WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchone()

    if not result:
        await message.answer("Сначала напишите /avatar.")
        return

    start_time = result[0]

    if time.time() - start_time > 30:
        await message.answer("Прошло 30 секунд. Пожалуйста, напишите /avatar снова.")
        return

    if not message.photo:
        await message.answer("Это не фотография. Пожалуйста, отправьте фото.")
        return

    # Сохраняем фотографию
    photo_id = message.photo[-1].file_id
    photo_info = await message.bot.get_file(photo_id)
    photo_path = f"avatars/{user_id}.jpg"

    await message.photo[-1].download(destination_file=photo_path)
    await message.answer("Фотография успешно сохранена!")

    # Удаляем запись о ожидании фотографии из базы данных
    cursor.execute(
        "DELETE FROM avatar_waiting WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()

    await log_operation_async(
        "Avatar Changed",
        f"User {message.from_user.id} uploaded new avatar",
        "PROFILE"
    )


async def profil_command(message: types.Message):
    if not await check_name(message):
        return

    user_id = message.from_user.id
    cursor.execute(
        "SELECT rarity, note_coins, points, highest_rarity, cat_coins, magic_coins, has_scratcher, has_companion, "
        "booster_end_time, has_time_watch, has_magic_medallion, has_magic_luck_scroll, has_wishing_fountain, "
        "username FROM users WHERE user_id = ?",
        (user_id,),
    )
    user_data = cursor.fetchone()

    if user_data:
        rarity, notocoins, points, highest_rarity, cat_coins, magic_coins, has_scratcher, has_companion, booster_end_time, has_time_watch, has_magic_medallion, has_magic_luck_scroll, has_wishing_fountain, username = user_data
        booster_status = "✅ активен" if booster_end_time and booster_end_time > time.time() else "❌ не активен"
        wishing_fountain_status = "✅ есть" if has_wishing_fountain else "❌ нет"

        # Получаем любимую карту пользователя
        cursor.execute(
            "SELECT card_id FROM favorite_cards WHERE user_id = ?",
            (user_id,),
        )
        favorite_card = cursor.fetchone()
        favorite_card_name = "не выбрана"
        if favorite_card:
            # Ищем имя кота по cat_id в списке cats
            cat_id = favorite_card[0]
            cat = next((cat for cat in cats if cat["id"] == cat_id), None)
            if cat:
                favorite_card_name = cat["catname"]

        avatar_path = f"avatars/{user_id}.jpg"
        if os.path.exists(avatar_path):
            photo = InputFile(avatar_path)
            caption = (
                f"🌟 **Профиль пользователя: {username}** 🌟\n\n"
                f"❤️ **Любимая карта:** {favorite_card_name}\n"
                f"✨ **Очки:** {points:,}\n"
                f"🏆 **Самая высокая редкость:** {highest_rarity}\n\n"

                f"💰 **Ресурсы:**\n"
                f"🐱 **Котокоины:** {cat_coins:,}\n"
                f"🔮 **Магические коины:** {magic_coins:,}\n"
                f"🎵 **Нотокоины:** {notocoins:,}\n\n"

                f"🛠️ **Инвентарь:**\n"
                f"🐾 **Чесалка:** {'✅ есть' if has_scratcher else '❌ нет'}\n"
                f"⏳ **Часы времени:** {'✅ есть' if has_time_watch else '❌ нет'}\n"
                f"🔮 **Магический медальон:** {'✅ есть' if has_magic_medallion else '❌ нет'}\n"
                f"✨ **Магический свиток удачи:** {'✅ есть' if has_magic_luck_scroll else '❌ нет'}\n"
                f"✨ **Фонтан желаний:** {wishing_fountain_status}\n\n"

                f"🚀 **Бустеры:**\n"
                f"🐱 **Кот компаньон:** {'✅ есть' if has_companion else '❌ нет'}\n"
                f"🚀 **Кот-бустер:** {booster_status}\n\n"
            )

            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton("📚 Мои карты", callback_data="view_collection"),
                InlineKeyboardButton("❤️ Выбрать любимую карту", callback_data="choose_favorite_card")
            )

            await message.answer_photo(
                photo,
                caption=caption,
                reply_markup=keyboard,
                parse_mode=types.ParseMode.MARKDOWN,
            )
        else:
            await message.answer(
                f"🌟 **Профиль пользователя: {username}** 🌟\n\n"
                f"❤️ **Любимая карта:** {favorite_card_name}\n"
                f"✨ **Очки:** {points:,}\n"
                f"🏆 **Самая высокая редкость:** {highest_rarity}\n\n"

                f"💰 **Ресурсы:**\n"
                f"🐱 **Котокоины:** {cat_coins:,}\n"
                f"🔮 **Магические коины:** {magic_coins:,}\n"
                f"🎵 **Нотокоины:** {notocoins:,}\n\n"

                f"🛠️ **Инвентарь:**\n"
                f"🐾 **Чесалка:** {'✅ есть' if has_scratcher else '❌ нет'}\n"
                f"⏳ **Часы времени:** {'✅ есть' if has_time_watch else '❌ нет'}\n"
                f"🔮 **Магический медальон:** {'✅ есть' if has_magic_medallion else '❌ нет'}\n"
                f"✨ **Магический свиток удачи:** {'✅ есть' if has_magic_luck_scroll else '❌ нет'}\n"
                f"✨ **Фонтан желаний:** {wishing_fountain_status}\n\n"

                f"🚀 **Бустеры:**\n"
                f"🐱 **Кот компаньон:** {'✅ есть' if has_companion else '❌ нет'}\n"
                f"🚀 **Кот-бустер:** {booster_status}\n\n",
                parse_mode=types.ParseMode.MARKDOWN,
            )
    else:
        await message.answer("У вас еще нет профиля. Получите кота, чтобы создать его!")

async def choose_favorite_card(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    cursor.execute(
        "SELECT cat_id, cat_image, rarity, points, catname FROM cards WHERE user_id = ?",
        (user_id,),
    )
    cards = cursor.fetchall()

    if not cards:
        await callback.answer("У вас пока нет карточек в коллекции.")
        return


    await show_card_for_favorite(callback.message, cards, 0)

async def show_card_for_favorite(message: types.Message, cards: list, index: int):
    if index >= len(cards) or index < 0:
        await message.answer("Это все ваши карточки!")
        return

    # Распаковываем все 5 значений
    cat_id, cat_image, rarity, points, catname = cards[index]

    keyboard = InlineKeyboardMarkup(row_width=2)
    if index > 0:
        keyboard.insert(InlineKeyboardButton("⬅️", callback_data=f"prev_favorite_{index - 1}"))
    if index < len(cards) - 1:
        keyboard.insert(InlineKeyboardButton("➡️", callback_data=f"next_favorite_{index + 1}"))
    keyboard.add(InlineKeyboardButton("❤️ Выбрать эту карту", callback_data=f"set_favorite_{cat_id}"))

    await message.bot.send_photo(
        chat_id=message.chat.id,
        photo=cat_image,
        caption=f"🐱 Имя кота: {catname}\n💎 Редкость: {rarity}\n✨ Очки: {points}",
        reply_markup=keyboard,
    )

async def set_favorite_card(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    card_id = callback.data.split("_")[2]

    # Сохраняем любимую карту в базу данных
    cursor.execute(
        "INSERT OR REPLACE INTO favorite_cards (user_id, card_id) VALUES (?, ?)",
        (user_id, card_id),
    )
    conn.commit()

    await callback.answer(f"Карта {card_id} выбрана как любимая!")
    await callback.message.delete()

async def next_favorite_card(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[2])

    cursor.execute(
        "SELECT cat_id, cat_image, rarity, points, catname FROM cards WHERE user_id = ?",
        (user_id,),
    )
    cards = cursor.fetchall()

    await callback.message.delete()
    await show_card_for_favorite(callback.message, cards, index)

async def prev_favorite_card(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[2])

    cursor.execute(
        "SELECT cat_id, cat_image, rarity, points, catname FROM cards WHERE user_id = ?",
        (user_id,),
    )
    cards = cursor.fetchall()

    await callback.message.delete()
    await show_card_for_favorite(callback.message, cards, index)

def register_urprofil_handlers(dp: Dispatcher):
    dp.register_message_handler(avatar_command, commands=["avatar"])
    dp.register_message_handler(handle_avatar, content_types=types.ContentType.PHOTO)
    dp.register_message_handler(profil_command, commands=["profile"])
    dp.register_callback_query_handler(choose_favorite_card, lambda c: c.data == "choose_favorite_card")
    dp.register_callback_query_handler(set_favorite_card, lambda c: c.data.startswith("set_favorite_"))
    dp.register_callback_query_handler(next_favorite_card, lambda c: c.data.startswith("next_favorite_"))
    dp.register_callback_query_handler(prev_favorite_card, lambda c: c.data.startswith("prev_favorite_"))
    add_catname_column()
    update_catname_in_cards()