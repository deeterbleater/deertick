# Bot.py API Reference

## Related Modules
- [DeerTick Main](deertick_doc.md)
- [Agent](agent_doc.md)
- [Database Manager](db_doc.md)

This module implements the Discord bot functionality for the DeerTick project. For an overview of how it fits into the larger system, see the [DeerTick Main Documentation](deertick_doc.md).

## Global Functions

### encode_data(data)
Encodes data to JSON if it's not already a string.

### decode_data(data)
Decodes JSON data to Python objects, returns original data if decoding fails.

### send_error_message(ctx, error_message, agent_name="System")
Sends an error message to the Discord channel and logs it to the database.

## Class: MyBot

Extends `commands.Bot` to add custom functionality.

### Constructor

```python
MyBot(*args, **kwargs)
````

### Attributes

- `db_manager` (DatabaseManager): Manages database operations.
- `agents` (dict): Stores active agent instances.

### Methods

#### setup_hook()
Asynchronous setup method called when the bot is starting.

#### on_ready()
Event handler called when the bot has successfully connected to Discord.

## Bot Commands

### create_agent(ctx, agent_name: str, model: str = "I-8b", provider: str = "replicate")
Creates a new agent with the given name, model, and provider.

### talk(ctx, agent_name: str, *, message: str)
Sends a message to a specific agent and gets a response.

### set_param(ctx, agent_name: str, param: str, *, value: str)
Sets a parameter for a specific agent.

### get_agent_info(ctx, agent_name: str)
Retrieves and displays information about a specific agent.

### list_agents(ctx)
Lists all currently available agents.

### continue_conversation(ctx)
Continues the conversation with the last agent that spoke in the channel.

### delete_agent(ctx, agent_name: str)
Deletes an agent from the bot and the database.

### attach_agent(ctx, agent_name: str)
Attaches an existing agent from the database to the bot.

### deertick_help(ctx)
Displays help information for all bot commands.

### backup_database(ctx)
Creates a backup of the entire database to CSV files.

### mermaid(ctx, *, diagram_code)
Renders a Mermaid diagram and sends it to the Discord channel.

### add_agent_to_channel(ctx, agent_name: str)
Adds an agent to the current channel. Only admins can use this command.

### remove_agent_from_channel(ctx, agent_name: str)
Removes an agent from the current channel. Only admins can use this command.

## Global Variables

- `df` (pandas.DataFrame): Stores model data loaded from 'model_data.csv'.
- `model` (dict): Maps model names to their IDs.
- `model_type` (dict): Maps model names to their types.
- `preferred_providers` (dict): Maps model names to their preferred providers.
- `providers` (dict): Maps model names to lists of supported providers.
- `config` (configparser.ConfigParser): Stores configuration data from 'config.ini'.
- `intents` (discord.Intents): Defines the bot's intents.
- `bot` (MyBot): The main bot instance.
- `director` (Agent): A special agent for managing other agents.

## Usage Example

````python
# Initialize the bot
bot = MyBot(command_prefix='!', intents=intents)

# Create a new agent
@bot.command()
async def create_new_agent(ctx, name):
    await create_agent(ctx, name)

# Run the bot
bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))
````


## Notes

- The bot uses a custom `DatabaseManager` for handling database operations.
- Many commands interact with both the bot's local `agents` dictionary and the database.
- Error handling is implemented using the `send_error_message` function.
- The bot supports various operations like creating agents, managing their parameters, and facilitating conversations.