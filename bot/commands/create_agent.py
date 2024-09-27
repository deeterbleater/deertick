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