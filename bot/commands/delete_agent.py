async def delete_agent(ctx, agent_name: str):
    """Delete an existing agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    del bot.agents[agent_name]
    await ctx.send(f"Agent {agent_name} deleted.")