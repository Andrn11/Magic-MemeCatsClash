import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from dotenv import load_dotenv
import json
from MelodyGame import register_melody_handlers
from advanced_logger import start_logger, log_operation_async
from dp_handlers import register_handlers
from quests import register_quest_handlers
from register import register_register_handlers
from urprofil import register_urprofil_handlers

load_dotenv()

with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

API_TOKEN = os.getenv("API_TOKEN")

if API_TOKEN is None:
    raise ValueError("Токен API не установлен. Проверьте файл .env.")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
register_quest_handlers(dp)
register_register_handlers(dp)
register_urprofil_handlers(dp)
logging.info("Регистрация обработчиков для /profil")
register_melody_handlers(dp)
logging.info("Регистрация обработчиков для /melody")
register_handlers(dp)
logging.info("Регистрация обработчиков из commands")


async def on_startup(dp):
    start_logger(dp)



async def on_error(update: types.Update, error: Exception):
    await log_operation_async(
        "Global Error",
        f"Error in {update}: {str(error)}",
        "CRITICAL"
    )

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)