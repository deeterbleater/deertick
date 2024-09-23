import discord
from discord.ext import commands
from deertick.agent import Agent
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
                content TEXT
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

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = None
        self.agents = {}

    async def setup_hook(self):
        self.db_pool = await create_pool()
        await create_tables(self.db_pool)
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
        
        for row in rows:
            agent = Agent(model=row['model'], provider=row['provider'])
            agent.system_prompt = row['system_prompt']
            agent.nickname = row['nickname']
            agent.color = row['color']
            agent.font = row['font']
            agent.max_tokens = row['max_tokens']
            agent.min_tokens = row['min_tokens']
            agent.temperature = row['temperature']
            agent.presence_penalty = row['presence_penalty']
            agent.frequency_penalty = row['frequency_penalty']
            agent.top_k = row['top_k']
            agent.top_p = row['top_p']
            agent.repetition_penalty = row['repetition_penalty']
            agent.min_p = row['min_p']
            agent.top_a = row['top_a']
            agent.seed = row['seed']
            agent.logit_bias = row['logit_bias']
            agent.logprobs = row['logprobs']
            agent.top_logprobs = row['top_logprobs']
            agent.response_format = row['response_format']
            agent.stop = row['stop']
            agent.tool_choice = row['tool_choice']
            agent.prompt_template = row['prompt_template']
            agent.tts_path = row['tts_path']
            agent.img_path = row['img_path']
            agent.output_format = row['output_format']
            agent.num_outputs = row['num_outputs']
            agent.lora_scale = row['lora_scale']
            agent.aspect_ratio = row['aspect_ratio']
            agent.guidance_scale = row['guidance_scale']
            agent.num_inference_steps = row['num_inference_steps']
            agent.disable_safety_checker = row['disable_safety_checker']
            agent.audio_path = row['audio_path']
            agent.tools = row['tools']
            
            agents[row['bot_name']] = agent
    
    return agents

intents = discord.Intents.default()
intents.message_content = True

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await log_message(message)
    await bot.process_commands(message)

async def log_message(message):
    user_id = message.author.id
    guild_id = message.guild.id if message.guild else None
    channel_id = message.channel.id
    content = message.content

    # Convert to UTC timestamp
    utc_timestamp = message.created_at.replace(tzinfo=datetime.timezone.utc).timestamp()

    async with bot.db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO messages (id, guild_id, channel_id, user_id, content, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', uuid.uuid4(), guild_id, channel_id, user_id, content, utc_timestamp)

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
        await ctx.send(f"An agent named {agent_name} already exists.")
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
        ''', uuid.uuid4(), ctx.guild.id, ctx.author.id, agent_name)
        
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
        ''', uuid.uuid4(), bot_id, new_agent.model, new_agent.system_prompt, new_agent.provider,
        new_agent.nickname, new_agent.color, new_agent.font, new_agent.max_tokens,
        new_agent.min_tokens, new_agent.temperature, new_agent.presence_penalty,
        new_agent.frequency_penalty, new_agent.top_k, new_agent.top_p,
        new_agent.repetition_penalty, new_agent.min_p, new_agent.top_a, new_agent.seed,
        json.dumps(new_agent.logit_bias), new_agent.logprobs, new_agent.top_logprobs,
        json.dumps(new_agent.response_format), json.dumps(new_agent.stop),
        json.dumps(new_agent.tool_choice), new_agent.prompt_template, new_agent.tts_path,
        new_agent.img_path, new_agent.output_format, new_agent.num_outputs,
        new_agent.lora_scale, new_agent.aspect_ratio, new_agent.guidance_scale,
        new_agent.num_inference_steps, new_agent.disable_safety_checker,
        new_agent.audio_path, json.dumps(new_agent.tools))
    
    # Add to bot's agents dictionary
    bot.agents[agent_name] = new_agent
    
    await ctx.send(f"Agent {agent_name} created with model {model} and provider {provider}.")

# Run the bot
bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))