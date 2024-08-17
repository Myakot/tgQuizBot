import schedule
import time
import threading
from tgQuizBot.bot_instance import bot

def ping_users(user_ids, message):
    for user_id in user_ids:
        bot.send_message(user_id, message)


def schedule_ping(user_ids, message, interval):
    """
    Schedules the ping_users function to run at a specific time interval.

    Args:
        user_ids (list): A list of user IDs.
        message (str): The message to be sent.
        interval (int): The time interval in seconds.
    """
    def job():
        ping_users(user_ids, message)

    schedule.every(interval).seconds.do(job) # Can be changed to minutes/hours/etc...

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    threading.Thread(target=run_schedule).start()
