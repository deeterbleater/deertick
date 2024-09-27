import datetime
import uuid

import discord

from bot.client import bot
from bot.data_encoding import decode_data, encode_data


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

async def log_message(message: discord.Message, is_bot_message=False, bot_content=None):
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

async def get_last_bot_message_in_channel(channel_id: int):
    async with bot.db_pool.acquire() as conn:
        return await conn.fetchrow('''
            SELECT username
            FROM messages
            WHERE channel_id = $1 AND is_bot = true
            ORDER BY timestamp DESC
            LIMIT 1
        ''', channel_id)