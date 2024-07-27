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
            price TEXT,
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


def insert_user(telegram_id, telegram_nickname):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, telegram_nickname)
        VALUES (?, ?)
    ''', (telegram_id, telegram_nickname))
    conn.commit()
    conn.close()


def get_quizzes_from_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT theme, date, time, location, organizers, description, 
    price, id FROM quizzes'''
    )
    quizzes = cursor.fetchall()
    conn.close()
    return quizzes


def insert_quiz_into_db(quiz_details):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO quizzes (theme, date, time, location, organizers, description, price) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (quiz_details['theme'], quiz_details['date'], quiz_details['time'], quiz_details['location'],
                    quiz_details['organizers'], quiz_details['description'], quiz_details['price']))
    conn.commit()
    conn.close()


def get_quiz_details_by_theme(quiz_theme):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE theme=?", (quiz_theme,))
    quiz_details = cursor.fetchone()
    conn.close()
    return quiz_details


def rsvp_to_quiz(user_id, quiz_id, status='interested'):
    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Check if the RSVP already exists
        cursor.execute('SELECT id FROM rsvp WHERE user_id=? AND quiz_id=?', (user_id, quiz_id))
        if cursor.fetchone():
            ic('User already RSVPed to this quiz', user_id, quiz_id)
            return False  # RSVP already exists

        # Insert new RSVP
        cursor.execute('''
        INSERT INTO rsvp (user_id, quiz_id, status) VALUES (?, ?, ?)
        ''', (user_id, quiz_id, status))
        conn.commit()
        ic('RSVP successfully added')
        return True
    except Exception as e:
        ic('Failed to RSVP to quiz', e)
        return False
    finally:
        conn.close()


def get_rsvp_users_by_quiz_id(quiz_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Debugging: Check rsvp entries for the given quiz_id
    cursor.execute('SELECT * FROM rsvp WHERE quiz_id=?', (quiz_id,))
    rsvp_entries = cursor.fetchall()
    ic(rsvp_entries, 'RSVP entries for quiz_id')

    # Debugging: Check all user entries
    cursor.execute('SELECT * FROM users')
    user_entries = cursor.fetchall()
    ic(user_entries, 'All user entries')

    # Debugging: Check if user_id exists in users table
    cursor.execute('SELECT user_id FROM rsvp WHERE quiz_id=? AND user_id NOT IN (SELECT telegram_id FROM users)',
                   (quiz_id,))
    invalid_user_ids = cursor.fetchall()
    ic(invalid_user_ids, 'Invalid user_ids in rsvp')

    # Final query to get users' telegram_nickname
    cursor.execute('''
        SELECT users.telegram_nickname 
        FROM rsvp
        JOIN users ON rsvp.user_id = users.telegram_id
        WHERE rsvp.quiz_id=?
    ''', (quiz_id,))
    users = cursor.fetchall()
    ic(users, 'db function returning users')

    conn.close()
    return users


def quiz_exists(quiz_id):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM quizzes WHERE id=?', (quiz_id,))
        result = cursor.fetchone()
        return result is not None
    finally:
        conn.close()
