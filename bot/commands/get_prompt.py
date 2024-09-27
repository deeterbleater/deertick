async def get_prompt(ctx, agent_name: str):
    """Get the system prompt for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    agent = bot.agents[agent_name]
    await ctx.send(f"System prompt for agent {agent_name}:\n{agent.system_prompt}")