async def continue_conversation(ctx):
    """Continue the conversation with the last agent that spoke in the channel."""
    cursor = bot.db_connection.cursor()
    cursor.execute("""
        SELECT nickname FROM messages
        WHERE channel_id = %s AND is_bot = TRUE
        ORDER BY timestamp DESC
        LIMIT 1
    """, (ctx.channel.id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        agent_name = result[0]
        if agent_name not in bot.agents:
            await ctx.send(f"The last speaking agent '{agent_name}' no longer exists.")
            return
    else:
        await ctx.send("No previous bot message found in this channel.")
        return

    agent = bot.agents[agent_name]

    # Get the context window of previous messages
    async for message in ctx.channel.history(limit=10):
        if message.author == bot.user and message.content.startswith(f"{agent_name}:"):
            context = message.content.split(": ", 1)[1]
            break
    else:
        context = ""

    # Send "continue" prompt to the agent
    response = agent.poke(f"{context}\nUser: !continue")
    await ctx.send(f"{agent_name}: {response}")
