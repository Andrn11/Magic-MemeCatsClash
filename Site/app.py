from flask import Flask, request, render_template, redirect, url_for, session, flash
import sqlite3
import os
from collection_logic import get_user_collection_data

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your-secret-key-here'
DB_PATH = os.path.join('..', 'users.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM site_name_password WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Неверный логин или пароль')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('home.html', username=session['username'])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/user_collection/<int:user_id>')
def user_collection(user_id):
    # Получаем данные коллекции
    collection_data = get_user_collection_data(user_id)

    if not collection_data:
        return render_template('error.html', error_message='Пользователь не найден или коллекция пуста')

    return render_template('user_collection.html',
                           collection=collection_data['collection'],
                           username=collection_data['username'],
                           user_id=user_id)


@app.route('/search_user', methods=['GET', 'POST'])
def search_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        search_query = request.form['search_query']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Search by username or user_id
        if search_query.isdigit():
            cursor.execute(
                "SELECT user_id, username FROM users WHERE user_id = ?",
                (int(search_query),)
            )
        else:
            cursor.execute(
                "SELECT user_id, username FROM users WHERE username LIKE ?",
                (f'%{search_query}%',)
            )

        users = cursor.fetchall()
        conn.close()

        return render_template('search_results.html', users=users)

    return render_template('search_user.html')


if __name__ == '__main__':
    app.run(debug=True)