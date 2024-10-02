# Deertick Agent Management and Integration Toolbox (DAMIT)

DeerTick is a versatile Python-based interface for interacting with various language models from different providers, including Replicate, OpenAI, Hugging Face, OpenRouter, and Mistral. It provides a unified way to manage AI agents and integrate them into various workflows.

## Features

- Support for multiple AI providers and models
- Interactive chat mode with customizable agent behaviors
- File input/output support for batch processing
- Customizable system prompts for tailored agent responses
- Image generation capabilities using Replicate's models
- Text-to-speech functionality for audio output
- Flexible tool creation for extending agent capabilities
- Easy switching between different providers and models
- Discord bot integration for interactive AI conversations and agent management
- Web scraping and crawling for data extraction
- Database backup and error logging

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/deeterbleater/deertick
   cd deertick
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `config.ini` file with the necessary API keys and database credentials:
   ```ini
   [database]
   host = your_database_host
   user = your_database_username
   password = your_secure_database_password
   database = your_database_name
   ec2_user = your_ec2_username
   ec2_key = path/to/your/ec2/key.pem
   cert = path/to/your/ssl/cert.pem

   [keys]
   REPLICATE_API_TOKEN = your_replicate_token
   OPENAI_API_TOKEN = your_openai_token
   ANTHROPIC_API_KEY = your_anthropic_key
   HUGGINGFACE_API_KEY = your_huggingface_key
   GOOGLE_API_KEY = your_google_key
   OPENROUTER_API_KEY = your_openrouter_key
   MISTRAL_API_KEY = your_mistral_key
   MESHY_API_KEY = your_meshy_key
   TWILIO_ACCOUNT_SID = your_twilio_sid
   TWILIO_AUTH_TOKEN = your_twilio_auth_token
   DISCORD_BOT_TOKEN = your_discord_bot_token
   ```

## Usage

### Command Line Interface

```
python deertick.py [options]
```

Options:
- `-m`, `--model MODEL`: Specify the model to use (e.g., "I-8b", "I-70b", "gpt-4")
- `-p`, `--provider PROVIDER`: Specify the provider (e.g., "replicate", "openai", "openrouter", "mistral")
- `-s`, `--system PROMPT`: Set the system prompt for the conversation
- `-i`, `--interactive`: Start an interactive chat session
- `-f`, `--file FILE`: Read input from a file
- `-o`, `--output FILE`: Write output to a file
- `-h`, `--help`: Show the help message
- `-l`, `--list`: List available models and providers

### Interactive Mode

To start an interactive chat session:

```
python deertick.py -i -m 405b-base -p openrouter
```

### File Input/Output

To process input from a file and save the output:

```
python deertick.py -f input.txt -o output.txt -m gpt-4 -p openai
```

## Advanced Features

### Image Generation

The `Agent` class includes a `generate_image` method that can be used to create images based on text prompts using Replicate's models.

### Text-to-Speech

The `tts` method in the `Agent` class allows for converting text to speech, providing audio output for agent responses.

### Custom Tools

Extend agent capabilities by creating custom tools using the `create_tool` method. This allows for adding specific functionalities to your agents.

### Web Scraping

The `scraper.py` script provides functionality to scrape web pages and extract specific information using AI. To use the scraper:

1. Ensure you have the required dependencies installed:
   ```
   pip install requests beautifulsoup4 pandas
   ```

2. Run the scraper:
   ```
   python scraper.py
   ```

   This will scrape the predefined list of URLs and save the extracted data to a CSV file in the `scraped_blogs` directory.

3. To modify the URLs to scrape, edit the `urls` list in the `main_with_dataframe()` function.

### Web Crawling

The `crawler.py` script provides a more advanced web crawling functionality. To use the crawler:

1. Ensure you have the required dependencies installed:
   ```
   pip install requests beautifulsoup4 pandas selenium webdriver_manager
   ```

2. Run the crawler:
   ```
   python crawler.py
   ```

   This will start crawling from the specified start URL and save the results to a CSV file.

3. To change the starting URL, modify the `start_url` variable at the bottom of the `crawler.py` file.

4. The crawler respects `robots.txt` files, uses sitemaps when available, and includes Selenium for JavaScript-rendered content.

### Discord Bot Integration

The `bot.py` script provides a Discord bot that integrates DeerTick's AI capabilities. This tool:
   - Connects to Discord and responds to commands
   - Allows creation and management of multiple AI agents within Discord
   - Supports dynamic loading and saving of agents to a database
   - Provides error logging and database backup functionality
   - Enables conversing with AI agents directly in Discord channels

To set up and run the Discord bot:

1. Ensure you have the required dependencies installed:
   ```
   pip install discord.py asyncssh asyncpg pytz
   ```

2. Set up a PostgreSQL database:
   - Install PostgreSQL if you haven't already: https://www.postgresql.org/download/
   - Create a new database for the bot:
     ```
     createdb deertick
     ```
   - Connect to the database and create the necessary tables:
     ```sql
     psql -d deertick

     CREATE TABLE bots (
         id SERIAL PRIMARY KEY,
         name VARCHAR(255) NOT NULL,
         token TEXT NOT NULL,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );

     CREATE TABLE agents (
         id SERIAL PRIMARY KEY,
         name VARCHAR(255) NOT NULL,
         model VARCHAR(255) NOT NULL,
         provider VARCHAR(255) NOT NULL,
         system_prompt TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );

     CREATE TABLE messages (
         id SERIAL PRIMARY KEY,
         agent_id INTEGER REFERENCES agents(id),
         content TEXT NOT NULL,
         role VARCHAR(50) NOT NULL,
         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );

     CREATE TABLE error_log (
         id SERIAL PRIMARY KEY,
         error_message TEXT NOT NULL,
         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```

3. Set up your `config.ini` file with the necessary Discord token and database credentials:
   ```ini
   [keys]
   DISCORD_BOT_TOKEN = your_discord_bot_token

   [database]
   host = your_database_host
   user = your_database_user
   password = your_database_password
   database = deertick
   ec2_user = your_ec2_username
   ec2_key = path/to/your/ec2/key.pem
   cert = path/to/your/ssl/cert.pem
   ```

4. Run the bot:
   ```
   python bot.py
   ```

5. Once the bot is running, you can use the following commands in Discord:
   - `!create_agent <name> [model] [provider]`: Create a new AI agent
   - `!list_agents`: List all available agents
   - `!talk <agent_name> <message>`: Talk to a specific agent
   - `!set_param <agent_name> <param> <value>`: Set a parameter for an agent
   - `!backup_database`: Create a backup of the database
   - `!deertick_help`: Display all available commands

This bot demonstrates how DeerTick can be integrated into a Discord server, allowing for interactive AI conversations and agent management directly within chat channels.

## Examples

DeerTick includes several examples that demonstrate how it can be used to create AI-powered workflows:

1. **soap_yote.py**: A sophisticated AI-driven soap opera generator. This script:
   - Creates a virtual TV set with AI actors, a director, producer, camera operator, and narrator
   - Generates dynamic storylines and character interactions
   - Produces images for scenes using AI image generation
   - Converts character dialogue to speech using text-to-speech technology
   - Saves the episode as a CSV file for further processing or analysis

   To run the soap opera generator:
   ```
   python soap_yote.py [chat_file] [summary_file] [interaction_limit] [last_episode_summary]
   ```

2. **songwriter.py**: An AI-powered songwriting assistant. This script:
   - Uses multiple AI models to collaborate on song creation
   - Generates a chorus based on a single word prompt
   - Expands the chorus into a full song
   - Allows for iterative song generation and saving of results

   To use the songwriter:
   ```python
   python songwriter.py
   ```
   Follow the prompts to generate songs, save them, or quit the program.

3. **podcast.py**: A comprehensive example that generates an entire AI-powered podcast. This script:
   - Creates an outline for a podcast based on a given prompt
   - Generates a conversation between two AI hosts
   - Converts the conversation to speech using text-to-speech (TTS) technology
   - Generates a background image for the podcast
   - Combines all elements to create a video podcast

   To use the podcast generator:
   ```python
   from podcast import Podcast

   # Create a new podcast
   podcast = Podcast(title="Coffee with Agents", prompt="What is the point of a network protocol?")

   # Generate the entire podcast
   podcast.generate_podcast()
   ```

These examples showcase the versatility of the DeerTick toolbox in different scenarios, from complex multi-agent simulations to creative content generation. They demonstrate how DeerTick can be used to create sophisticated AI-driven applications that combine text generation, speech synthesis, and image creation.

## Extending DeerTick

DeerTick is designed to be easily extensible. You can add new providers, models, or functionalities by modifying the `Agent` class and updating the `model_data.py` file with new model information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the AI providers (Replicate, OpenAI, Hugging Face, OpenRouter, Mistral) for their amazing models and APIs.
- Special thanks to the open-source community for inspiration and support.