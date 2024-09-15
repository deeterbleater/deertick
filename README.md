# DeerTick: Multi-Provider Language Model Interface

DeerTick is a versatile Python-based interface for interacting with various language models from different providers, including Replicate, OpenAI, Hugging Face, OpenRouter, and Mistral.

## Features

- Support for multiple AI providers and models
- Interactive chat mode
- File input/output support
- Customizable system prompts
- Image generation capabilities
- Text-to-speech functionality

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/deertick.git
   cd deertick
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `config.ini` file with the necessary API keys:
   ```ini
   [keys]
   REPLICATE_API_TOKEN = your_replicate_token
   OPENAI_API_TOKEN = your_openai_token
   HUGGINGFACE_API_KEY = your_huggingface_key
   OPENROUTER_API_KEY = your_openrouter_key
   MISTRAL_API_KEY = your_mistral_key
   ```

## Usage

### Command Line Interface

```
python deertick.py [options]
```

Options:
- `-m`, `--model MODEL`: Specify the model to use (e.g., "I-8b", "I-70b", "gpt-4")
- `-p`, `--provider PROVIDER`: Specify the provider (e.g., "replicate", "openai")
- `-s`, `--system PROMPT`: Set the system prompt for the conversation
- `-i`, `--interactive`: Start an interactive chat session
- `-f`, `--file FILE`: Read input from a file
- `-o`, `--output FILE`: Write output to a file
- `-h`, `--help`: Show the help message
- `-l`, `--list`: List available models and providers

### Interactive Mode

To start an interactive chat session:

```
python deertick.py -i -m I-8b -p replicate
```

### File Input/Output

To process input from a file and save the output:

```
python deertick.py -f input.txt -o output.txt -m gpt-4 -p openai
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.