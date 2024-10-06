"""
DeerTick Agents Gateway: A Multi-Provider Language Model Interface

Created by Doe Sparkle

This program provides a unified interface to interact with various language models
from different providers including Replicate, Anthropic, Hugging Face, Google,
OpenAI, and OpenRouter. It also includes web crawling, scraping, database operations,
Discord bot functionality, image generation, and text-to-speech capabilities.

Usage:
    python deertick.py [options]

For a full list of options, use: python deertick.py -h
"""
import argparse
from agent import Agent
from model_data import models, list_all, ModelHead
import pandas as pd
import asyncio
import discord

def main():
    parser = argparse.ArgumentParser(description="DeerTick: A Multi-Provider Language Model Interface")
    parser.add_argument("-m", "--model", default="405b-base", help="Specify the model to use")
    parser.add_argument("-p", "--provider", default="openrouter", help="Specify the provider")
    parser.add_argument("-s", "--system", default="", help="Set the system prompt for the conversation")
    parser.add_argument("-i", "--interactive", action="store_true", help="Start an interactive chat session")
    parser.add_argument("-f", "--file", help="Read input from a file")
    parser.add_argument("-o", "--output", help="Write output to a file")
    parser.add_argument("-l", "--list", action="store_true", help="List available models and providers")
    parser.add_argument("--crawl", help="Start a web crawl from the specified URL")
    parser.add_argument("--scrape", help="Scrape content from the specified URL")
    parser.add_argument("--deep-analysis", action="store_true", help="Perform deep analysis during web crawling")
    parser.add_argument("--export-db", action="store_true", help="Export scraped data to the database")
    parser.add_argument("--backup-db", action="store_true", help="Create a backup of the entire database")
    parser.add_argument("--discord", action="store_true", help="Start the Discord bot")
    parser.add_argument("--generate-image", help="Generate an image based on the given prompt")
    parser.add_argument("--tts", help="Convert the given text to speech")
    parser.add_argument("--voice", help="Specify the voice to use for text-to-speech")
    parser.add_argument("--create-agent", help="Create a new agent with the specified name")
    parser.add_argument("--delete-agent", help="Delete the agent with the specified name")
    parser.add_argument("--agent-info", help="Display information about the specified agent")
    parser.add_argument("--set-param", nargs=3, metavar=('AGENT', 'PARAM', 'VALUE'), help="Set a parameter for the specified agent")
    parser.add_argument("--list-agents", action="store_true", help="List all available agents")
    
    args = parser.parse_args()
    for llm in models:
        if llm[0] == args.model:
            deertick = Agent(llm[1], args.system, args.provider)
            break

    if args.list:
        list_all()
    elif args.interactive:
        #check model exists
        for model in models:
            if model[ModelHead.name.value] == args.model:
                if model[ModelHead.type.value] != "llm" and args.provider == "openrouter":
                    print("Openrouter only works with llm models, please choose another provider.")
                    break
                #don't allow incompatible provider
                for incompatibility in model[ModelHead.incompatible.value]:
                    if incompatibility == args.provider:
                        print("The provider you have chosen is currently incompatible with this model. Please consider asking in the deerTick discord for more information.")
                        break
                else:
                    from terminal_chat import TerminalChat
					# noinspection PyUnboundLocalVariable
                    TerminalChat(deertick).chat("", name_mention=0.5, random_response=0.1)
                break
        else:
            print("The model you have chosen does not exist in the csv file. Please check your spelling.")

    elif args.file:
        # noinspection PyUnboundLocalVariable
        response = deertick.generate_response(args.system, file_read(args.file))
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as file:
                file.write(response)
        else:
            print(f"Agent: {response}")

    elif args.crawl:
        from crawler import WebCrawler
        crawler = WebCrawler(args.crawl, deep_analysis=args.deep_analysis)
        crawler.crawl()

    elif args.scrape:
        from scraper import DynamicBlogScraper
        scraper = DynamicBlogScraper(export_to_db=args.export_db)
        asyncio.run(scraper.scrape_url(args.scrape))

    elif args.backup_db:
        from db import DatabaseManager
        db_manager = DatabaseManager()
        db_manager.backup_database()

    elif args.discord:
        from bot import MyBot
        bot = MyBot(command_prefix='!', intents=discord.Intents.default())
        bot.run(config.get('keys', 'DISCORD_BOT_TOKEN'))

    elif args.generate_image:
        agent = Agent(args.model, args.provider)
        image_url = agent.generate_image(args.generate_image)
        print(f"Generated image: {image_url}")

    elif args.tts:
        agent = Agent(args.model, args.provider)
        audio_path = agent.tts_poke(args.tts, args.voice)
        print(f"Generated audio: {audio_path}")

    elif args.create_agent:
        agent = Agent(args.model, args.provider)
        agent.nickname = args.create_agent
        # Add code to save the agent to the database

    elif args.delete_agent:
        # Add code to delete the agent from the database
        print(f"Agent '{args.delete_agent}' deleted.")

    elif args.agent_info:
        # Add code to retrieve and display agent info from the database
        print(f"Info for agent '{args.agent_info}':")

    elif args.set_param:
        agent_name, param, value = args.set_param
        # Add code to update the agent parameter in the database
        print(f"Updated {param} for agent '{agent_name}' to {value}")

    elif args.list_agents:
        # Add code to list all agents from the database
        print("Available agents:")

    else:
        print("Please specify a valid operation. Use -h for help.")

if __name__ == "__main__":
    main()
