import telebot
from dotenv import load_dotenv
import os
import sqlite3
from icecream import ic
from telebot import types

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
user_state = {}
user_pages = {}
# Replace global variables with a better solution before prod
ic('Starting...')


# Commands to add? upcoming, rsvp, leaderboard, reminders, give user access to add/delete
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
ic('Database initialized')


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
    # Change != to == on production!!! "Dev" mode
    if message.chat.type != "group":
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


# Right now adding quiz info isn't fluent, it's a chore. Need some kind of parser to get the info from the user
# in a better manner. For now, it'll do.
# Needs a command to cancel the process, otherwise unless you put something in - bot will keep asking
@bot.message_handler(func=lambda message: message.chat.type == 'private' and user_state.get(
    message.from_user.id) == "AWAITING_QUIZ_DETAILS")
def receive_quiz_details(message):
    # Parse the quiz details
    details = message.text.split(';')
    if len(details) != 7:
        bot.send_message(message.chat.id, "Please follow the correct format and send all required details.")
        ic('Incorrect details format')
        return
    quiz_details = {
        "theme": details[0].strip(),
        "date": details[1].strip(),
        "time": details[2].strip(),
        "location": details[3].strip(),
        "organizers": details[4].strip(),
        "description": details[5].strip(),
        "registration_link": details[6].strip()
        # add quiz_id field to sort by later, not manually inputted, just appended
    }
    insert_quiz_into_db(quiz_details)
    del user_state[message.from_user.id]
    bot.send_message(message.chat.id, "Quiz added successfully!")
    ic('Quiz added, user state deleted')


def get_quizzes_from_db():
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT theme, date, time, location, organizers, description, registration_link FROM quizzes''')
    quizzes = cursor.fetchall()
    conn.close()
    return quizzes


def get_quizzes_page(page_num, page_size=4):
    quizzes = get_quizzes_from_db()
    # Calculate start and end index
    start_page = (page_num - 1) * page_size
    end_page = start_page + page_size
    ic(f'page_num: {page_num}, start_page: {start_page}, end_page: {end_page}')
    return quizzes[start_page:end_page]


def update_quiz_message(call, quizzes):
    markup = types.InlineKeyboardMarkup()
    for quiz in quizzes:
        button = types.InlineKeyboardButton(quiz[0], callback_data=f"quiz_{quiz[0]}")
        markup.add(button)

    # Add pagination buttons
    page_num = user_pages.get(call.from_user.id, 1)
    if len(get_quizzes_from_db()) > page_num * 4:
        markup.add(types.InlineKeyboardButton("Next", callback_data="quizzes_next_" + str(page_num + 1)))
    if page_num > 1:
        markup.add(types.InlineKeyboardButton("Previous", callback_data="quizzes_prev_" + str(page_num - 1)))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Select a quiz:",
                          reply_markup=markup)


# Before release have to change this so only Quiz name would be displayed initially.
# Clicking on a name button would show the rest of the info in a message
# Check if it's possible to send this message as "silent" and most messages from this bot, barring reminders
# Need to fix pagination - first time it shows - it shows all quizzes until a button is pressed

@bot.message_handler(commands=['quizzes'])
def send_quizzes(message):
    ic('User requested list of upcoming quizzes')
    quizzes = get_quizzes_from_db()
    markup = types.InlineKeyboardMarkup()
    displayed_quizzes = quizzes[:4]
    ic(f'Quizzes displayed: {displayed_quizzes}')

    if not quizzes:
        bot.send_message(message.chat.id, "No quizzes found.")
        ic('No quizzes sent to user')
        return

    # Format the message
    quizzes_message = "Here are the upcoming quizzes:\n\n"
    for quiz in quizzes:
        # Each button text is the quiz theme, callback data could be quiz id or theme
        button = types.InlineKeyboardButton(quiz[0], callback_data=f"quiz_{quiz[0]}")
        markup.add(button)

        # Pagination buttons
        if len(quizzes) > 4:
            ic('Quizzes more than 4, pagination implemented')
            markup.add(types.InlineKeyboardButton("Next", callback_data="quizzes_next_1"))

    bot.send_message(message.chat.id, "Select a quiz:", reply_markup=markup)
    ic('Quizzes sent to user')


def get_quiz_details_by_theme(quiz_theme):
    # need to implement the actual database query here.
    # For example:
    conn = sqlite3.connect('quiz.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE theme=?", (quiz_theme,))
    quiz_details = cursor.fetchone()
    conn.close()
    return quiz_details


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("quiz_"):
        quiz_theme = call.data.split("_")[1]
        # Fetch the full details of the quiz
        quiz_details = get_quiz_details_by_theme(quiz_theme)
        if quiz_details:
            # Assuming quiz_details is a tuple in the order of (theme, date, time, location, organizers, description,
            # registration_link)
            details_message = f"You selected: {quiz_details[0]}\nDate: {quiz_details[1]}\nTime: {quiz_details[2]}\nLocation: {quiz_details[3]}\nOrganizers: {quiz_details[4]}\nDescription: {quiz_details[5]}\nRegistration Link: {quiz_details[6]}"
            bot.send_message(call.message.chat.id, details_message)
            ic('Quiz details sent to user')
        else:
            ic('Quiz details not found')
            bot.send_message(call.message.chat.id, "Sorry, I couldn't find details for the selected quiz.")
    elif "quizzes_next_" in call.data or "quizzes_prev_" in call.data:
        direction, page_num = call.data.split("_")[1:]
        page_num = int(page_num)
        user_pages[call.from_user.id] = page_num

        quizzes = get_quizzes_page(page_num)
        update_quiz_message(call, quizzes)


@bot.message_handler(commands=['deletequiz'])
def handle_deletequiz_command(message):
    ic('User is trying to delete a quiz {message.text}')
    # Check if the user is authorized to delete quizzes
    if not is_user_authorized(message.from_user.id):
        ic('User no access tried to delete quizzes')
        bot.reply_to(message, "You are not authorized to delete quizzes.")
        return

    # Assuming the command format is "/deletequiz theme"
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Please specify the quiz theme to delete.")
        return
    quiz_theme = args[1]

    # Perform the deletion
    if delete_quiz_by_theme(quiz_theme):
        bot.reply_to(message, f"Quiz '{quiz_theme}' deleted successfully.")
    else:
        bot.reply_to(message, "Failed to delete the quiz. It might not exist.")


def delete_quiz_by_theme(quiz_theme):
    try:
        conn = sqlite3.connect('quiz.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quizzes WHERE theme=?", (quiz_theme,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting quiz: {e}")
        return False


def is_user_authorized(user_id):
    """Check if the given user_id is authorized to delete quizzes."""
    # Add logic here.
    return True


def rsvp(message):
    # Similar to add_quiz(message) for updating the table
    pass


def reminders(message):
    # have to be scheduled tasks that are checking for date-time and send messages to the group chat,
    # tagging everyone that rsvp'ed
    pass


bot.polling(non_stop=True)

#TODO
# Add reminders
# Add rsvp
# Add leaderboard
# Add upcoming
# Add list upcoming
# Decide where to deploy - Heroku?
# plan to cancel RSVPs
# admin features? Or just manually reset bot if needed
