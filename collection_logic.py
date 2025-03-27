import sqlite3
import json
import os
from data import cats

DB_PATH = os.path.join('..', 'users.db')
COLLECTION_FILE = 'collection.json'


def get_user_collection_data(user_id):
    """Получает данные коллекции пользователя из БД и сохраняет в JSON"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получаем информацию о пользователе
        cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        if not user_data:
            return None

        # Получаем карточки пользователя
        cursor.execute("""
            SELECT c.cat_id, c.rarity, c.points 
            FROM user_cards uc
            JOIN cards c ON uc.card_id = c.cat_id AND uc.user_id = c.user_id
            WHERE uc.user_id = ?
            ORDER BY 
                CASE c.rarity 
                    WHEN 'особый' THEN 0
                    WHEN 'хромотический' THEN 1
                    WHEN 'легендарный' THEN 2
                    WHEN 'мифический' THEN 3
                    WHEN 'эпический' THEN 4
                    WHEN 'сверхредкий' THEN 5
                    WHEN 'редкий' THEN 6
                    WHEN 'обычный' THEN 7
                END,
                c.points DESC
        """, (user_id,))

        user_cards = cursor.fetchall()

        # Формируем данные для коллекции
        collection_data = []
        for card in user_cards:
            cat = next((c for c in cats if c['id'] == str(card['cat_id'])), None)
            if cat:
                collection_data.append({
                    'photo': cat['photo'],
                    'catname': cat['catname'],
                    'rarity': card['rarity'],
                    'points': card['points'],
                    'catinfo': cat['catinfo']
                })

        # Сохраняем в JSON файл
        with open(COLLECTION_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'user_id': user_id,
                'username': user_data['username'],
                'collection': collection_data
            }, f, ensure_ascii=False, indent=4)

        return {
            'user_id': user_id,
            'username': user_data['username'],
            'collection': collection_data
        }

    except Exception as e:
        print(f"Error getting user collection: {e}")
        return None
    finally:
        if conn:
            conn.close()


def load_collection_from_json():
    """Загружает данные коллекции из JSON файла"""
    try:
        with open(COLLECTION_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


# Блок для ручного тестирования
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Использование: python collection_logic.py <user_id>")
        sys.exit(1)

    try:
        user_id = int(sys.argv[1])
        result = get_user_collection_data(user_id)

        if result:
            print(f"Коллекция пользователя {result['username']} (ID: {result['user_id']}):")
            print(f"Найдено карточек: {len(result['collection'])}")
            print(f"Данные сохранены в {COLLECTION_FILE}")

            # Выводим первые 3 карточки для примера
            print("\nПример карточек:")
            for i, card in enumerate(result['collection'][:3], 1):
                print(f"{i}. {card['catname']} ({card['rarity']}) - {card['points']} очков")
        else:
            print("Коллекция не найдена или пуста")

    except ValueError:
        print("Ошибка: user_id должен быть числом")
    except Exception as e:
        print(f"Ошибка при получении коллекции: {e}")