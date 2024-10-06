import discord
from discord.ext import commands
from agent import Agent
import asyncio
import asyncssh
import configparser
import asyncpg
import uuid
import datetime
import pytz
import ssl
import json
import uuid
import pandas as pd
import json
import random
import time
import os
import requests
from db import DatabaseManager


def encode_data(data):
    if isinstance(data, str):
        return data
    return json.dumps(data)

def decode_data(data):
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return data

df = pd.read_csv('model_data.csv')

model = {}
model_type = {}
preferred_providers = {}
providers = {}

for _, row in df.iterrows():
    model_name = row['model_name']
    model[model_name] = row['model_id']
    model_type[model_name] = row['model_type']
    preferred_providers[model_name] = row['preferred_provider']
    providers[model_name] = row['providers'].split(', ')

# print(model)
# print(model_name)
# print(model_type)

config = configparser.ConfigParser()
config.read('config.ini')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Bot configuration
PREFIX = '!'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Dictionary to store agents
agents = {}

# Dictionary to store chat histories for each channel
chat_histories = {}


async def send_error_message(ctx, error_message, agent_name="System"):
    """Send an error message to the Discord channel with a caution emoji and log it to the database."""
    caution_emoji = "⚠️"  # Unicode caution emoji
    await ctx.send(f"{caution_emoji} Error: {error_message}")
    
    # Log the error to the database
    context = f"Command: {ctx.message.content}" if ctx.message else "No context available"
    await bot.db_manager.log_error(agent_name, error_message, ctx.channel.id, ctx.guild.id, context)

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_manager = None
        self.agents = {}

    async def setup_hook(self):
        self.db_manager = DatabaseManager()
        await self.db_manager.create_pool()
        await self.db_manager.create_tables()
        self.agents = await self.db_manager.load_agents_from_db()
        print(f"Loaded {len(self.agents)} agents from the database.")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Loaded agents: {", ".join(self.agents.keys())}')


intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(command_prefix='!', intents=intents)

director = Agent(model="NousResearch: Hermes 2 Pro - Llama-3 8B", provider="openrouter")
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
    last_message = await bot.db_manager.get_last_bot_message(message.channel.id)

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
                await bot.db_manager.log_message(message.guild.id, message.channel.id, bot.user.id, agent_name, response, True)
                chunks = [response[i:i+1800] for i in range(0, len(response), 1800)]
                for chunk in chunks:
                    await message.channel.send(f"{agent_name}: ```{chunk}```")

async def get_context(channel_id):
    return await bot.db_manager.get_context(channel_id)

@bot.event
async def on_message(message):
    is_bot = False
    if message.author == bot.user:
        is_bot = True

    await log_message(message, is_bot_message=is_bot)
    await bot.process_commands(message)
    
    # Only process messages not starting with the command prefix
    if not message.content.startswith(bot.command_prefix):
        await who_should_speak(message)

async def log_message(message, is_bot_message=False, bot_content=None):
    if is_bot_message:
        user_id = bot.user.id
        guild_id = message.guild.id if hasattr(message, 'guild') else None
        channel_id = message.id
        content = bot_content
        username = bot.user.name
    else:
        user_id = message.author.id
        guild_id = message.guild.id if message.guild else None
        channel_id = message.channel.id
        content = message.content
        username = message.author.name

    await bot.db_manager.log_message(guild_id, channel_id, user_id, username, content, is_bot_message)
    print(f"Logged message from user ID: {user_id}")



# async def get_or_create_bot(guild_id, bot_id, bot_name):
#     async with bot.db_pool.acquire() as conn:
#         # Try to get existing bot
#         bot_record = await conn.fetchrow('''
#             SELECT id FROM bots
#             WHERE guild_id = $1 AND bot_name = $2
#         ''', guild_id, bot_name)

#         if bot_record:
#             return bot_record['id']

#         # If bot doesn't exist, create new record with UUID
#         bot_uuid = uuid.uuid4()
#         await conn.execute('''
#             INSERT INTO bots (id, guild_id, bot_id, bot_name)
#             VALUES ($1, $2, $3, $4)
#             ON CONFLICT (guild_id, bot_id) DO UPDATE
#             SET bot_name = $4
#         ''', bot_uuid, guild_id, str(bot_uuid), bot_name)

#         return bot_uuid

@bot.command(name='create_agent')
async def create_agent(ctx, agent_name: str, model: str = "I-8b", provider: str = "replicate"):
    """Create a new agent with the given name, model, and provider."""
    # Check if the agent name already exists in the bot's agents dictionary
    if agent_name in bot.agents:
        await send_error_message(ctx, f"An agent named {agent_name} already exists.", "System")
        return

    # Check if the agent name already exists in the database
    agent_exists = await bot.db_manager.agent_exists(agent_name)
    if agent_exists:
        await send_error_message(ctx, f"An agent named {agent_name} already exists in the database.", "System")
        return

    new_agent = Agent(model=model, provider=provider)
    new_agent.nickname = agent_name

    # Add to database
    bot_id = await bot.db_manager.get_or_create_bot(ctx.guild.id, ctx.author.id, agent_name)

    await bot.db_manager.create_agent(
        bot_id, new_agent.model, new_agent.system_prompt, new_agent.provider, new_agent.nickname,
        new_agent.color, new_agent.font, new_agent.max_tokens, new_agent.min_tokens,
        new_agent.temperature, new_agent.presence_penalty, new_agent.frequency_penalty,
        new_agent.top_k, new_agent.top_p, new_agent.repetition_penalty, new_agent.min_p,
        new_agent.top_a, new_agent.seed, new_agent.logit_bias, new_agent.logprobs,
        new_agent.top_logprobs, new_agent.response_format, new_agent.stop,
        new_agent.tool_choice, new_agent.prompt_template, new_agent.tts_path,
        new_agent.img_path, new_agent.output_format, new_agent.num_outputs,
        new_agent.lora_scale, new_agent.aspect_ratio, new_agent.guidance_scale,
        new_agent.num_inference_steps, new_agent.disable_safety_checker,
        new_agent.audio_path, new_agent.tools
    )

    # Add to bot's agents dictionary
    bot.agents[agent_name] = new_agent

    await ctx.send(f"Agent {agent_name} created with model {model} and provider {provider}.")


@bot.command(name='talk')
async def talk(ctx, agent_name: str, *, message: str):
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist. Create it first with !create_agent.", "System")
        return

    agent = bot.agents[agent_name]

    # Check if the message is a reply
    replied_message = None
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    # Get context using DatabaseManager
    context = await bot.db_manager.get_context(ctx.channel.id)
    
    # If it's a reply, add the replied message to the context
    if replied_message:
        context += f"\n[Replied to {replied_message.author.name}: {replied_message.content}]"
    
    context += f"\n{ctx.author.name}: {message}"

    # Use typing() context manager to show typing indicator
    async with ctx.typing():
        # Simulate processing time (you can remove this in production)
        await asyncio.sleep(2)
        print(f"{agent.model} Context: {context}")
        # Get the current timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate the response
        response = agent.poke(context)
        
        # Prepare the output string
        output = f"Model: {agent.model}\nTimestamp: {timestamp}\n\nContext Sent:\n{context}\n\nAgent.convo:\n{agent.convo}\n\nResponse:\n{response}\n\n"
        
        # Write to a text file
        with open(f"{agent_name}_responses.txt", "a") as f:
            f.write(output)
            f.write("-" * 80 + "\n")  # Add a separator for readability

    # Log the bot's message using DatabaseManager
    await bot.db_manager.log_message(ctx.guild.id, ctx.channel.id, bot.user.id, agent_name, response, True)

    # Update agent's history
    new_history_entry = {"role": "assistant", "content": response}
    await bot.db_manager.update_agent_history(agent_name, new_history_entry)

    chunks = [response[i:i+1800] for i in range(0, len(response), 1800)]

    for chunk in chunks:
        await ctx.send(f"{agent_name}: ```{chunk}```")


@bot.command(name='set_param')
async def set_param(ctx, agent_name: str, param: str, *, value: str):
    """Set a parameter for a specific agent. Only admins or the creator of the agent can use this command."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.")
        return

    is_admin = await bot.db_manager.is_admin(ctx.author.id, ctx.guild.id)
    is_creator = await bot.db_manager.is_agent_creator(ctx.author.id, agent_name)

    if not (is_admin or is_creator):
        await send_error_message(ctx, "Only admins or the creator of the agent can change its parameters.", "System")
        return

    agent = bot.agents[agent_name]
    try:
        # Convert value to appropriate type
        if param in ['max_tokens', 'min_tokens', 'top_k', 'top_logprobs', 'num_outputs', 'num_inference_steps']:
            value = int(value)
        elif param in ['temperature', 'presence_penalty', 'frequency_penalty', 'top_p', 'repetition_penalty', 'min_p', 'top_a', 'lora_scale', 'guidance_scale']:
            value = float(value)
        elif param == 'disable_safety_checker':
            value = value.lower() == 'true'
        elif param in ['logit_bias', 'response_format', 'stop', 'tool_choice', 'tools']:
            value = json.loads(value)

        setattr(agent, param, value)
        
        # Update the database
        await bot.db_manager.update_agent(agent_name, {param: value})

        await ctx.send(f"Parameter {param} set to {value} for agent {agent_name}.")
    except AttributeError:
        await send_error_message(ctx, f"Invalid parameter: {param}")
    except ValueError:
        await send_error_message(ctx, f"Invalid value for parameter {param}")
    except json.JSONDecodeError:
        await send_error_message(ctx, f"Invalid JSON format for parameter {param}")

@bot.command(name='set_prompt')
async def set_prompt(ctx, agent_name: str, *, prompt: str):
    """Set the system prompt for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.")
        return

    agent = bot.agents[agent_name]
    agent.system_prompt = prompt

    # Update the database
    await bot.db_manager.update_agent_prompt(agent_name, prompt)

    await ctx.send(f"System prompt updated for agent {agent_name}.")

@bot.command(name='add_to_prompt')
async def add_to_prompt(ctx, agent_name: str, *, text: str):
    """Add text to the system prompt for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.")
        return

    agent = bot.agents[agent_name]
    agent.system_prompt += f"\n{text}"

    # Update the database
    async with bot.db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE agents
            SET system_prompt = $1
            WHERE bot_id = (SELECT id FROM bots WHERE bot_name = $2)
        ''', encode_data(agent.system_prompt), agent_name)

    await ctx.send(f"Text added to system prompt for agent {agent_name}.")

@bot.command(name='get_prompt')
async def get_prompt(ctx, agent_name: str):
    """Get the system prompt for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    agent = bot.agents[agent_name]
    await ctx.send(f"System prompt for agent {agent_name}:\n{agent.system_prompt}")

@bot.command(name='get_param')
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

@bot.command(name='get_agent_info')
async def get_agent_info(ctx, agent_name: str):
    """Get the information for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    agent = bot.agents[agent_name]
    info = f"Agent {agent_name} info:\n{agent}"
    
    # Split the info into chunks of 1900 characters (leaving room for code block formatting)
    chunks = [info[i:i+1900] for i in range(0, len(info), 1900)]
    
    for chunk in chunks:
        await ctx.send(f"```{chunk}```")

@bot.command(name='list_agents')
async def list_agents(ctx):
    """List all current agents."""
    if not bot.agents:
        await ctx.send("There are no agents currently available.")
    else:
        agent_list = "\n".join(f"- {name}" for name in bot.agents.keys())
        await ctx.send(f"Current agents:\n{agent_list}")

@bot.command(name='continue')
async def continue_conversation(ctx):
    """Continue the conversation with the last agent that spoke in the channel."""
    last_message = await bot.db_manager.get_last_bot_message(ctx.channel.id)

    if last_message:
        agent_name = last_message['username']
        if agent_name not in bot.agents:
            await ctx.send(f"The last speaking agent '{agent_name}' no longer exists.")
            return
    else:
        await ctx.send("No previous bot message found in this channel.")
        return

    agent = bot.agents[agent_name]

    # Get the context window of previous messages
    context = await bot.db_manager.get_context(ctx.channel.id)

    # Send "continue" prompt to the agent
    response = agent.poke(f"{context}\nUser: !continue")

    # Log the bot's message
    await bot.db_manager.log_message(ctx.guild.id, ctx.channel.id, bot.user.id, agent_name, response, True)

    # Update agent's history
    new_history_entry = {"role": "assistant", "content": response}
    await bot.db_manager.update_agent_history(agent_name, new_history_entry)

    # Send the response in chunks if it's too long
    chunks = [response[i:i+1800] for i in range(0, len(response), 1800)]
    for chunk in chunks:
        await ctx.send(f"{agent_name}: ```{chunk}```")


@bot.command(name='delete_agent')
async def delete_agent(ctx, agent_name: str):
    """Delete an existing agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    del bot.agents[agent_name]
    await ctx.send(f"Agent {agent_name} deleted.")


@bot.command(name='attach_agent')
async def attach_agent(ctx, agent_name: str):
    """Manually attach an agent from the database to the bot."""
    if agent_name in bot.agents:
        await ctx.send(f"Agent '{agent_name}' is already attached to the bot.")
        return

    async with bot.db_pool.acquire() as conn:
        # Fetch agent data from the database
        agent_data = await conn.fetchrow('''
            SELECT a.*, b.bot_name
            FROM agents a
            JOIN bots b ON a.bot_id = b.id
            WHERE b.bot_name = $1
        ''', agent_name)

    if agent_data:
        # Create a new Agent instance with the retrieved data
        model_key = None
        for key, value in model.items():
            if value == agent_data['model']:
                model_key = key
                break
        
        new_agent = Agent(model=model_key,
                          system_prompt=decode_data(agent_data['system_prompt']),
                          provider=decode_data(agent_data['provider']))
        
        # Set all the agent's attributes
        new_agent.nickname = decode_data(agent_data['nickname'])
        new_agent.color = decode_data(agent_data['color'])
        new_agent.font = decode_data(agent_data['font'])
        new_agent.max_tokens = decode_data(agent_data['max_tokens'])
        new_agent.min_tokens = decode_data(agent_data['min_tokens'])
        new_agent.temperature = decode_data(agent_data['temperature'])
        new_agent.presence_penalty = agent_data['presence_penalty']
        new_agent.frequency_penalty = decode_data(agent_data['frequency_penalty'])
        new_agent.top_k = decode_data(agent_data['top_k'])
        new_agent.top_p = decode_data(agent_data['top_p'])
        new_agent.repetition_penalty = decode_data(agent_data['repetition_penalty'])
        new_agent.min_p = agent_data['min_p']
        new_agent.top_a = decode_data(agent_data['top_a'])
        new_agent.seed = decode_data(agent_data['seed'])
        new_agent.logit_bias = decode_data(agent_data['logit_bias'])
        new_agent.logprobs = decode_data(agent_data['logprobs'])
        new_agent.top_logprobs = agent_data['top_logprobs']
        new_agent.response_format = decode_data(agent_data['response_format'])
        new_agent.stop = decode_data(agent_data['stop'])
        new_agent.tool_choice = decode_data(agent_data['tool_choice'])
        new_agent.prompt_template = decode_data(agent_data['prompt_template'])
        new_agent.tts_path = decode_data(agent_data['tts_path'])
        new_agent.img_path = decode_data(agent_data['img_path'])
        new_agent.output_format = decode_data(agent_data['output_format'])
        new_agent.num_outputs = decode_data(agent_data['num_outputs'])
        new_agent.lora_scale = decode_data(agent_data['lora_scale'])
        new_agent.aspect_ratio = decode_data(agent_data['aspect_ratio'])
        new_agent.guidance_scale = decode_data(agent_data['guidance_scale'])
        new_agent.num_inference_steps = decode_data(agent_data['num_inference_steps'])
        new_agent.disable_safety_checker = decode_data(agent_data['disable_safety_checker'])
        new_agent.audio_path = decode_data(agent_data['audio_path'])
        new_agent.tools = decode_data(agent_data['tools'])

        # Add the new agent to the bot's agents dictionary
        bot.agents[agent_name] = new_agent
        await ctx.send(f"Agent '{agent_name}' has been successfully attached to the bot from the database.")
    else:
        await ctx.send(f"No agent named '{agent_name}' found in the database.")

@bot.command(name='deertick_help')
async def deertick_help_command(ctx):
    """Display help information for the bot commands."""
    help_text = """
    Available commands:

    Agent Management:
    !create_agent <name> [model] [provider] - Create a new agent
    !list_agents - List all available agents
    !get_agent_info <name> - Display all parameters of a specific agent
    !set_param <agent_name> <param> <value> - Set a parameter for a specific agent
    !get_param <agent_name> <param> - Get the value of a parameter for a specific agent
    !delete_agent <name> - Delete an existing agent
    !attach_agent <name> - Manually attach an existing agent to the bot

    Conversation:
    !talk <agent_name> <message> - Talk to a specific agent (includes chat history)
    !talk_single <agent_name> <message> - Talk to a specific agent (single message only)
    !continue - Continue the conversation with the last speaking agent

    Prompt Management:
    !set_prompt <agent_name> <prompt> - Set the system prompt for a specific agent
    !get_prompt <agent_name> - Get the system prompt for a specific agent
    !add_to_prompt <agent_name> <text> - Add text to the system prompt for a specific agent

    Channel Management:
    !add_agent_to_channel <agent_name> - Add an agent to the current channel
    !remove_agent_from_channel <agent_name> - Remove an agent from the current channel
    !get_enabled_agents - List agents enabled for the current channel

    Admin Commands:
    !add_admin <user_id> - Add a user as an admin
    !remove_admin <user_id> - Remove a user from admin list
    !backup_database - Create a backup of the entire database

    Utility:
    !mermaid <diagram_code> - Render a Mermaid diagram
    !deertick_help - Display this help message

    For more detailed information on each command, use !help <command_name>
    """
    await ctx.send(help_text)

@bot.command(name='backup_database')
async def backup_database(ctx):
    """Backup the entire database to CSV files with the current date and time."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"backup_{timestamp}"
        os.makedirs('..', exist_ok=True)

        tables = ['bots', 'agents', 'messages', 'error_log']

        for table in tables:
            filename = f"{backup_folder}/{table}_{timestamp}.csv"
            async with bot.db_pool.acquire() as conn:
                data = await conn.fetch(f"SELECT * FROM {table}")
                if data:
                    df = pd.DataFrame([dict(row) for row in data])
                    df = df.applymap(decode_data)
                    df.to_csv(filename, index=False)
            await ctx.send(f"Table {table} backed up to {filename}")

        await ctx.send(f"Database backup completed. Files saved in folder: {backup_folder}")
    except Exception as e:
        error_message = f"An error occurred during database backup: {str(e)}"
        await send_error_message(ctx, error_message)

@bot.command(name='mermaid')
async def mermaid(ctx, *, diagram_code):
    """Render a Mermaid diagram."""
    try:
        # Encode the Mermaid syntax
        encoded_diagram = requests.utils.quote(diagram_code)
        
        # Generate the image URL
        image_url = f"https://mermaid.ink/img/{encoded_diagram}"
        
        # Send the image to Discord
        await ctx.send(image_url)
    except Exception as e:
        error_message = f"An error occurred while rendering the Mermaid diagram: {str(e)}"
        await send_error_message(ctx, error_message, "Mermaid Renderer")

@bot.command(name='add_agent_to_channel')
async def add_agent_to_channel(ctx, agent_name: str):
    """Add an agent to the current channel. Only admins can use this command."""
    is_admin = await bot.db_manager.is_admin(ctx.author.id, ctx.guild.id)
    if not is_admin:
        await send_error_message(ctx, "Only admins can add agents to channels.", "System")
        return

    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    success = await bot.db_manager.add_agent_to_channel(agent_name, ctx.guild.id, ctx.channel.id, ctx.author.id)
    if success:
        await ctx.send(f"Agent {agent_name} has been added to this channel.")
    else:
        await send_error_message(ctx, f"Failed to add agent {agent_name} to this channel.", "System")

@bot.command(name='remove_agent_from_channel')
async def remove_agent_from_channel(ctx, agent_name: str):
    """Remove an agent from the current channel. Only admins can use this command."""
    is_admin = await bot.db_manager.is_admin(ctx.author.id, ctx.guild.id)
    if not is_admin:
        await send_error_message(ctx, "Only admins can remove agents from channels.", "System")
        return

    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.", "System")
        return

    success = await bot.db_manager.remove_agent_from_channel(agent_name, ctx.guild.id, ctx.channel.id, ctx.author.id)
    if success:
        await ctx.send(f"Agent {agent_name} has been removed from this channel.")
    else:
        await send_error_message(ctx, f"Failed to remove agent {agent_name} from this channel.", "System")

# Run the bot
bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))