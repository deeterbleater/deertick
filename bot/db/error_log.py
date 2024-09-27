import uuid
from datetime import datetime

import pytz


async def log_error(pool, agent_name, error, channel_id, guild_id, context):
    async with pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO error_log (id, timestamp, agent_name, error, channel_id, guild_id, context)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        ''', uuid.uuid4(), datetime.now(pytz.utc), agent_name, error, channel_id, guild_id, context)
