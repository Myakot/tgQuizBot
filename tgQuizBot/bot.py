from tgQuizBot.bot_instance import bot
from handlers import command_handlers


# Setup command handlers
bot.add_message_handler(command_handlers.handle_addquiz_command)
bot.add_message_handler(command_handlers.handle_deletequiz_command)
bot.add_message_handler(command_handlers.handle_quizzes_command)
# Add other handlers...

if __name__ == "__main__":
    bot.polling()
