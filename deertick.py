"""
DeerTick Agents Gateway: A Multi-Provider Language Model Interface

Created by Doe Sparkle

This program provides a unified interface to interact with various language models
from different providers including Replicate, Anthropic, Hugging Face, Google,
OpenAI, and OpenRouter.

Usage:
    python deertick.py [options]

Options:
    -m, --model MODEL     Specify the model to use (e.g., "I-8b", "I-70b", "gpt-4")
    -p, --provider PROVIDER   Specify the provider (e.g., "replicate", "anthropic")
    -s, --system PROMPT   Set the system prompt for the conversation
    -i, --interactive     Start an interactive chat session
    -f, --file FILE       Read input from a file
    -o, --output FILE     Write output to a file
    -h, --help            Show this help message
    -l, --list            List available models and providers

The program reads API keys from a config.ini file and supports various models
across different providers. It allows for both single-query and interactive
chat sessions, with options for input/output redirection.

For more information, please refer to the documentation or README file.
"""
import argparse
from agent import Agent
from model_data import model, providers
from terminal_chat import TerminalChat
import pandas as pd



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeerTick: A Multi-Provider Language Model Interface")
    parser.add_argument("-m", "--model", default="I-8b", help="Specify the model to use (e.g., 'I-8b', 'I-70b', 'gpt-4')")
    parser.add_argument("-p", "--provider", default="replicate", help="Specify the provider (e.g., 'replicate', 'anthropic')")
    parser.add_argument("-s", "--system", default="", help="Set the system prompt for the conversation")
    parser.add_argument("-i", "--interactive", action="store_true", help="Start an interactive chat session")
    parser.add_argument("-f", "--file", help="Read input from a file")
    parser.add_argument("-o", "--output", help="Write output to a file")
    parser.add_argument("-l", "--list", action="store_true", help="List available models and providers")
    args = parser.parse_args()

    if args.list:
        print("Available models:")
        for model_name in model:
            print(f"- {model_name}")
        print("\nAvailable providers:")
        for provider_name in providers:
            print(f"- {provider_name}")
    elif args.interactive:
        deertick = TerminalChat(args.model, args.system, args.provider)
        deertick.chat("", name_mention=0.5, random_response=0.1)
    elif args.file:
        with open(args.file, 'r') as file:
            input_text = file.read()
        deertick = Agent(args.model, args.system, args.provider)
        response = deertick.generate_response(args.system, input_text)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(response)
        else:
            print(f"Agent: {response}")
    else:
        print("Please specify either -i for interactive mode, -f for file input, or -l to list available models and providers.")