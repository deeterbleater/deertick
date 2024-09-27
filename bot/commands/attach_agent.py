from agent import Agent
from bot.client import bot
from bot.data_encoding import decode_data
from bot.models import model


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