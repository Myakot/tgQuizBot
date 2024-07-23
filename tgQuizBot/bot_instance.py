from telebot import TeleBot
import tgQuizBot.config as config

bot = TeleBot(config.BOT_TOKEN)
# bot is initialized in a separate module to avoid circular importing, I'm bad at this lol
