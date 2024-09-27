async def get_param(ctx, agent_name: str, param: str):
    """Get the value of a parameter for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    agent = bot.agents[agent_name]
    try:
        value = getattr(agent, param)
        await ctx.send(f"Parameter {param} for agent {agent_name} is set to: {value}")
    except AttributeError:
        await send_error_message(ctx, f"Invalid parameter: {param}", agent_name)