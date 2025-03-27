import logging
import random
import sqlite3
import time
import asyncio
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import Dispatcher

from advanced_logger import log_operation_async
from database import get_db_connection
from CheckName import check_name
from melodydata import melody_songs
from aiogram.utils.exceptions import MessageToDeleteNotFound

from quests import load_user_progress, update_quest_progress

logging.basicConfig(level=logging.DEBUG)
logging.info("MelodyGame.py загружен")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
except sqlite3.Error as e:
    logging.error(f"Ошибка базы данных: {e}")

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
logging.info("MelodyGame продолжает работу")

melody_cooldowns = {}

user_choices = {}
sent_photos = None
sent_message = None
sent_audio = None

async def melody_command(message: types.Message):
    global sent_photos, sent_message, sent_audio
    logging.info("melody_command вызвана")  # Дополнительное логирование
    if not await check_name(message):
        return

    user_id = message.from_user.id
    current_time = time.time()

    if user_id in melody_cooldowns:
        remaining_time = 43200 - (current_time - melody_cooldowns[user_id])
        if remaining_time > 0:
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            await message.answer(f"Вы можете использовать команду /melody снова через {hours} часов {minutes} минут.")
            return

    melody_cooldowns[user_id] = current_time

    # Выбираем случайный блок
    selected_melody = random.choice(melody_songs)
    photos = selected_melody["photos"]

    # Выбираем одну случайную фотографию и запоминаем её описание и звук
    correct_photo = random.choice(photos)
    correct_description = correct_photo["description"]
    correct_song = correct_photo["song"]  # Уникальный звук для этой фотографии

    # Отправляем одну случайную фотографию
    sent_photos = await message.bot.send_photo(chat_id=message.chat.id, photo=correct_photo["url"])

    # Создаем список всех описаний из файла melodydata.py
    all_descriptions = [photo["description"] for photo in photos]

    # Убираем правильное описание из списка, чтобы оно не дублировалось
    all_descriptions.remove(correct_description)

    # Выбираем 5 случайных описаний из оставшихся
    random_descriptions = random.sample(all_descriptions, 5)

    # Добавляем правильное описание в список
    all_buttons_descriptions = random_descriptions + [correct_description]

    # Перемешиваем описания
    random.shuffle(all_buttons_descriptions)

    # Создаем кнопки
    keyboard = InlineKeyboardMarkup(row_width=2)

    for description in all_buttons_descriptions:
        if description == correct_description:
            # Правильная кнопка
            keyboard.insert(InlineKeyboardButton(description, callback_data="melody_choice_correct"))
        else:
            # Неправильные кнопки
            keyboard.insert(InlineKeyboardButton(description, callback_data="melody_choice_wrong"))

    sent_message = await message.answer("Что это за мем?", reply_markup=keyboard)

    try:
        # Отправляем соответствующий звук
        sent_audio = await message.bot.send_audio(chat_id=message.chat.id, audio=correct_song, caption="Подсказка")
    except Exception as e:
        logging.error(f"Ошибка при отправке аудио: {e}")
        await message.answer("Произошла ошибка при загрузке аудио. Попробуйте снова позже.")
        return

    asyncio.create_task(delete_after_timeout(user_id, sent_photos, sent_message, sent_audio, message))


async def delete_after_timeout(user_id, sent_photos, sent_message, sent_audio, message):
    await asyncio.sleep(60)  # Ждем 60 секунд
    if user_id not in user_choices:
        try:
            # Пытаемся удалить фотографию
            await sent_photos.delete()
        except MessageToDeleteNotFound:
            logging.warning("Фотография уже удалена.")

        try:
            # Пытаемся удалить сообщение с кнопками
            await sent_message.delete()
        except MessageToDeleteNotFound:
            logging.warning("Сообщение с кнопками уже удалено.")

        try:
            # Пытаемся удалить аудио
            await sent_audio.delete()
        except MessageToDeleteNotFound:
            logging.warning("Аудио уже удалено.")
            return

        await message.answer("Вы не успели выбрать правильную фотографию. Попробуйте снова через 12 часов.")


async def melody_callback(callback: types.CallbackQuery):
    logging.info(f"melody_callback вызвана с данными: {callback.data}")
    global sent_photos, sent_message, sent_audio


    user_id = callback.from_user.id

    if callback.data == "melody_choice_correct":
        if callback.data == "melody_choice_correct":
            await log_operation_async(
                "Melody Game Win",
                f"User {callback.from_user.id} guessed the melody",
                "GAME"
            )
        cursor.execute("UPDATE users SET points = points + 8000, note_coins = note_coins + 500 WHERE user_id = ?",
                       (user_id,))
        conn.commit()
        await callback.message.answer(
            "Поздравляем! Вы выбрали правильный мем и получили 8000 очков и 500 нотокоинов.")

        # Обновляем прогресс квеста
        user_progress = await load_user_progress(user_id)
        if user_progress and not user_progress["completed"] and user_progress["category"] == "melody":
            await update_quest_progress(user_id, "melody")
            await log_operation_async(
                "Quest Progress",
                f"User {user_id} updated melody quest progress",
                "DEBUG"
            )
    else:
        await callback.message.answer("К сожалению, это не правильная фотография. Попробуйте снова через 12 часов.")
        # Пользователь выбрал неправильную кнопку
        await callback.message.answer("К сожалению, это не правильная фотография. Попробуйте снова через 12 часов.")

    try:
        # Пытаемся удалить фотографию
        await sent_photos.delete()
    except MessageToDeleteNotFound:
        logging.warning("Фотография уже удалена.")

    try:
        # Пытаемся удалить сообщение с кнопками
        await sent_message.delete()
    except MessageToDeleteNotFound:
        logging.warning("Сообщение с кнопками уже удалено.")

    try:
        # Пытаемся удалить аудио
        await sent_audio.delete()
    except MessageToDeleteNotFound:
        logging.warning("Аудио уже удалено.")

def register_melody_handlers(dp: Dispatcher):
    logging.info("Регистрация обработчиков melody_command и melody_callback")  # Дополнительное логирование
    dp.register_message_handler(melody_command, commands=["melody"])
    dp.register_callback_query_handler(melody_callback, lambda c: c.data.startswith("melody_choice_"))