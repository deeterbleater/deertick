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