from agent import Agent
from bot.data_encoding import decode_data
from model_data import model


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
            agent = Agent(
                model=model_key,
                system_prompt=decode_data(row['system_prompt']),
                provider=decode_data(row['provider'])
            )
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
