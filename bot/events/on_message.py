from bot.client import bot
from bot.db.message import log_message
from bot.director import who_should_speak


async def on_message(message):
    is_bot = False
    if message.author == bot.user:
        is_bot = True

    await log_message(message, is_bot_message=is_bot)
    await bot.process_commands(message)

    # Only process messages not starting with the command prefix
    if not message.content.startswith(bot.command_prefix):
        await who_should_speak(message)