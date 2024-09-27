async def deertick_help_command(ctx):
    """Display help information for the bot commands."""
    help_text = """
    Available commands:
    !create_agent <name> [model] [provider] - Create a new agent
    !list_agents - List all available agents
    !get_agent_info <name> - Display all parameters of a specific agent
    !set_param <agent_name> <param> <value> - Set a parameter for a specific agent
    !get_param <agent_name> <param> - Get the value of a parameter for a specific agent
    !set_prompt <agent_name> <prompt> - Set the system prompt for a specific agent
    !get_prompt <agent_name> - Get the system prompt for a specific agent
    !add_to_prompt <agent_name> <text> - Add text to the system prompt for a specific agent
    !talk <agent_name> <message> - Talk to a specific agent (includes chat history)
    !talk_single <agent_name> <message> - Talk to a specific agent (single message only)
    !delete_agent <name> - Delete an existing agent
    !continue - Continue the conversation with the last speaking agent
    !attach_agent <name> - Manually attach an existing agent to the bot
    !deertick_help - Display this help message
    """
    await ctx.send(help_text)
