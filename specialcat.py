import random
import logging
import sqlite3
from aiogram import types
from database import get_db_connection
from spescial import special_cats

conn = get_db_connection()
cursor = conn.cursor()

async def specialcat_command(message: types.Message):
    user_id = message.from_user.id


    cursor.execute("SELECT has_wishing_fountain FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        await message.answer("У вас еще нет профиля. Получите кота, чтобы создать его!")
        return

    has_wishing_fountain = result[0]

    if not has_wishing_fountain:
        await message.answer("У вас нет Фонтана желаний. Купите его в магазине!")
        return


    cat = random.choice(special_cats)
    logging.info(f"Выбрана карточка из special_cats: {cat}")


    cursor.execute("UPDATE users SET has_wishing_fountain = 0 WHERE user_id = ?", (user_id,))
    conn.commit()

    try:

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

        logging.info(f"Карточка {cat['catname']} успешно сохранена в базе данных.")

    except sqlite3.Error as e:
        logging.error(f"Ошибка при сохранении карточки в базу данных: {e}")
        await message.answer("Произошла ошибка при сохранении карточки.")
        return


    message_text = (
        f"👤 {message.from_user.first_name}, успех! Вы нашли особую карточку! 🎉\n"
        f"🌟 Карточка: «{cat['catname']}» 🐱\n"
        "--------------------------\n"
        f"💎 Редкость: {cat['rarity']}\n"
        f"✨ Очки: +{cat['points']}\n"
        f"🐱 Котокоины: +{cat['cat_coins']}\n"
        f"🧧 Описание: {cat['catinfo']}\n"
    )

    await message.bot.send_photo(
        chat_id=message.chat.id,
        photo=cat["photo"],
        caption=message_text,
        parse_mode=types.ParseMode.MARKDOWN,
    )

def register_specialcat_handlers(dp):
    dp.register_message_handler(specialcat_command, commands=["specialcat"])