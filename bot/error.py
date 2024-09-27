from bot.client import bot
from bot.db.error_log import log_error


async def send_error_message(ctx, error_message, agent_name="System"):
    """Send an error message to the Discord channel with a caution emoji and log it to the database."""
    caution_emoji = "⚠️"  # Unicode caution emoji
    await ctx.send(f"{caution_emoji} Error: {error_message}")

    # Log the error to the database
    context = f"Command: {ctx.message.content}" if ctx.message else "No context available"
    await log_error(bot.db_pool, agent_name, error_message, ctx.channel.id, ctx.guild.id, context)