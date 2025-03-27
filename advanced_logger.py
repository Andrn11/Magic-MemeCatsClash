import os

import aiofiles
import zipfile
from datetime import datetime
import asyncio
from pathlib import Path

from aiogram import Dispatcher, types

# Настройки
LOG_DIR = "logs"
ARCHIVE_DIR = "logs/archives"
MIN_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50 МБ
ARCHIVE_INTERVAL = 600
ROTATION_HOURS = 2

# Создаем папки при старте
Path(LOG_DIR).mkdir(exist_ok=True)
Path(ARCHIVE_DIR).mkdir(exist_ok=True)


async def log_operation_async(operation: str, details: str, level: str = "INFO"):
    """Асинхронное логирование (без изменений)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level.upper()}: {operation}\nДетали: {details}\n\n"

    try:
        async with aiofiles.open(f"{LOG_DIR}/complex_operations.log", mode='a', encoding='utf-8') as f:
            await f.write(log_entry)
    except Exception as e:
        print(f"⚠️ Failed to log: {e}")


async def archive_file(log_file: Path):
    """Архивирует один лог-файл"""
    try:
        archive_name = f"{ARCHIVE_DIR}/{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        async with aiofiles.open(log_file, mode='rb') as f:
            content = await f.read()

        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(log_file.name, content)

        async with aiofiles.open(log_file, mode='wb') as f:
            await f.write(b"")

        await log_operation_async("Log Archive", f"Archived {log_file.name}", "INFO")
        return True
    except Exception as e:
        await log_operation_async("Archive Error", f"{log_file.name}: {str(e)}", "ERROR")
        return False


async def archive_large_logs():
    """Архивирует все лог-файлы > 50 МБ с проверкой ошибок"""
    archived = 0
    log_dir = Path("logs")

    # Создаем папку для архивов
    (log_dir / "archives").mkdir(exist_ok=True)

    for log_file in log_dir.glob("*.log"):
        try:
            # Явная проверка существования
            if not log_file.exists():
                await log_operation_async("File Check", f"{log_file.name} - не существует", "WARNING")
                continue

            # Альтернативный способ проверки размера
            file_size = os.path.getsize(log_file)
            size_mb = file_size / (1024 * 1024)

            await log_operation_async("File Check",
                                      f"{log_file.name} - {size_mb:.2f} MB (реальный размер)",
                                      "DEBUG")

            if file_size > MIN_ARCHIVE_SIZE:
                # Архивируем с новым именем
                archive_path = log_dir / "archives" / f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

                # Чтение через стандартный open (на случай проблем с aiofiles)
                with open(log_file, 'rb') as f:
                    content = f.read()

                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.writestr(log_file.name, content)

                # Очистка файла
                with open(log_file, 'wb') as f:
                    f.write(b"")

                archived += 1
                await log_operation_async("Archive Success",
                                          f"{log_file.name} ({size_mb:.2f} MB) → {archive_path}",
                                          "INFO")

        except Exception as e:
            await log_operation_async("Archive Error",
                                      f"{log_file.name}: {type(e).__name__} - {str(e)}",
                                      "ERROR")

    return archived


async def auto_archive_task():
    """Фоновая задача для автоматической архивации"""
    while True:
        try:
            archived = await archive_large_logs()
            if archived > 0:
                await log_operation_async("Auto Archive", f"Archived {archived} files", "DEBUG")
        except Exception as e:
            await log_operation_async("Auto Archive Error", str(e), "ERROR")
        await asyncio.sleep(ARCHIVE_INTERVAL)

async def rotation_task_async():
    """Фоновая проверка (без изменений)"""
    while True:
        await archive_large_logs()
        await asyncio.sleep(ROTATION_HOURS * 3600)


async def clean_old_archives(max_files=5):
    """Очистка архивов (без изменений)"""
    try:
        archives = sorted(Path(ARCHIVE_DIR).glob("*.zip"), key=lambda f: f.stat().st_mtime)
        if len(archives) > max_files:
            for old_archive in archives[:-max_files]:
                old_archive.unlink()
    except Exception as e:
        await log_operation_async("Archive Clean Error", str(e), "ERROR")


async def archive_command(message: types.Message):
    """Ручная архивация логов для админов"""
    try:
        if message.from_user.id not in [6324881038]:  # Ваш ID
            await message.answer("⛔ У вас нет прав на эту команду")
            return

        await message.answer("🔄 Начинаю архивацию логов...")
        archived = await archive_large_logs()
        await message.answer(f"✅ Заархивировано {archived} файлов")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {str(e)}")
        await log_operation_async("Archive Command Error", str(e), "ERROR")

def start_logger(app):
    @app.on_startup
    async def startup():
        asyncio.create_task(auto_archive_task())  # Запускаем фоновую задачу
        await log_operation_async("System", "Auto-archive task started", "INFO")

def register_quest_handlers(dp: Dispatcher):
    """Регистрация обработчиков"""
    # ... существующие обработчики ...
    dp.register_message_handler(archive_command, commands=["archive"], user_id=[6324881038])