import requests
# from tgQuizBot.config import GROUP_CHAT_ID
from tgQuizBot.util.utils import ping_users
from tgQuizBot.bot_instance import bot
from tgQuizBot.db.database import (insert_quiz_into_db, delete_quiz_by_theme, get_rsvp_users_by_quiz_id, insert_user,
                                   get_quizzes_from_db, get_quiz_details_by_theme, rsvp_to_quiz, quiz_exists)
from telebot import types
from icecream import ic


# Example usage for pinging users:
# user_ids = [123, 456, 789]
# message = "Hello, users!"
# interval = 86400  # 1 day in seconds
# schedule_ping(user_ids, message, interval)

user_state = {}
user_pages = {}
user_quiz_data = {}
# Replace global variables with a better solution in the future


@bot.message_handler(commands=['help'])
def handle_help_command(message):
    help_text = """
    Список доступных команд:
    /addquiz - добавить новый квиз. Бот напишет вам в личные сообщения и попросит ввести 7 параметров квиза.
        /cancel - отменить процесс добавления квиза
    /deletequiz - удалить квиз по названию Темы
    /quizzes - показать все квизы
    /rsvp - зарегистрироваться на квиз. Использовать в формате /rsvp {номер квиза}
    /help - показать эту справку
    """
    bot.send_message(message.chat.id, help_text)
    ic('User requested help', message.from_user.first_name)


@bot.message_handler(commands=['cancel'])
def cancel_process(message):
    if message.from_user.id in user_state:
        del user_state[message.from_user.id]
        if message.from_user.id in user_quiz_data:
            del user_quiz_data[message.from_user.id]
        bot.send_message(message.from_user.id, "Процесс добавления квиза отменён.")
        ic('User canceled quiz adding', message.from_user.first_name)
    else:
        bot.send_message(message.from_user.id, "Нет активного процесса для отмены.")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    telegram_id = message.from_user.id
    telegram_nickname = message.from_user.username

    # Insert the user into the database
    insert_user(telegram_id, telegram_nickname)

    bot.reply_to(message, "Привет человекин!")


@bot.message_handler(commands=['addquiz'])
def handle_addquiz_command(message):
    bot.send_message(message.chat.id, "Пользователь {} добавляет новый квиз. Пожалуйста проверьте свои ЛС и "
                                      "предоставьте данные боту.".format(message.from_user.first_name))
    bot.send_message(message.from_user.id, "Пожалуйста пришлите мне Тему квиза.")
    user_state[message.from_user.id] = "AWAITING_QUIZ_THEME"
    user_quiz_data[message.from_user.id] = {}


@bot.message_handler(func=lambda message: message.chat.type == 'private' and message.from_user.id in user_state)
def receive_quiz_details(message):
    state = user_state[message.from_user.id]

    if state == "AWAITING_QUIZ_THEME":
        user_quiz_data[message.from_user.id]["theme"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Дату квиза.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_DATE"

    elif state == "AWAITING_QUIZ_DATE":
        user_quiz_data[message.from_user.id]["date"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Время квиза.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_TIME"

    elif state == "AWAITING_QUIZ_TIME":
        user_quiz_data[message.from_user.id]["time"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Локацию квиза.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_LOCATION"

    elif state == "AWAITING_QUIZ_LOCATION":
        user_quiz_data[message.from_user.id]["location"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Организаторов квиза.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_ORGANIZERS"

    elif state == "AWAITING_QUIZ_ORGANIZERS":
        user_quiz_data[message.from_user.id]["organizers"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Описание квиза.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_DESCRIPTION"

    elif state == "AWAITING_QUIZ_DESCRIPTION":
        user_quiz_data[message.from_user.id]["description"] = message.text.strip()
        bot.send_message(message.chat.id, "Пожалуйста пришлите мне Цену за человека.")
        user_state[message.from_user.id] = "AWAITING_QUIZ_PRICE"

    elif state == "AWAITING_QUIZ_PRICE":
        user_quiz_data[message.from_user.id]["price"] = message.text.strip()
        insert_quiz_into_db(user_quiz_data[message.from_user.id])
        del user_state[message.from_user.id]
        del user_quiz_data[message.from_user.id]
        bot.send_message(message.chat.id, "Квиз добавлен успешно!")
        ic('Quiz added, user state deleted')


@bot.message_handler(func=lambda message: message.chat.type == 'private' and user_state.get(
    message.from_user.id) == "AWAITING_QUIZ_DETAILS")
def receive_quiz_details(message):
    # Parse the quiz details
    details = message.text.split(';')
    if len(details) != 7:
        bot.send_message(message.chat.id, "Пожалуйста введите данные в правильном формате."
                                          "Если вы хотите отменить добавление квиза, напишите /cancel.")
        ic('Incorrect details format', details)
        return
    quiz_details = {
        "theme": details[0].strip(),
        "date": details[1].strip(),
        "time": details[2].strip(),
        "location": details[3].strip(),
        "organizers": details[4].strip(),
        "description": details[5].strip(),
        "price": details[6].strip()
    }
    insert_quiz_into_db(quiz_details)
    del user_state[message.from_user.id]
    bot.send_message(message.chat.id, "Квиз добавлен успешно!")
    ic('Quiz added, user state deleted')


@bot.message_handler(commands=['quizzes'])
def handle_quizzes_command(message):
    ic('User requested list of upcoming quizzes', message.from_user.first_name)
    quizzes = get_quizzes_from_db()
    markup = types.InlineKeyboardMarkup()
    displayed_quizzes = quizzes[:4]
    ic(f'Quizzes displayed: {displayed_quizzes}')

    if not quizzes:
        bot.send_message(message.chat.id, "Не найдено никаких квизов.")
        ic('No quizzes sent to user', message.from_user.first_name)
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
            markup.add(types.InlineKeyboardButton("Далее", callback_data="quizzes_next_1"))

    bot.send_message(message.chat.id, "Выберите квиз:", reply_markup=markup)
    ic('Quizzes sent to user', message.from_user.first_name)


@bot.message_handler(commands=['deletequiz'])
def handle_deletequiz_command(message):
    ic('User is trying to delete a quiz {message.text}', message.from_user.first_name)

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Пожалуйста назовите Тему квиза, чтобы его удалить.")
        return
    quiz_theme = args[1]

    # Perform the deletion
    if delete_quiz_by_theme(quiz_theme):
        bot.reply_to(message, f"Квиз '{quiz_theme}' успешно удалён.")
        ic(f'Quiz {quiz_theme} deleted successfully', message.from_user.first_name)
    else:
        bot.reply_to(message, "Не получилось удалить квиз. Возможно...")
        ic(f'Failed to delete quiz {quiz_theme}', message.from_user.first_name)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("quiz_"):
        quiz_theme = call.data.split("_")[1]
        # Fetch the full details of the quiz
        quiz_details = get_quiz_details_by_theme(quiz_theme)
        if quiz_details:
            rsvp_users = get_rsvp_users_by_quiz_id(quiz_details[7])  # The 8th element is the quiz ID
            rsvp_users_list = "\n".join([str(user[0]) for user in rsvp_users])  # Convert user nicknames to strings
            ic(rsvp_users_list, "converted user nicknames to strings", rsvp_users, 'rsvp_users listed!')
            details_message = (f"ID-квиза: {quiz_details[7]}\nТема: {quiz_details[0]}\nДата: {quiz_details[1]}\n"
                               f"Время: {quiz_details[2]}\nЛокация: {quiz_details[3]}\n"
                               f"Организаторы: {quiz_details[4]}\nОписание: {quiz_details[5]}\n"
                               f"Цена за человека (рубли): {quiz_details[6]}\n"
                               f"Записавшиеся пользователи:\n{rsvp_users_list}")
            bot.send_message(call.message.chat.id, details_message)
            ic('Quiz details sent to user', call.from_user.first_name, rsvp_users_list)
        else:
            ic('Quiz details not found', call.from_user.first_name)
            bot.send_message(call.message.chat.id, "Прошу прощения, я не смог найти детали этого квиза.")

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
        markup.add(types.InlineKeyboardButton("Далее", callback_data="quizzes_next_" + str(page_num + 1)))
    if page_num > 1:
        markup.add(types.InlineKeyboardButton("Назад", callback_data="quizzes_prev_" + str(page_num - 1)))

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите квиз:",
                          reply_markup=markup)


def get_quizzes_page(page_num, page_size=4):
    quizzes = get_quizzes_from_db()
    # Calculate start and end index
    start_page = (page_num - 1) * page_size
    end_page = start_page + page_size
    ic(f'page_num: {page_num}, start_page: {start_page}, end_page: {end_page}')
    return quizzes[start_page:end_page]


def extract_quiz_id_from_message(message):
    ic(f'Extracting quiz ID from message: {message.text}')
    text = message.text.strip()
    parts = text.split()

    # Check if the message is formatted correctly
    # add isdigit() check for non-numeric IDs
    if len(parts) == 2 and parts[0] == '/rsvp':
        # Return the quiz ID part
        ic(f'Extracted quiz ID: {parts[1]}')
        return parts[1]
    else:
        ic('Quiz ID not found in message: {message.text}')
        return None


@bot.message_handler(commands=['rsvp'])
def rsvp(message):
    user_id = message.from_user.id
    quiz_id = extract_quiz_id_from_message(message)
    ic(f'User {user_id} rsvp to quiz {quiz_id}')

    if not quiz_id or not quiz_exists(quiz_id):
        bot.reply_to(message, "Квиз с указанным ID не существует.")
        ic(f'User {user_id} tried to rsvp to non-existent quiz {quiz_id}')
        return

    if rsvp_to_quiz(user_id, quiz_id):
        bot.reply_to(message, "У вас получилось успешно привязаться к квизу!")
        ic(f'User {user_id} rsvp to quiz {quiz_id} successful', message.from_user.first_name)
    else:
        bot.reply_to(message, "Случилась ошибка, возможно вы уже были привязаны к этому квизу.")
        ic(f'User {user_id} rsvp to quiz {quiz_id} failed', message.from_user.first_name)


if __name__ == "__main__":
    while True:
        try:
            bot.polling(timeout=40)  # Increase timeout as needed
        except requests.exceptions.ReadTimeout:
            print("ReadTimeout occurred, retrying...")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
