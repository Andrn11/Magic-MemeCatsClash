from aiogram import types, Dispatcher
from database import get_db_connection, conn, cursor


# Глобальный словарь для временного хранения данных
temp_data = {}


async def register_start(message: types.Message):
    user_id = message.from_user.id


    cursor.execute("SELECT * FROM site_name_password WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        await message.answer("❌ Вы уже зарегистрированы!")
        return

    # Запоминаем, что пользователь начал регистрацию
    temp_data[user_id] = {"step": "waiting_for_name"}
    await message.answer("📝 Введите имя пользователя (оно будет использоваться на сайте):")


async def process_name(message: types.Message):
    user_id = message.from_user.id
    username = message.text.strip()

    # Проверки имени
    if len(username) < 3 or len(username) > 20:
        await message.answer("❌ Имя должно быть от 3 до 20 символов!")
        return

    cursor.execute("SELECT * FROM site_name_password WHERE username = ?", (username,))
    if cursor.fetchone():
        await message.answer("❌ Это имя уже занято! Попробуйте другое.")
        return


    temp_data[user_id] = {
        "step": "waiting_for_password",
        "username": username
    }
    await message.answer("🔑 Теперь придумайте пароль (от 5 до 32 символов):")

async def process_password(message: types.Message):
    user_id = message.from_user.id
    password = message.text.strip()


    if len(password) < 5 or len(password) > 32:
        await message.answer("❌ Пароль должен быть от 5 до 32 символов!")
        return


    username = temp_data[user_id]["username"]


    cursor.execute(
        "INSERT INTO site_name_password (user_id, username, password) VALUES (?, ?, ?)",
        (user_id, username, password)
    )
    conn.commit()


    del temp_data[user_id]

    await message.answer(
        f"✅ Регистрация завершена!\n\n"
        f"Логин: <code>{username}</code>\n"
        f"Пароль: <code>{password}</code>\n\n"
        "Теперь вы можете войти на сайте!",
        parse_mode="HTML"
    )

def register_register_handlers(dp: Dispatcher):
    dp.register_message_handler(register_start, commands=['register'])
    dp.register_message_handler(process_name, lambda message: temp_data.get(message.from_user.id, {}).get("step") == "waiting_for_name")
    dp.register_message_handler(process_password, lambda message: temp_data.get(message.from_user.id, {}).get("step") == "waiting_for_password")