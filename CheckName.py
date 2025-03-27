from aiogram import types
from Start import process_name
from database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()


async def check_name(message: types.Message):
    if message.text is None or message.text.startswith('/'):
        return True

    user_id = message.from_user.id

    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if result and result[0]:
        return True
    else:
        await message.answer(
            "У вас еще нет имени. Пожалуйста, введите команду /name, чтобы указать ваше имя."
        )
        return False