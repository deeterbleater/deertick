import json

from bot.client import bot
from bot.data_encoding import encode_data
from bot.error import send_error_message


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
        elif param in ['temperature', 'presence_penalty', 'frequency_penalty', 'top_p', 'repetition_penalty', 'min_p',
                       'top_a', 'lora_scale', 'guidance_scale']:
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