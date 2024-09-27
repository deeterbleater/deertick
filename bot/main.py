from bot.client import bot
from bot.commands import register_commands
from bot.config import config
from bot.events import register_event_handlers

if __name__ == "__main__":
    register_event_handlers(bot)
    register_commands(bot)
    bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))