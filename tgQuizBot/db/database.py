import sqlite3
from icecream import ic


def connect_db():
    return sqlite3.connect('quiz.db')


def init_db():
    conn = connect_db()
    cursor = conn.cursor()

    # Create the Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            theme TEXT,
            date TEXT,
            time TEXT,
            location TEXT,
            organizers TEXT,
            description TEXT,
            registration_link TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
    ''')

    # Create the Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id TEXT UNIQUE,
            telegram_nickname TEXT
        )
    ''')

    # Create the RSVP table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quiz_id INTEGER,
            status TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
        )
    ''')

    conn.commit()
    conn.close()


# Call init_db to initialize the database and create the tables
init_db()
ic('Database initialized')


def delete_quiz_by_theme(quiz_theme):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quizzes WHERE theme=?", (quiz_theme,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        ic('Failed to delete quiz', e)
        return False


def get_quizzes_from_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT theme, date, time, location, organizers, description, 
    registration_link, id FROM quizzes'''
    )
    quizzes = cursor.fetchall()
    conn.close()
    return quizzes


def insert_quiz_into_db(quiz_details):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO quizzes (theme, date, time, location, organizers, description, registration_link) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (quiz_details['theme'], quiz_details['date'], quiz_details['time'], quiz_details['location'],
                    quiz_details['organizers'], quiz_details['description'], quiz_details['registration_link']))
    conn.commit()
    conn.close()


def get_quiz_details_by_theme(quiz_theme):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE theme=?", (quiz_theme,))
    quiz_details = cursor.fetchone()
    conn.close()
    return quiz_details
