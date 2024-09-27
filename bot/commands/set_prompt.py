async def set_prompt(ctx, agent_name: str, *, prompt: str):
    """Set the system prompt for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.")
        return

    agent = bot.agents[agent_name]
    agent.system_prompt = prompt

    # Update the database
    async with bot.db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE agents
            SET system_prompt = $1
            WHERE bot_id = (SELECT id FROM bots WHERE bot_name = $2)
        ''', encode_data(prompt), agent_name)

    await ctx.send(f"System prompt updated for agent {agent_name}.")