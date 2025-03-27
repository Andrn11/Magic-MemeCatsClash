import json
import random
from datetime import datetime
from aiogram import types, Dispatcher
from pathlib import Path
import aiofiles
from typing import Dict, Any, Optional, List

from database import get_db_connection

# Настройки
QUESTS_DIR = Path("quests_data")
USER_PROGRESS_DIR = QUESTS_DIR / "user_progress_json_files"
QUEST_CATEGORIES = {
    "cat": QUESTS_DIR / "available_quests/available_quests_cat",
    "magic": QUESTS_DIR / "available_quests/available_quests_magic",
    "melody": QUESTS_DIR / "available_quests/available_quests_melodygame"
}
CATEGORY_WEIGHTS = {
    "cat": 1.0,    # Стандартная частота
    "magic": 1.0,  # Стандартная частота
    "melody": 1.25 # На 25% чаще
}

# Проверка структуры папок при импорте
for category_dir in QUEST_CATEGORIES.values():
    if not category_dir.exists():
        raise RuntimeError(
            f"Папка квестов не найдена: {category_dir}\n"
            "Сначала выполните init_quests.py для создания структуры"
        )


async def log_operation_async(operation: str, details: str, level: str = "INFO"):
    """Асинхронное логирование операций"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level.upper()}: {operation}\nДетали: {details}\n\n"

    try:
        async with aiofiles.open("logs/quests.log", mode="a", encoding="utf-8") as f:
            await f.write(log_entry)
    except Exception as e:
        print(f"⚠️ Ошибка логирования: {e}")


async def load_user_progress(user_id: int) -> Optional[Dict[str, Any]]:
    """Загрузка и валидация прогресса пользователя"""
    user_file = USER_PROGRESS_DIR / f"{user_id}.json"
    try:
        if user_file.exists():
            async with aiofiles.open(user_file, mode="r", encoding="utf-8") as f:
                data = json.loads(await f.read())

                # Валидация данных
                required_fields = ["active_quest", "category", "progress", "completed"]
                if not all(field in data for field in required_fields):
                    await log_operation_async(
                        "Invalid Progress File",
                        f"User {user_id} - Missing fields, resetting",
                        "WARNING"
                    )
                    return None

                # Дополнительная проверка для "битых" квестов
                if data["active_quest"] and not data.get("quest_file"):
                    await log_operation_async(
                        "Corrupted Quest",
                        f"User {user_id} - Quest without file, resetting",
                        "ERROR"
                    )
                    return None

                return data
    except Exception as e:
        await log_operation_async("Load Progress Error", f"User {user_id}: {str(e)}", "ERROR")
    return None


async def save_user_progress(user_id: int, data: Dict[str, Any]):
    """Сохранение прогресса пользователя"""
    user_file = USER_PROGRESS_DIR / f"{user_id}.json"
    try:
        async with aiofiles.open(user_file, mode="w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        await log_operation_async(
            "Save Progress Error",
            f"User {user_id}: {str(e)}",
            "CRITICAL"
        )


async def load_quests(category: str) -> List[Dict[str, Any]]:
    """Загрузка всех квестов указанной категории"""
    quests = []
    quest_dir = QUEST_CATEGORIES.get(category)

    if not quest_dir:
        return quests

    for quest_file in quest_dir.glob("*.json"):
        try:
            async with aiofiles.open(quest_file, mode="r", encoding="utf-8") as f:
                quest_data = json.loads(await f.read())
                quest_data["file"] = quest_file.name  # Сохраняем имя файла для логов
                quests.append(quest_data)
        except Exception as e:
            await log_operation_async(
                "Load Quest Error",
                f"Failed to load {quest_file}: {str(e)}",
                "ERROR"
            )

    return quests


async def assign_random_quest(user_id: int) -> Optional[Dict[str, Any]]:
    try:
        weighted_quests = []

        # Собираем ВСЕ квесты с учётом весов
        for category in QUEST_CATEGORIES:
            quests = await load_quests(category)
            for quest in quests:
                quest["_category"] = category
                # Добавляем квест несколько раз в зависимости от веса категории
                repeat_count = int(CATEGORY_WEIGHTS.get(category, 1.0) * 100)
                weighted_quests.extend([quest] * repeat_count)

        # Проверяем, есть ли квесты вообще (теперь после сбора ВСЕХ)
        if not weighted_quests:
            await log_operation_async("No Quests", "No quests in ANY category", "WARNING")
            return None

        # Выбираем случайный квест с учётом весов
        new_quest = random.choice(weighted_quests)

        # Сохраняем прогресс
        progress_data = {
            "active_quest": new_quest["id"],
            "category": new_quest["_category"],
            "progress": 0,
            "completed": False,
            "last_update": datetime.now().date().isoformat(),
            "reward_claimed": False,
            "quest_file": new_quest.get("file", "unknown")
        }
        await save_user_progress(user_id, progress_data)

        return new_quest

    except Exception as e:
        await log_operation_async("Assign Quest Error", f"User {user_id}: {str(e)}", "CRITICAL")
        raise


async def update_quest_progress(user_id: int, quest_type: str, amount: int = 1) -> bool:
    """Обновление прогресса по активному квесту"""
    try:
        progress = await load_user_progress(user_id)
        if not progress or progress["completed"]:
            return False

        quest_category = progress["category"]
        quests = await load_quests(quest_category)
        quest = next(
            (q for q in quests if q["id"] == progress["active_quest"]),
            None
        )

        if not quest:
            return False

        # Для квеста на редких котов проверяем тип
        if quest_type == "cat_rare" and quest["id"] != "cat_quest_2":
            return False

        # Обновляем прогресс
        progress["progress"] += amount
        if progress["progress"] >= quest["target"]:
            progress["completed"] = True

        await save_user_progress(user_id, progress)
        return True

    except Exception as e:
        await log_operation_async(
            "Update Progress Error",
            f"User {user_id}: {str(e)}",
            "ERROR"
        )
        return False


async def claim_quest_reward(user_id: int, cursor=None, conn=None) -> Optional[Dict[str, int]]:
    """Выдача награды за выполненный квест"""
    try:
        progress = await load_user_progress(user_id)
        if not progress or not progress["completed"] or progress["reward_claimed"]:
            return None

        quest_category = progress["category"]
        quests = await load_quests(quest_category)
        quest = next((q for q in quests if q["id"] == progress["active_quest"]), None)

        if not quest:
            return None

        reward = quest.get("reward", {})

        # Выдача награды (ваш существующий код)
        # ...

        # После выдачи награды СБРАСЫВАЕМ прогресс
        progress["active_quest"] = None
        progress["progress"] = 0
        progress["completed"] = False
        progress["reward_claimed"] = False
        await save_user_progress(user_id, progress)

        return reward

    except Exception as e:
        await log_operation_async(
            "Claim Reward Error",
            f"User {user_id}: {str(e)}",
            "CRITICAL"
        )
        raise


async def quests_command(message: types.Message):
    try:
        user_id = message.from_user.id
        progress = await load_user_progress(user_id)

        # Принудительный сброс битых данных
        if progress and not progress.get("active_quest"):
            await save_user_progress(user_id, {})
            progress = None

        if not progress or not progress.get("active_quest"):
            quest = await assign_random_quest(user_id)  # Убрали категорию!
            if not quest:
                await message.answer("❌ Нет доступных квестов")
                return

            await message.answer(
                f"🎉 Новый квест ({quest.get('type', quest['_category'])})!\n\n"
                f"🏷 {quest['title']}\n"
                f"📝 {quest['description']}\n\n"
                f"Используйте /quests_progress для проверки статуса"
            )
            return

        # Если квест завершён, но награда не получена
        if progress["completed"] and not progress["reward_claimed"]:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(
                    "🎁 Получить награду",
                    callback_data=f"claim_reward:{user_id}"
                )
            )
            await message.answer(
                "У вас есть завершённый квест. Получите награду чтобы взять новый.",
                reply_markup=keyboard
            )
            return

        # Если есть активный незавершённый квест
        quests = await load_quests(progress["category"])
        current_quest = next(
            (q for q in quests if q["id"] == progress["active_quest"]),
            {"title": "Unknown", "description": "", "target": 1}
        )

        await message.answer(
            f"📌 Текущий квест ({progress['category']}):\n"
            f"🏷 {current_quest['title']}\n"
            f"📝 {current_quest['description']}\n"
            f"⏳ Прогресс: {progress['progress']}/{current_quest['target']}"
        )

    except Exception as e:
        await log_operation_async(
            "Quests Command Error",
            f"User {message.from_user.id}: {str(e)}",
            "CRITICAL"
        )
        await message.answer("⚠️ Произошла ошибка. Попробуйте позже.")


async def quests_progress_command(message: types.Message):
    """Обработчик команды /quests_progress"""
    try:
        user_id = message.from_user.id
        progress = await load_user_progress(user_id)

        if not progress:
            await message.answer("У вас нет активных квестов. Используйте /quests")
            return

        quests = await load_quests(progress["category"])
        current_quest = next(
            (q for q in quests if q["id"] == progress["active_quest"]),
            {"title": "Unknown", "description": "", "target": 1}
        )

        await message.answer(
            f"📊 Прогресс по квесту ({progress['category']}):\n"
            f"🏷 {current_quest['title']}\n"
            f"🔹 {progress['progress']}/{current_quest['target']}\n"
            f"📝 {current_quest['description']}\n\n"
            f"Статус: {'✅ Завершен' if progress['completed'] else '🟡 В процессе'}"
        )

    except Exception as e:
        await log_operation_async(
            "Quest Progress Error",
            f"User {message.from_user.id}: {str(e)}",
            "ERROR"
        )
        await message.answer("⚠️ Ошибка загрузки прогресса")


async def claim_reward_callback(callback: types.CallbackQuery):
    """Обработчик получения награды"""
    try:
        user_id = int(callback.data.split(":")[1])
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            reward = await claim_quest_reward(user_id, cursor=cursor, conn=conn)
            if not reward:
                await callback.answer("Награда уже получена или квест не завершен")
                return

            # Локализация названий наград
            reward_names = {
                "magic_coins": "🔮 Магические коины",
                "cat_coins": "🐱 котокоины",
                "note_coins": "🎵 Нотокоины",
                "points": "⭐ Очки"
            }

            reward_text = "\n".join(
                f"{reward_names.get(key, key)}: {value}"
                for key, value in reward.items()
            )

            await callback.message.edit_text(
                f"🎉 Награда получена!\n\n{reward_text}\n\n"
                f"Используйте /quests для нового квеста"
            )
            await callback.answer()
        finally:
            conn.close()
    except Exception as e:
        await log_operation_async("Reward Claim Error", f"User {callback.from_user.id}: {str(e)}", "CRITICAL")
        await callback.answer("⚠️ Ошибка выдачи награды")


async def send_logs_command(message: types.Message):
    """Отправка логов админу"""
    try:
        log_file = Path("logs/quests.log")
        archive_dir = Path("logs/archives")
        archives = []  # Инициализируем переменную заранее

        # Отправка текущего лога
        if log_file.exists():
            await message.bot.send_document(
                chat_id=message.chat.id,
                document=open(log_file, 'rb'),
                caption="📜 Актуальный лог"
            )

        # Отправка последнего архива (если есть)
        if archive_dir.exists():
            archives = sorted(archive_dir.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)

        if archives:  # Теперь переменная всегда определена
            await message.bot.send_document(
                chat_id=message.chat.id,
                document=open(archives[0], 'rb'),
                caption="🗄 Последний архив логов"
            )
        elif not log_file.exists():
            await message.answer("Логи не найдены")

    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
        await log_operation_async(
            "Log Send Error",
            f"Failed to send logs: {str(e)}",
            "CRITICAL"
        )

def register_quest_handlers(dp: Dispatcher):
    """Регистрация обработчиков"""
    dp.register_message_handler(quests_command, commands=["quests"])
    dp.register_message_handler(quests_progress_command, commands=["quests_progress"])
    dp.register_message_handler(send_logs_command, commands=["logs"], user_id=[6324881038])
    dp.register_callback_query_handler(
        claim_reward_callback,
        lambda c: c.data.startswith("claim_reward:")
    )