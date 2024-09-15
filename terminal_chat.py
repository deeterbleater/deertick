import random
from deertick import Agent
import pandas as pd
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

class TerminalChat:
    def __init__(self, model='I-8b', system_prompt='', provider='replicate', settings=None):     
        self.agents = []
        self.agents.append(Agent(model, system_prompt, provider, settings))

    def chat(self, prompt, name_mention = 0.5, random_response = 0.1):
        history = str()
        print(f"{Fore.GREEN}*{self.agents[0].model} connected to the chat*{Style.RESET_ALL}\n-----------------------")
        responding_agents = self.agents
        while True:
            system_prompt = "Have a casual conversation. You only have to respond with a message. The user input is the conversation history. Everything before this happened in the past."
            prompt = input(f"{Fore.CYAN}Doe: {Style.RESET_ALL}")
            if prompt.lower() == '%exit':
                break
            elif prompt.lower() == '%help':
                self.help()
            elif prompt.lower() == '%clear':
                self.clear_history()
            elif prompt.lower() == '%new_agent':
                self.agents.append(Agent(input('Model: '), input('System Prompt: '), input('Provider: ')))
                print(f"{Fore.GREEN}*{self.agents[0].model} connected to the chat*{Style.RESET_ALL}\n-----------------------")
            elif prompt.lower() == '%remove_agent':
                self.agents.pop(int(input('Index: ')))
                print(f"{Fore.GREEN}*{self.agents[0].model} disconnected from the chat*{Style.RESET_ALL}\n-----------------------")
            elif prompt.lower() == '%list_agents':
                index = 0
                for x in self.agents:
                    print(f'{index}. {x.model} as {x.nickname} with {x.color} hair and {x.font} font')
                    index += 1
            elif prompt.lower() == '%agent_settings':
                agent_index = int(input('Index: '))
                settings = input('Settings: ')
                for x in settings:
                    if x == '[':
                        settings_dict = {}
                    elif x == ']':
                        self.agents[agent_index].settings = settings_dict
                    elif x == ':':
                        key = str()
                        value = str()
                    elif x == ',':
                        settings_dict[key] = value
            elif '@' in prompt:
                for i in range(len(self.agents)):
                    if f"@{self.agents[i].model}" in prompt or f"@{self.agents[i].nickname}" in prompt:
                        responding_agents.append(self.agents[i])
                    elif f"{self.agents[i].nickname}>" in prompt or f"<{self.agents[i].model}" in prompt:
                        if self.agents[i] not in responding_agents:
                            if random.random() < name_mention:  # 50% chance to respond
                                responding_agents.append(self.agents[i])
                    else:
                        if random.random() < random_response:
                            responding_agents.append(self.agents[i])
            else:
                for i in range(len(self.agents)):
                    if f"{self.agents[i].model}" in prompt or f"{self.agents[i].nickname}" in prompt or str(i) in prompt:
                        responding_agents.append(self.agents[i])
                    if random.random() < random_response:
                        if self.agents[i] not in responding_agents:
                            responding_agents.append(self.agents[i])
            for agent in responding_agents:
                agent_prompt = f"{history}\n{prompt}\n"
                print("-----------------------")
                history = agent_prompt
                try:
                    output = agent.generate_response(system_prompt, agent_prompt)
                except Exception as e:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                    continue
                history = f"{history}\n{agent.model}: {''.join(output)}\n"
                print(f"{Fore.YELLOW}{agent.model}: {Style.RESET_ALL}{''.join(output)}\n-----------------------")
            responding_agents = []    

    def clear_history(self):
        self.history = str()

    def help(self):
        print(f"{Fore.MAGENTA}Available commands:{Style.RESET_ALL}")
        print("""
        %exit - exit the chat
        %help - show this message
        %clear - clear the chat history
        %new_agent - create a new agent
        %remove_agent - remove an agent
        %list_agents - list all agents
        %agent_settings - change agent settings
        """)


if __name__ == "__main__":
    chat = TerminalChat()
    chat.chat('I-8b, What is the capital of the moon?')
