import random

from agent import Agent
from bot.client import bot
from bot.db.message import get_context, log_message

director = Agent(model="Qwen 2 7B Instruct (free)", provider="openrouter")
director.system_prompt = "You are in control of a team of agents within a discord server. Your task is to decide which agent(s) should respond to each message."


async def who_should_speak(message):
    agents_list = list(bot.agents.keys())
    agents_string = ", ".join(agents_list)

    # Use the director agent to decide who should speak
    user_prompt = f"The following agents are available: {agents_string}. Based on the last message: '{message.content}', which agent should respond? They don't need their name mentioned directly, just poke them if they are being talked about, even vaguely. Respond with the agents names that you think should speak, any name you say will speak so only say them if you want them to speak."

    response = director.poke(user_prompt)

    # Extract the agent names from the response
    chosen_agents = [agent for agent in agents_list if agent.lower() in response.lower()]

    # Check the database for the last message sender and remove them from the list
    async with bot.db_pool.acquire() as conn:
        last_message = await conn.fetchrow('''
            SELECT username
            FROM messages
            WHERE channel_id = $1 AND is_bot = true
            ORDER BY timestamp DESC
            LIMIT 1
        ''', message.channel.id)

    if last_message and last_message['username'] in chosen_agents:
        chosen_agents.remove(last_message['username'])

    for agent_name in chosen_agents:
        if agent_name in bot.agents:
            agent = bot.agents[agent_name]
            # Implement random choice with 60% odds
            if random.random() < 0.6:
                break
            async with message.channel.typing():
                context = await get_context(message.channel.id)
                response = agent.poke(context + f"\n{message.author.name}: {message.content}")
                await log_message(message.channel, is_bot_message=True, bot_content=response)
                chunks = [response[i:i + 1800] for i in range(0, len(response), 1800)]
                for chunk in chunks:
                    await message.channel.send(f"{agent_name}: ```{chunk}```")