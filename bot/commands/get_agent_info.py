from bot.client import bot
from bot.error import send_error_message


async def get_agent_info(ctx, agent_name: str):
    """Get the information for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    agent = bot.agents[agent_name]
    info = f"Agent {agent_name} info:\n{agent}"

    # Split the info into chunks of 1900 characters (leaving room for code block formatting)
    chunks = [info[i:i + 1900] for i in range(0, len(info), 1900)]

    for chunk in chunks:
        await ctx.send(f"```{chunk}```")