from bot.client import bot


async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Loaded agents: {", ".join(bot.agents.keys())}')