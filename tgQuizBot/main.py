import telebot
from telebot import types
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}


# Commands to add? addquiz, upcoming, rsvp, leaderboard, list upcoming quizzes, reminders, deletequiz
# When will reminders be used? Possible to set up? A day or 2?
# Needs functionality to change quizz time/date/location if plans have changed


def init_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()

    # Create the Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme TEXT,
            date TEXT,
            time TEXT,
            location TEXT,
            organizers TEXT,
            description TEXT,
            registration_link TEXT
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


def insert_quiz_into_db(quiz_details):
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO quizzes (theme, date, time, location, organizers, description, registration_link) 
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (quiz_details['theme'], quiz_details['date'], quiz_details['time'], quiz_details['location'],
                    quiz_details['organizers'], quiz_details['description'], quiz_details['registration_link']))
    conn.commit()
    conn.close()


@bot.message_handler(commands=['addquiz'])
def handle_addquiz_command(message):
    if message.chat.type == "group":
        # Inform the group
        bot.send_message(message.chat.id, "A new quiz is being added by {}. Please check your private messages to "
                                          "provide the details.".format(message.from_user.first_name))
        # Prompt the user in private
        bot.send_message(message.from_user.id, "Please send me the quiz details in the following format: Theme; Date; "
                                               "Time; Location; Organizers; Description; Registration Link")
        # Set the user's state to expecting quiz details
        user_state[message.from_user.id] = "AWAITING_QUIZ_DETAILS"
    else:
        # Inform the user
        bot.send_message(message.chat.id, "Please send this command in the group chat.")


@bot.message_handler(func=lambda message: message.chat.type == 'private' and user_state.get(message.from_user.id) == "AWAITING_QUIZ_DETAILS")
def receive_quiz_details(message):
    # Parse the quiz details
    details = message.text.split(';')
    if len(details) != 7:
        bot.send_message(message.chat.id, "Please follow the correct format and send all required details.")
        return
    quiz_details = {
        "theme": details[0].strip(),
        "date": details[1].strip(),
        "time": details[2].strip(),
        "location": details[3].strip(),
        "organizers": details[4].strip(),
        "description": details[5].strip(),
        "registration_link": details[6].strip()
    }
    # Insert into DB
    insert_quiz_into_db(quiz_details)
    # Reset user state
    del user_state[message.from_user.id]
    # Confirm to the user
    bot.send_message(message.chat.id, "Quiz added successfully!")


def rsvp(message):
    # Similar to add_quiz(message) for updating the table
    pass


def reminders(message):
    # have to be scheduled tasks that are checking for date-time and send messages to the group chat,
    # tagging everyone that rsvp'ed
    pass


@bot.message_handler(commands=['start'])
def start(message):
    pass


bot.polling(non_stop=True)

#TODO
# Add reminders
# Add rsvp
# Add leaderboard
# Add upcoming
# Add list upcoming
# Decide where to deploy - Heroku?
# Add printf's to errorhandle
# plan to cancel RSVPs
# admin features? Or just manually reset bot if needed
