async def talk(ctx, agent_name: str, *, message: str):
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist. Create it first with !create_agent.",
                                 "System")
        return

    agent = bot.agents[agent_name]

    # Check if the message is a reply
    replied_message = None
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    async with bot.db_pool.acquire() as conn:
        context_messages = await conn.fetch('''
            SELECT username, content, is_bot
            FROM messages
            WHERE channel_id = $1
            ORDER BY timestamp DESC
            LIMIT 50
        ''', ctx.channel.id)

    context = "\n".join([f"{msg['username']}: {decode_data(msg['content'])}" for msg in reversed(context_messages)])

    # If it's a reply, add the replied message to the context
    if replied_message:
        context += f"\n[Replied to {replied_message.author.name}: {replied_message.content}]"

    context += f"\n{ctx.author.name}: {message}"

    # Use typing() context manager to show typing indicator
    async with ctx.typing():
        # Simulate processing time (you can remove this in production)
        await asyncio.sleep(2)

        response = agent.poke(context)

    await log_message(discord.Object(id=ctx.channel.id), is_bot_message=True, bot_content=response)

    chunks = [response[i:i + 1800] for i in range(0, len(response), 1800)]

    for chunk in chunks:
        await ctx.send(f"{agent_name}: ```{chunk}```")