import asyncpg
import asyncssh
import ssl
import configparser
import uuid
import datetime
import pytz
import json
import pandas as pd
import os

class DatabaseManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.db_pool = None

    async def create_ssh_tunnel(self):
        conn = await asyncssh.connect(
            self.config.get('database', 'host'),
            username=self.config.get('database', 'ec2_user'),
            client_keys=[self.config.get('database', 'ec2_key')]
        )
        tunnel = await conn.forward_local_port('', 5432, 'localhost', 5432)
        return conn, tunnel

    async def create_pool(self):
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=self.config.get('database', 'cert')
        )
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Only for self-signed certs

        ssh_conn, tunnel = await self.create_ssh_tunnel()
        self.db_pool = await asyncpg.create_pool(
            user=self.config.get('database', 'user'),
            password=self.config.get('database', 'password'),
            database=self.config.get('database', 'database'),
            host=self.config.get('database', 'host'),
            port=tunnel.get_port(),
            ssl=ssl_context
        )
        return self.db_pool

    async def create_tables(self):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    id UUID PRIMARY KEY,
                    guild_id BIGINT,
                    bot_id BIGINT,
                    bot_name TEXT,
                    UNIQUE (guild_id, bot_id)
                )
            ''')

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
                    tools JSONB,
                    created_by TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    history JSONB,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

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

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_server_channels (
                    id UUID PRIMARY KEY,
                    agent_id UUID REFERENCES agents(id),
                    guild_id BIGINT,
                    channel_id BIGINT,
                    is_enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for the new table
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_agent_server_channels_agent_id ON agent_server_channels(agent_id);
                CREATE INDEX IF NOT EXISTS idx_agent_server_channels_guild_id ON agent_server_channels(guild_id);
                CREATE INDEX IF NOT EXISTS idx_agent_server_channels_channel_id ON agent_server_channels(channel_id);
            ''')

            await conn.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id UUID PRIMARY KEY,
                    user_id BIGINT UNIQUE,
                    guild_id BIGINT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for the admins table
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_admins_user_guild ON admins(user_id, guild_id);
            ''')

    async def log_error(self, agent_name, error, channel_id, guild_id, context):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO error_log (id, timestamp, agent_name, error, channel_id, guild_id, context)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', uuid.uuid4(), datetime.datetime.now(pytz.utc), agent_name, error, channel_id, guild_id, context)

    async def load_agents_from_db(self):
        agents = {}
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT a.*, b.bot_name
                FROM agents a
                JOIN bots b ON a.bot_id = b.id
                WHERE a.is_active = TRUE
            ''')

            for row in rows:
                agent_data = dict(row)
                # Decode fields that might contain encoded data
                for field in ['bot_name', 'system_prompt', 'logit_bias', 'response_format', 'stop', 'tool_choice', 'tools', 'history']:
                    if field in agent_data:
                        agent_data[field] = self.decode_data(agent_data[field])
                agents[agent_data['bot_name']] = agent_data

        return agents

    async def get_or_create_bot(self, guild_id, bot_id, bot_name):
        async with self.db_pool.acquire() as conn:
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

    async def get_context(self, channel_id):
        async with self.db_pool.acquire() as conn:
            context_messages = await conn.fetch('''
                SELECT username, content, is_bot
                FROM messages
                WHERE channel_id = $1
                ORDER BY timestamp DESC
                LIMIT 50
            ''', channel_id)
        
        return "\n".join([f"{msg['username']}: {self.decode_data(msg['content'])}" for msg in reversed(context_messages)])

    async def log_message(self, guild_id, channel_id, user_id, username, content, is_bot_message=False):
        utc_timestamp = datetime.datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO messages (id, guild_id, channel_id, user_id, username, content, timestamp, is_bot)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''', uuid.uuid4(), guild_id, channel_id, user_id, self.encode_data(username), self.encode_data(content), utc_timestamp, is_bot_message)

    async def get_or_create_bot(self, guild_id, bot_id, bot_name):
        async with self.db_pool.acquire() as conn:
            bot = await conn.fetchrow('''
                SELECT * FROM bots WHERE guild_id = $1 AND bot_id = $2
            ''', guild_id, bot_id)

            if not bot:
                bot_id = uuid.uuid4()
                await conn.execute('''
                    INSERT INTO bots (id, guild_id, bot_id, bot_name)
                    VALUES ($1, $2, $3, $4)
                ''', bot_id, guild_id, bot_id, bot_name)
            else:
                bot_id = bot['id']

            return bot_id


    async def backup_database(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = f"backup_{timestamp}"
        os.makedirs(backup_folder, exist_ok=True)

        tables = ['bots', 'agents', 'messages', 'error_log']
        backups = {}

        for table in tables:
            filename = f"{backup_folder}/{table}_{timestamp}.csv"
            async with self.db_pool.acquire() as conn:
                data = await conn.fetch(f"SELECT * FROM {table}")
                if data:
                    df = pd.DataFrame([dict(row) for row in data])
                    df = df.applymap(self.decode_data)
                    df.to_csv(filename, index=False)
                    backups[table] = filename

        return backups

    async def import_csv_to_database(self, table_name, csv_file_path):
        async with self.db_pool.acquire() as conn:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            
            # Get column names from the CSV
            columns = df.columns.tolist()
            
            # Prepare the SQL query
            placeholders = ', '.join(f'${i+1}' for i in range(len(columns)))
            column_names = ', '.join(columns)
            query = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # Insert data row by row
            for _, row in df.iterrows():
                values = [self.encode_data(value) for value in row]
                try:
                    await conn.execute(query, *values)
                except Exception as e:
                    print(f"Error inserting row: {row}")
                    print(f"Error message: {str(e)}")
                    continue
        
        print(f"CSV data imported into {table_name} table successfully.")

    @staticmethod
    def encode_data(data):
        if isinstance(data, str):
            return data
        return json.dumps(data)

    @staticmethod
    def decode_data(data):
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data

    async def create_agent(self, bot_id, model, system_prompt, provider, nickname, color, font,
                           max_tokens, min_tokens, temperature, presence_penalty, frequency_penalty,
                           top_k, top_p, repetition_penalty, min_p, top_a, seed, logit_bias, logprobs,
                           top_logprobs, response_format, stop, tool_choice, prompt_template, tts_path,
                           img_path, output_format, num_outputs, lora_scale, aspect_ratio, guidance_scale,
                           num_inference_steps, disable_safety_checker, audio_path, tools):
        async with self.db_pool.acquire() as conn:
            agent_id = uuid.uuid4()
            await conn.execute('''
                INSERT INTO agents (id, bot_id, model, system_prompt, provider, nickname, color, font, max_tokens, 
                min_tokens, temperature, presence_penalty, frequency_penalty, top_k, top_p, repetition_penalty, min_p, 
                top_a, seed, logit_bias, logprobs, top_logprobs, response_format, stop, tool_choice, prompt_template, 
                tts_path, img_path, output_format, num_outputs, lora_scale, aspect_ratio, guidance_scale, 
                num_inference_steps, disable_safety_checker, audio_path, tools)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, 
                $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36, $37)
            ''', agent_id, bot_id, model, self.encode_data(system_prompt), provider, nickname, color, font, max_tokens,
            min_tokens, temperature, presence_penalty, frequency_penalty, top_k, top_p, repetition_penalty, min_p,
            top_a, seed, self.encode_data(logit_bias), logprobs, top_logprobs, self.encode_data(response_format),
            self.encode_data(stop), self.encode_data(tool_choice), prompt_template, tts_path, img_path, output_format,
            num_outputs, lora_scale, aspect_ratio, guidance_scale, num_inference_steps, disable_safety_checker,
            audio_path, self.encode_data(tools))
            return agent_id

    async def update_agent(self, agent_name, updated_data):
        async with self.db_pool.acquire() as conn:
            update_query = ', '.join([f"{key} = ${i+2}" for i, key in enumerate(updated_data.keys())])
            query = f'''
                UPDATE agents
                SET {update_query}
                WHERE nickname = $1
            '''
            values = [agent_name] + [self.encode_data(value) for value in updated_data.values()]
            await conn.execute(query, *values)

    async def delete_agent(self, agent_name):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                UPDATE agents
                SET is_active = FALSE, updated_at = $1
                WHERE nickname = $2
            ''', datetime.datetime.now(pytz.utc), agent_name)

    async def add_agent_to_channel(self, agent_id, guild_id, channel_id, user_id):
        if await self.is_admin(user_id, guild_id):
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO agent_server_channels (id, agent_id, guild_id, channel_id)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (agent_id, guild_id, channel_id) DO UPDATE
                    SET is_enabled = TRUE, updated_at = CURRENT_TIMESTAMP
                ''', uuid.uuid4(), agent_id, guild_id, channel_id)
            return True
        else:
            return False

    async def remove_agent_from_channel(self, agent_id, guild_id, channel_id, user_id):
        if await self.is_admin(user_id, guild_id):
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE agent_server_channels
                    SET is_enabled = FALSE, updated_at = CURRENT_TIMESTAMP
                    WHERE agent_id = $1 AND guild_id = $2 AND channel_id = $3
                ''', agent_id, guild_id, channel_id)
            return True
        else:
            return False

    async def get_enabled_agents_for_channel(self, guild_id, channel_id):
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT a.*
                FROM agents a
                JOIN agent_server_channels asc ON a.id = asc.agent_id
                WHERE asc.guild_id = $1 AND asc.channel_id = $2 AND asc.is_enabled = TRUE AND a.is_active = TRUE
            ''', guild_id, channel_id)
            
            return [dict(row) for row in rows]

    async def update_agent_history(self, agent_name, new_history_entry):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                UPDATE agents
                SET history = history || $1::jsonb, updated_at = CURRENT_TIMESTAMP
                WHERE nickname = $2
            ''', json.dumps([new_history_entry]), agent_name)

    async def add_admin(self, user_id, guild_id):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO admins (id, user_id, guild_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            ''', uuid.uuid4(), user_id, guild_id)

    async def remove_admin(self, user_id, guild_id):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM admins
                WHERE user_id = $1 AND guild_id = $2
            ''', user_id, guild_id)

    async def is_admin(self, user_id, guild_id):
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT EXISTS(SELECT 1 FROM admins WHERE user_id = $1 AND guild_id = $2)
            ''', user_id, guild_id)
            return result

    async def create_scraped_data_table(self):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    url TEXT,
                    title TEXT,
                    content TEXT,
                    full_text TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    async def insert_scraped_data(self, url, title, content, full_text):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO scraped_data (url, title, content, full_text)
                VALUES ($1, $2, $3, $4)
            ''', self.encode_data(url), self.encode_data(title), 
                self.encode_data(content), self.encode_data(full_text))

    async def insert_multiple_scraped_data(self, data_list):
        async with self.db_pool.acquire() as conn:
            encoded_data_list = [
                (self.encode_data(url), self.encode_data(title), 
                 self.encode_data(content), self.encode_data(full_text))
                for url, title, content, full_text in data_list
            ]
            await conn.executemany('''
                INSERT INTO scraped_data (url, title, content, full_text)
                VALUES ($1, $2, $3, $4)
            ''', encoded_data_list)

    async def create_crawler_tables(self):
        async with self.db_pool.acquire() as conn:
            # Create table for normal crawl data
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS normal_crawl_data (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    url TEXT,
                    links TEXT,
                    selenium_required TEXT,
                    description TEXT,
                    errors TEXT,
                    additional_notes TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create table for deep crawl data
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS deep_crawl_data (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    url TEXT,
                    selenium_required TEXT,
                    elements TEXT,
                    challenges TEXT,
                    notes TEXT,
                    important_elements TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    async def insert_normal_crawl_data(self, url, links, selenium_required, description, errors, additional_notes):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO normal_crawl_data (url, links, selenium_required, description, errors, additional_notes)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', self.encode_data(url), self.encode_data(links), self.encode_data(selenium_required),
                self.encode_data(description), self.encode_data(errors), self.encode_data(additional_notes))

    async def insert_deep_crawl_data(self, url, selenium_required, elements, challenges, notes, important_elements):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO deep_crawl_data (url, selenium_required, elements, challenges, notes, important_elements)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', self.encode_data(url), self.encode_data(selenium_required), self.encode_data(elements),
                self.encode_data(challenges), self.encode_data(notes), self.encode_data(important_elements))

    async def get_last_bot_message(self, channel_id):
        async with self.db_pool.acquire() as conn:
            last_message = await conn.fetchrow('''
                SELECT username, content
                FROM messages
                WHERE channel_id = $1 AND is_bot = true
                ORDER BY timestamp DESC
                LIMIT 1
            ''', channel_id)
        
        if last_message:
            return {
                'username': self.decode_data(last_message['username']),
                'content': self.decode_data(last_message['content'])
            }
        return None

    async def update_agent_prompt(self, agent_name, prompt):
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                UPDATE agents
                SET system_prompt = $1
                WHERE nickname = $2
            ''', self.encode_data(prompt), agent_name)

    async def agent_exists(self, agent_name):
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT EXISTS(SELECT 1 FROM agents WHERE nickname = $1)
            ''', agent_name)
            return result

# Usage example:
# async def main():
#     db_manager = DatabaseManager()
#     await db_manager.create_pool()
#     await db_manager.create_tables()
#     agents = await db_manager.load_agents_from_db()
#     print(f"Loaded {len(agents)} agents from the database.")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())