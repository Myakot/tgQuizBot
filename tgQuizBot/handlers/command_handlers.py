from tgQuizBot.config import GROUP_CHAT_ID
from tgQuizBot.bot_instance import bot
from tgQuizBot.db.database import (insert_quiz_into_db, delete_quiz_by_theme,
                                   get_quizzes_from_db, get_quiz_details_by_theme)
from tgQuizBot.util.auth import is_user_authorized
from telebot import types
from icecream import ic


user_state = {}
user_pages = {}
# Replace global variables with a better solution in the future


@bot.message_handler(commands=['addquiz'])
def handle_addquiz_command(message):
    allowed_group_chat_id = int(GROUP_CHAT_ID)
    # Change != to == on production!!! "Dev" mode
    # if message.chat.type == "group" and message.chat.id != allowed_group_chat_id:
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
        bot.send_message(message.chat.id, "Please send this command in the specified group chat.")


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
        "theme": details[1].strip(),
        "date": details[2].strip(),
        "time": details[3].strip(),
        "location": details[4].strip(),
        "organizers": details[5].strip(),
        "description": details[6].strip(),
        "registration_link": details[7].strip()
        # add quiz_id field to sort by later, not manually inputted, just appended
    }
    insert_quiz_into_db(quiz_details)
    del user_state[message.from_user.id]
    bot.send_message(message.chat.id, "Quiz added successfully!")
    ic('Quiz added, user state deleted')


@bot.message_handler(commands=['quizzes'])
def handle_quizzes_command(message):
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


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("quiz_"):
        quiz_theme = call.data.split("_")[1]
        # Fetch the full details of the quiz
        quiz_details = get_quiz_details_by_theme(quiz_theme)
        if quiz_details:
            # Assuming quiz_details is a tuple in the order of (theme, date, time, location, organizers, description,
            # registration_link)
            details_message = (f"You selected: {quiz_details[0]}\nTheme: {quiz_details[1]}\nDate: {quiz_details[2]}\n"
                               f"Time: {quiz_details[3]}\nLocation: {quiz_details[4]}\n"
                               f"Organizers: {quiz_details[5]}\nDescription: {quiz_details[6]}\n"
                               f"Registration Link: {quiz_details[7]}")
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


def get_quizzes_page(page_num, page_size=4):
    quizzes = get_quizzes_from_db()
    # Calculate start and end index
    start_page = (page_num - 1) * page_size
    end_page = start_page + page_size
    ic(f'page_num: {page_num}, start_page: {start_page}, end_page: {end_page}')
    return quizzes[start_page:end_page]


def rsvp(message):
    # Similar to add_quiz(message) for updating the table
    pass
