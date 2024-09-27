from bot.client import bot


async def list_agents(ctx):
    """List all current agents."""
    if not bot.agents:
        await ctx.send("There are no agents currently available.")
    else:
        agent_list = "\n".join(f"- {name}" for name in bot.agents.keys())
        await ctx.send(f"Current agents:\n{agent_list}")