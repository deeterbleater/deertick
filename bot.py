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

# Database connection
async def create_ssh_tunnel():
    conn = await asyncssh.connect(config.get('database', 'host'), username=config.get('database', 'ec2_user'), client_keys=[config.get('database', 'ec2_key')])
    tunnel = await conn.forward_local_port('', 5432, 'localhost', 5432)
    return conn, tunnel

ssl_context = ssl.create_default_context(
    purpose=ssl.Purpose.SERVER_AUTH,
    cafile=config.get('database', 'cert')
)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Only for self-signed certs

async def create_pool():
    ssh_conn, tunnel = await create_ssh_tunnel()
    return await asyncpg.create_pool(
        user=config.get('database', 'user'),
        password=config.get('database', 'password'),
        database=config.get('database', 'database'),
        host=config.get('database', 'host'),
        port=tunnel.get_port(),
        ssl=ssl_context
    )

# Create tables if they don't exist
async def create_tables(pool):
    async with pool.acquire() as conn:
        # Create bots table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id UUID PRIMARY KEY,
                guild_id BIGINT,
                bot_id BIGINT,
                bot_name TEXT,
                UNIQUE (guild_id, bot_id)
            )
        ''')

        # Create agents table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY,
                bot_id UUID REFERENCES bots(id),
                model TEXT,
                system_prompt TEXT,
                provider TEXT,
                nickname TEXT,
                color TEXT,
                font TEXT,
                max_tokens INTEGER,
                min_tokens INTEGER,
                temperature FLOAT,
                presence_penalty FLOAT,
                frequency_penalty FLOAT,
                top_k INTEGER,
                top_p FLOAT,
                repetition_penalty FLOAT,
                min_p FLOAT,
                top_a FLOAT,
                seed INTEGER,
                logit_bias JSONB,
                logprobs BOOLEAN,
                top_logprobs INTEGER,
                response_format JSONB,
                stop JSONB,
                tool_choice JSONB,
                prompt_template TEXT,
                tts_path TEXT,
                img_path TEXT,
                output_format TEXT,
                num_outputs INTEGER,
                lora_scale FLOAT,
                aspect_ratio TEXT,
                guidance_scale FLOAT,
                num_inference_steps INTEGER,
                disable_safety_checker BOOLEAN,
                audio_path TEXT,
                tools JSONB
            )
        ''')

        # Create messages table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id UUID PRIMARY KEY,
                guild_id BIGINT,
                channel_id BIGINT,
                user_id BIGINT,
                username TEXT,
                is_bot BOOLEAN,
                bot_id UUID REFERENCES bots(id),
                timestamp TIMESTAMP,
                content TEXT,
                bot_name TEXT
            )
        ''')

        # Check if the is_bot column exists, if not, add it
        await conn.execute('''
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='messages' AND column_name='is_bot') THEN
                    ALTER TABLE messages ADD COLUMN is_bot BOOLEAN;
                END IF;
            END $$;
        ''')

        # Check if the bot_name column exists, if not, add it
        await conn.execute('''
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                               WHERE table_name='messages' AND column_name='bot_name') THEN
                    ALTER TABLE messages ADD COLUMN bot_name TEXT;
                END IF;
            END $$;
        ''')

async def create_error_log_table(pool):
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS error_log (
                id UUID PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE,
                agent_name TEXT,
                error TEXT,
                channel_id BIGINT,
                guild_id BIGINT,
                context TEXT
            )
        ''')

async def log_error(pool, agent_name, error, channel_id, guild_id, context):
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO error_log (id, timestamp, agent_name, error, channel_id, guild_id, context)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', uuid.uuid4(), datetime.datetime.now(pytz.utc), agent_name, error, channel_id, guild_id, context)

async def send_error_message(ctx, error_message, agent_name="System"):
    """Send an error message to the Discord channel with a caution emoji and log it to the database."""
    caution_emoji = "⚠️"  # Unicode caution emoji
    await ctx.send(f"{caution_emoji} Error: {error_message}")
    
    # Log the error to the database
    context = f"Command: {ctx.message.content}" if ctx.message else "No context available"
    await log_error(bot.db_pool, agent_name, error_message, ctx.channel.id, ctx.guild.id, context)

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = None
        self.agents = {}

    async def setup_hook(self):
        self.db_pool = await create_pool()
        await create_tables(self.db_pool)
        await create_error_log_table(self.db_pool)  # Add this line
        self.agents = await load_agents_from_db(self.db_pool)
        print(f"Loaded {len(self.agents)} agents from the database.")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Loaded agents: {", ".join(self.agents.keys())}')

async def load_agents_from_db(pool):
    agents = {}
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT a.*, b.bot_name
            FROM agents a
            JOIN bots b ON a.bot_id = b.id
        ''')

        model_key = None

        for row in rows:
            for key, value in model.items():
                if value == row['model']:
                    model_key = key
                    break
            agent = Agent(model=model_key,
            system_prompt=decode_data(row['system_prompt']),
            provider=decode_data(row['provider']))
            agent.nickname = decode_data(row['nickname'])
            agent.color = decode_data(row['color'])
            agent.font = decode_data(row['font'])
            agent.max_tokens = decode_data(row['max_tokens'])
            agent.min_tokens = decode_data(row['min_tokens'])
            agent.temperature = decode_data(row['temperature'])
            agent.presence_penalty = row['presence_penalty']
            agent.frequency_penalty = decode_data(row['frequency_penalty'])
            agent.top_k = decode_data(row['top_k'])
            agent.top_p = decode_data(row['top_p'])
            agent.repetition_penalty = decode_data(row['repetition_penalty'])
            agent.min_p = row['min_p']
            agent.top_a = decode_data(row['top_a'])
            agent.seed = decode_data(row['seed'])
            agent.logit_bias = decode_data(row['logit_bias'])
            agent.logprobs = decode_data(row['logprobs'])
            agent.top_logprobs = row['top_logprobs']
            agent.response_format = decode_data(row['response_format'])
            agent.stop = decode_data(row['stop'])
            agent.tool_choice = decode_data(row['tool_choice'])
            agent.prompt_template = decode_data(row['prompt_template'])
            agent.tts_path = decode_data(row['tts_path'])
            agent.img_path = decode_data(row['img_path'])
            agent.output_format = decode_data(row['output_format'])
            agent.num_outputs = decode_data(row['num_outputs'])
            agent.lora_scale = decode_data(row['lora_scale'])
            agent.aspect_ratio = decode_data(row['aspect_ratio'])
            agent.guidance_scale = decode_data(row['guidance_scale'])
            agent.num_inference_steps = decode_data(row['num_inference_steps'])
            agent.disable_safety_checker = decode_data(row['disable_safety_checker'])
            agent.audio_path = decode_data(row['audio_path'])
            agent.tools = decode_data(row['tools'])

            agents[decode_data(row['bot_name'])] = agent

    return agents

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
                chunks = [response[i:i+1800] for i in range(0, len(response), 1800)]
                for chunk in chunks:
                    await message.channel.send(f"{agent_name}: ```{chunk}```")

async def get_context(channel_id):
    async with bot.db_pool.acquire() as conn:
        context_messages = await conn.fetch('''
            SELECT username, content, is_bot
            FROM messages
            WHERE channel_id = $1
            ORDER BY timestamp DESC
            LIMIT 50
        ''', channel_id)
    
    return "\n".join([f"{msg['username']}: {decode_data(msg['content'])}" for msg in reversed(context_messages)])

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
        content = encode_data(bot_content)
        username = bot.user.name
    else:
        user_id = message.author.id
        guild_id = message.guild.id if message.guild else None
        channel_id = message.channel.id
        content = encode_data(message.content)
        username = message.author.name

    utc_timestamp = datetime.datetime.utcnow()

    async with bot.db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO messages (id, guild_id, channel_id, user_id, username, content, timestamp, is_bot)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ''', uuid.uuid4(), guild_id, channel_id, user_id, encode_data(username),  encode_data(content), utc_timestamp, is_bot_message)

    print(f"Logged message from user ID: {user_id}")



async def get_or_create_bot(guild_id, bot_id, bot_name):
    async with bot.db_pool.acquire() as conn:
        # Try to get existing bot
        bot_record = await conn.fetchrow('''
            SELECT id FROM bots
            WHERE guild_id = $1 AND bot_name = $2
        ''', guild_id, bot_name)

        if bot_record:
            return bot_record['id']

        # If bot doesn't exist, create new record with UUID
        bot_uuid = uuid.uuid4()
        await conn.execute('''
            INSERT INTO bots (id, guild_id, bot_id, bot_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, bot_id) DO UPDATE
            SET bot_name = $4
        ''', bot_uuid, guild_id, str(bot_uuid), bot_name)

        return bot_uuid

@bot.command(name='create_agent')
async def create_agent(ctx, agent_name: str, model: str = "I-8b", provider: str = "replicate"):
    """Create a new agent with the given name, model, and provider."""
    if agent_name in bot.agents:
        await send_error_message(ctx, f"An agent named {agent_name} already exists.", "System")
        return

    new_agent = Agent(model=model, provider=provider)
    new_agent.nickname = agent_name

    # Add to database
    async with bot.db_pool.acquire() as conn:
        bot_id = await conn.fetchval('''
            INSERT INTO bots (id, guild_id, bot_id, bot_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (guild_id, bot_id) DO UPDATE
            SET bot_name = $4
            RETURNING id
        ''', uuid.uuid4(), ctx.guild.id, ctx.author.id, encode_data(agent_name))

        await conn.execute('''
            INSERT INTO agents (
                id, bot_id, model, system_prompt, provider, nickname, color, font,
                max_tokens, min_tokens, temperature, presence_penalty, frequency_penalty,
                top_k, top_p, repetition_penalty, min_p, top_a, seed, logit_bias, logprobs,
                top_logprobs, response_format, stop, tool_choice, prompt_template, tts_path,
                img_path, output_format, num_outputs, lora_scale, aspect_ratio, guidance_scale,
                num_inference_steps, disable_safety_checker, audio_path, tools
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17,
                $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32,
                $33, $34, $35, $36, $37
            )
        ''', uuid.uuid4(), bot_id, encode_data(new_agent.model), encode_data(new_agent.system_prompt),
        encode_data(new_agent.provider), encode_data(new_agent.nickname), encode_data(new_agent.color),
        encode_data(new_agent.font), new_agent.max_tokens, new_agent.min_tokens, new_agent.temperature,
        new_agent.presence_penalty, new_agent.frequency_penalty, new_agent.top_k, new_agent.top_p,
        new_agent.repetition_penalty, new_agent.min_p, new_agent.top_a, new_agent.seed,
        encode_data(new_agent.logit_bias), new_agent.logprobs, new_agent.top_logprobs,
        encode_data(new_agent.response_format), encode_data(new_agent.stop),
        encode_data(new_agent.tool_choice), encode_data(new_agent.prompt_template),
        encode_data(new_agent.tts_path), encode_data(new_agent.img_path),
        encode_data(new_agent.output_format), new_agent.num_outputs, new_agent.lora_scale,
        encode_data(new_agent.aspect_ratio), new_agent.guidance_scale,
        new_agent.num_inference_steps, new_agent.disable_safety_checker,
        encode_data(new_agent.audio_path), encode_data(new_agent.tools))

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

    async with bot.db_pool.acquire() as conn:
        context_messages = await conn.fetch('''
            SELECT username, content, is_bot
            FROM messages
            WHERE channel_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        ''', ctx.channel.id, 50)

    context = "\n".join([f"{msg['username']}: {decode_data(msg['content'])}" for msg in reversed(context_messages)])
    
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
        response = agent.poke(context)

    await log_message(discord.Object(id=ctx.channel.id), is_bot_message=True, bot_content=response)

    chunks = [response[i:i+1800] for i in range(0, len(response), 1800)]

    for chunk in chunks:
        await ctx.send(f"{agent_name}: ```{chunk}```")


@bot.command(name='set_param')
async def set_param(ctx, agent_name: str, param: str, *, value: str):
    """Set a parameter for a specific agent."""
    if agent_name not in bot.agents:
        await send_error_message(ctx, f"Agent {agent_name} does not exist.")
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
        async with bot.db_pool.acquire() as conn:
            await conn.execute(f'''
                UPDATE agents
                SET {param} = $1
                WHERE bot_id = (SELECT id FROM bots WHERE bot_name = $2)
            ''', encode_data(value), agent_name)

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
    async with bot.db_pool.acquire() as conn:
        await conn.execute('''
            UPDATE agents
            SET system_prompt = $1
            WHERE bot_id = (SELECT id FROM bots WHERE bot_name = $2)
        ''', encode_data(prompt), agent_name)

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
    !create_agent <name> [model] [provider] - Create a new agent
    !list_agents - List all available agents
    !get_agent_info <name> - Display all parameters of a specific agent
    !set_param <agent_name> <param> <value> - Set a parameter for a specific agent
    !get_param <agent_name> <param> - Get the value of a parameter for a specific agent
    !set_prompt <agent_name> <prompt> - Set the system prompt for a specific agent
    !get_prompt <agent_name> - Get the system prompt for a specific agent
    !add_to_prompt <agent_name> <text> - Add text to the system prompt for a specific agent
    !talk <agent_name> <message> - Talk to a specific agent (includes chat history)
    !talk_single <agent_name> <message> - Talk to a specific agent (single message only)
    !delete_agent <name> - Delete an existing agent
    !continue - Continue the conversation with the last speaking agent
    !attach_agent <name> - Manually attach an existing agent to the bot
    !deertick_help - Display this help message
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



# Run the bot
bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))