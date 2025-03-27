import random
import time
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from CheckName import check_name
from MagicData import magic, technique_weights
from advanced_logger import log_operation_async
from lecsicon import magic_synonyms
from aiogram import Dispatcher, types
import logging
import json

from quests import update_quest_progress, load_user_progress

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

def get_random_magic(magic, has_magic_luck_scroll=False):
    weighted_magic = []
    for m in magic:
        if has_magic_luck_scroll:

            if m["technique"] in ["Сложная", "Великая"]:
                weight = technique_weights.get(m["technique"], 1) * 2
            else:
                weight = technique_weights.get(m["technique"], 1)
        else:
            weight = technique_weights.get(m["technique"], 1)
        weighted_magic.extend([m] * weight)
    return random.choice(weighted_magic)


async def jujitsu_command(message: types.Message):
    if not await check_name(message):
        return
    user_id = message.from_user.id
    current_time = time.time()

    cursor.execute(
        "SELECT last_magic_time, has_magic_medallion, has_magic_luck_scroll, has_magic_scroll FROM users WHERE user_id = ?",
        (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, magic_coins, has_magic_scroll) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0),
        )
        conn.commit()
        last_magic_time = 0
        has_magic_medallion = 0
        has_magic_luck_scroll = 0
        has_magic_scroll = 0
    else:
        last_magic_time, has_magic_medallion, has_magic_luck_scroll, has_magic_scroll = user_data

    if last_magic_time and (current_time - last_magic_time) < 21600 and not has_magic_scroll:
        remaining_time = 21600 - (current_time - last_magic_time)
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        await message.answer(
            f"Вы осмотрелись, но не нашли магической карты. Попробуйте через {hours} часов {minutes} минут."
        )
        return

    if has_magic_scroll:
        cursor.execute("UPDATE users SET has_magic_scroll = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    cursor.execute("UPDATE users SET last_magic_time = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()

    magic_card = get_random_magic(magic, has_magic_luck_scroll)

    try:
        cursor.execute(
            "INSERT INTO magic_cards (user_id, card_id) VALUES (?, ?)",
            (user_id, magic_card["id"]),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных при сохранении магической карты: {e}")

    if has_magic_medallion:
        magic_card["magic_coins"] = int(magic_card["magic_coins"] * 1.25)

    if has_magic_luck_scroll:
        magic_card["points"] = int(magic_card["points"] * 1.2)

    try:
        cursor.execute(
            """
            UPDATE users SET 
                rarity = ?, 
                points = points + ?, 
                highest_rarity = CASE 
                    WHEN ? > highest_rarity THEN ? 
                    ELSE highest_rarity 
                END,
                magic_coins = magic_coins + ?
            WHERE user_id = ?
            """,
            (
                magic_card["technique"],
                magic_card["points"],
                magic_card["technique"],
                magic_card["technique"],
                magic_card["magic_coins"],
                user_id,
            ),
        )
        conn.commit()

        message_text = (
            f"👤 {message.from_user.first_name}, успех! Вы нашли магическую карту!\n"
            f"✨ Карта: «{magic_card['magicname']}»\n"
            "--------------------------\n"
            f"🔮 Техника: {magic_card['technique']}\n"
            f"💎 Очки: +{magic_card['points']}\n"
            f"🔮 Магические коины: +{magic_card['magic_coins']}\n"
            f"🧧 Описание: {magic_card['magicinfo']}"
        )

        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=magic_card["photo"],
            caption=message_text,
            reply_to_message_id=message.message_id,
            parse_mode=types.ParseMode.MARKDOWN,
        )
    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных: {e}")
        await message.answer("Произошла ошибка.")

    user_id = message.from_user.id
    user_progress = await load_user_progress(user_id)

    if user_progress and not user_progress["completed"]:
        if user_progress["category"] == "magic":
            await update_quest_progress(user_id, "magic")

    if last_magic_time and (current_time - last_magic_time) < 21600:
        await log_operation_async(
            "Cooldown Blocked",
            f"User {message.from_user.id} tried to bypass cooldown",
            "WARNING"
        )


async def send_magic(message: types.Message):
    if message.text.lower() not in ["Магическая битва"] + magic_synonyms:
        return
    if not await check_name(message):
        return
    user_id = message.from_user.id
    current_time = time.time()

    cursor.execute("SELECT last_magic_time, has_magic_medallion, has_magic_luck_scroll, has_magic_scroll FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.execute(
            "INSERT INTO users (user_id, rarity, points, highest_rarity, magic_coins, has_magic_scroll) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "обычный", 0, "обычный", 0, 0),
        )
        conn.commit()
        last_magic_time = 0
        has_magic_medallion = 0
        has_magic_luck_scroll = 0
        has_magic_scroll = 0
    else:
        last_magic_time, has_magic_medallion, has_magic_luck_scroll, has_magic_scroll = user_data


    if last_magic_time and (current_time - last_magic_time) < 21600 and not has_magic_scroll:
        remaining_time = 21600 - (current_time - last_magic_time)
        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        await message.answer(
            f"Вы осмотрелись, но не нашли магической карты. Попробуйте через {hours} часов {minutes} минут."
        )
        return


    if has_magic_scroll:
        cursor.execute("UPDATE users SET has_magic_scroll = 0 WHERE user_id = ?", (user_id,))
        conn.commit()

    cursor.execute("UPDATE users SET last_magic_time = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()

    magic_card = get_random_magic(magic, has_magic_luck_scroll)

    try:
        cursor.execute(
            "INSERT INTO magic_cards (user_id, card_id) VALUES (?, ?)",
            (user_id, magic_card["id"]),
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных при сохранении магической карты: {e}")


    if has_magic_medallion:
        magic_card["magic_coins"] = int(magic_card["magic_coins"] * 1.25)


    if has_magic_luck_scroll:
        magic_card["points"] = int(magic_card["points"] * 1.2)

    try:
        cursor.execute(
            """
            UPDATE users SET 
                rarity = ?, 
                points = points + ?, 
                highest_rarity = CASE 
                    WHEN ? > highest_rarity THEN ? 
                    ELSE highest_rarity 
                END,
                magic_coins = magic_coins + ?
            WHERE user_id = ?
            """,
            (
                magic_card["technique"],
                magic_card["points"],
                magic_card["technique"],
                magic_card["technique"],
                magic_card["magic_coins"],
                user_id,
            ),
        )
        conn.commit()

        message_text = (
            f"👤 {message.from_user.first_name}, успех! Вы нашли магическую карту!\n"
            f"✨ Карта: «{magic_card['magicname']}»\n"
            "--------------------------\n"
            f"🔮 Техника: {magic_card['technique']}\n"  
            f"💎 Очки: +{magic_card['points']}\n"
            f"🔮 Магические коины: +{magic_card['magic_coins']}\n"
            f"🧧 Описание: {magic_card['magicinfo']}"
        )

        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=magic_card["photo"],
            caption=message_text,
            reply_to_message_id=message.message_id,
            parse_mode=types.ParseMode.MARKDOWN,
        )

    except sqlite3.Error as e:
        logging.error(f"Ошибка базы данных: {e}")
        await message.answer("Произошла ошибка.")

        user_progress = await load_user_progress(user_id)
        if user_progress and not user_progress["completed"] and user_progress["category"] == "magic":
            await update_quest_progress(user_id, "magic")
            await log_operation_async(
                "Quest Progress",
                f"User {user_id} updated magic quest progress",
                "DEBUG"
            )

        await log_operation_async(
            "Magic Used",
            f"User {message.from_user.id} cast {magic_card['magicname']}",
            "DEBUG"
        )


async def jujitsucollection_command(message: types.Message):
    if not await check_name(message):
        return
    user_id = message.from_user.id

    cursor.execute("SELECT card_id FROM magic_cards WHERE user_id = ?", (user_id,))
    magic_cards = cursor.fetchall()

    if not magic_cards:
        await message.answer("У вас пока нет магических карт в коллекции.")
        return

    await show_magic_card(message, magic_cards, 0)

async def show_magic_card(message: types.Message, magic_cards: list, index: int):
    if index >= len(magic_cards) or index < 0:
        await message.answer("Это все ваши магические карты!")
        return

    card_id = magic_cards[index][0]
    magic_card = next((m for m in magic if m["id"] == card_id), None)

    if not magic_card:
        await message.answer("Ошибка: карта не найдена.")
        return

    keyboard = InlineKeyboardMarkup(row_width=2)

    if index > 0:
        keyboard.insert(InlineKeyboardButton("⬅️", callback_data=f"prev_magic_card_{index - 1}"))

    if index < len(magic_cards) - 1:
        keyboard.insert(InlineKeyboardButton("➡️", callback_data=f"next_magic_card_{index + 1}"))

    await message.bot.send_photo(
        chat_id=message.chat.id,
        photo=magic_card["photo"],
        caption=f"🔮 Имя: {magic_card['magicname']}\n✨ Техника: {magic_card['technique']}\n💎 Очки: {magic_card['points']}\n🧧 Описание: {magic_card['magicinfo']}\n",
        reply_markup=keyboard,
    )

async def next_magic_card_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[3])

    cursor.execute("SELECT card_id FROM magic_cards WHERE user_id = ?", (user_id,))
    magic_cards = cursor.fetchall()

    await callback.message.delete()
    await show_magic_card(callback.message, magic_cards, index)

async def prev_magic_card_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    index = int(callback.data.split("_")[3])

    cursor.execute("SELECT card_id FROM magic_cards WHERE user_id = ?", (user_id,))
    magic_cards = cursor.fetchall()

    await callback.message.delete()
    await show_magic_card(callback.message, magic_cards, index)





def register_magic_handlers(dp: Dispatcher):
    dp.register_message_handler(send_magic, lambda message: message.text.lower() in magic_synonyms)
    dp.register_message_handler(jujitsu_command, commands=["jujitsu"])
    dp.register_message_handler(jujitsucollection_command, commands=["jujitsucollection"])
    dp.register_callback_query_handler(next_magic_card_callback, lambda c: c.data.startswith("next_magic_card_"))
    dp.register_callback_query_handler(prev_magic_card_callback, lambda c: c.data.startswith("prev_magic_card_"))