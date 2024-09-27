import discord
from discord.app_commands import commands

from bot.db.agent import load_agents_from_db
from bot.db.pool import create_pool
from bot.db.tables import create_tables


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = None
        self.agents = {}

    async def setup_hook(self):
        self.db_pool = await create_pool()
        await create_tables(self.db_pool)
        self.agents = await load_agents_from_db(self.db_pool)
        print(f"Loaded {len(self.agents)} agents from the database.")


intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(command_prefix='!', intents=intents)
