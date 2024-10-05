import random
from agent import Agent
import pandas as pd
from colorama import init, Fore, Back, Style
from model_data import voice_samples, models, ModelHead

# Initialize colorama
init(autoreset=True)

class TerminalChat:
    def __init__(self, model='I-8b', system_prompt='', provider='replicate', settings=None):
        self.agents = []
        for llm in models:
            if llm[ModelHead.name.value] == model:
                self.agents.append(Agent(llm[ModelHead.id.value], system_prompt, provider, settings))
                break
        self.system_prompt = system_prompt

    def chat(self, prompt, name_mention = 0.5, random_response = 0.1):
        self.system_prompt = input('System Prompt (leave blank for default): ')
        user_name = input('Username: ')
        history = str()
        self.connect_msg(self.agents[0].model)
        responding_agents = self.agents
        while True:
            prompt = input(f"{Fore.CYAN}{user_name}: {Style.RESET_ALL}")
            prompt_low = prompt.lower()
            if prompt_low == '%exit':
                break
            elif prompt_low == '%help':
                self.help()
            elif prompt_low == '%clear':
                self.clear_history()
            elif prompt_low == '%file_read':
                print()
            elif prompt_low == '%new_agent':
                model_nick = input('Model (l to list models): ')
                if model_nick == 'l':
                    for model in models:
                        print(f'{model[ModelHead.name.value]}: {model[ModelHead.id.value]}')
                    model_nick = input('Model: ')
                provider = ''
                for model in models:
                    if model[ModelHead.name.value] == model_nick:
                        provider = model[ModelHead.preferred_provider.value]
                        break
                self.agents.append(Agent(model_nick, self.system_prompt, provider))
                self.connect_msg(self.agents[-1].model)
            elif prompt.lower() == '%remove_agent':
                self.agents.pop(int(input('Index: ')))
                print(f"{Fore.GREEN}*{self.agents[0].model} disconnected from the chat*{Style.RESET_ALL}\n-----------------------")
            elif prompt_low == '%list_agents':
                index = 0
                for x in self.agents:
                    print(f'{index}. {x.model} as {x.nickname} with {x.color} hair and {x.font} font')
                    index += 1
            elif prompt_low == '%agent_settings':
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
            elif prompt_low == '%set_global_system_prompt':
                self.system_prompt = input('System Prompt: ')
                for x in self.agents:
                    x.system_prompt = self.system_prompt
            elif prompt_low == '%set_agent_system_prompt':
                for i in range(len(self.agents)):
                    print(f'{i}. {self.agents[i].model} as {self.agents[i].nickname} with {self.agents[i].color} hair and {self.agents[i].font} font')
                agent_index = int(input('Select Agent Index: '))
                system_prompt = input('System Prompt: ')
                self.agents[agent_index].system_prompt = system_prompt
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
                    for model in models:
                        if model[ModelHead.id.value] == agent.nickname:
                            if model[ModelHead.type.value] == 'llm':
                                if self.system_prompt != '':
                                    if agent.system_prompt == '':
                                        agent.system_prompt = self.system_prompt
                                agent.generate_response(agent.system_prompt, agent_prompt)
                                break
                            elif model[ModelHead.type.value] == 'tts':
                                if agent.audio_path == '':
                                    for x, y in voice_samples.items():
                                        print(f'{x}: {y}')
                                    voice_sample = input('Select a voice sample by key name: ')
                                    agent.audio_path = voice_samples[voice_sample]
                                agent.tts(prompt, agent.audio_path)
                                break
                            elif model[ModelHead.type.value] == 'image' or model[ModelHead.type.value] == 'video':
                                agent.generate_image(prompt)
                                break

                except Exception as e:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                    continue
                history = f"{history}\n{agent.model}: {agent.content}\n"
                print(f"{Fore.YELLOW}{agent.model}: {Style.RESET_ALL}{agent.content}\n-----------------------")
            responding_agents = []

    def clear_history(self):
        self.history = str()

    def connect_msg(self, connected_model):
        print(f"{Fore.GREEN}*{connected_model} connected to the chat*{Style.RESET_ALL}\n-----------------------")
        if "free" in connected_model:
            print(f"{Fore.GREEN}_Outputs may be cached. Read about rate limits in ./docs/limits._{Style.RESET_ALL}\n-----------------------")

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
        %set_global_system_prompt - set the system prompt for all agents
        %set_agent_system_prompt - set the system prompt for a specific agent
        """)


if __name__ == "__main__":
    chat = TerminalChat()
    chat.chat('I-8b, What is the capital of the moon?')
