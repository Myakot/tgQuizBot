import telebot
from telebot import types
from dotenv import load_dotenv
import os
import sqlite3

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


# Commands to add? addquiz, upcoming, rsvp, leaderboard, list upcoming quizzes, reminders

# Plan a DB schema to store quizzes and RSVPs. Need table for users // for quizzes // for rsvp user-quiz relationship
# When will reminders be used? Possible to set up? A day or 2?


# Init DB needs to be called at the start of the bot for tables to be set up
def init_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date_time TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvp (
            user_id INTEGER,
            quiz_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES players(id),
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
        )
    ''')
    conn.commit()
    conn.close()


@bot.message_handler(commands=['addquiz'])
def add_quiz(message):
    # Simplistic interaction, will figure out a proper one later
    # For simplicity, let's assume the message is formatted as "/addquiz title; datetime"
    details = message.text.split(' ', 1)[1]  # To remove the command and split the rest
    title, date_time = details.split(';')
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO quizzes (title, date_time) VALUES (?, ?)', (title.strip(), date_time.strip()))
    conn.commit()
    conn.close()
    bot.reply_to(message, "Quiz added successfully!")


@bot.message_handler(commands=['addquiz'])
def rsvp(message):
    # Similar to add_quiz(message) for updating the table
    pass


def reminders(message):
    # have to be scheduled tasks that are checking for date-time and send messages to the group chat,
    # tagging everyone that rsvp'ed
    pass


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Hello, ' + message.from_user.first_name)
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Play', callback_data='play')
    btn2 = types.InlineKeyboardButton(text='Help', callback_data='help')
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, 'Choose', reply_markup=markup)


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
