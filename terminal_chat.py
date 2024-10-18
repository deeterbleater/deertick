import random
from agent import Agent
import pandas as pd
from colorama import init, Fore, Back, Style
from model_data import file_read, list_models, voice_samples, ModelHead, validate_provider, model_by_id

# Initialize colorama
init(autoreset=True)

class TerminalChat:
    def __init__(self, init_agent):
        self.agents = []
        self.agents.append(init_agent)
        self.system_prompt = init_agent.system_prompt

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
                input_file = input('Input file name: ')
                prompt = file_read(input_file)
                agent_nick = input('Agent to show file to (l to list agents): ')
                if agent_nick == 'l':
                    self.list_agents()
                    agent_nick = input('Agent: ')
                responding_agents.append(self.agents[int(agent_nick)])
            elif prompt_low == '%new_agent':
                model_nick = input('Model (l to list models): ')
                if model_nick == 'l':
                    list_models()
                    model_nick = input('Model: ')
                provider = validate_provider('', model_nick)
                self.agents.append(Agent(model_nick, self.system_prompt, provider))
                self.connect_msg(self.agents[-1].model)
            elif prompt.lower() == '%remove_agent':
                self.agents.pop(int(input('Index: ')))
                print(f"{Fore.GREEN}*{self.agents[0].model} disconnected from the chat*{Style.RESET_ALL}\n-----------------------")
            elif prompt_low == '%list_agents':
                self.list_agents()
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
                self.list_agents()
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
                    model = model_by_id(agent.nickname)
                    if model:
                        match model[ModelHead.type.value]:
                            case 'llm':
                                if self.system_prompt != '':
                                    if agent.system_prompt == '':
                                        agent.system_prompt = self.system_prompt
                                agent.generate_response(agent.system_prompt, agent_prompt)
                            case 'tts':
                                if agent.audio_path == '':
                                    for x, y in voice_samples.items():
                                        print(f'{x}: {y}')
                                    voice_sample = input('Select a voice sample by key name: ')
                                    agent.audio_path = voice_samples[voice_sample]
                                agent.tts(prompt, agent.audio_path)
                            case 'image':
                                agent.generate_image(prompt)
                            case 'video':
                                agent.generate_image(prompt)

                except Exception as e:
                    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
                    continue
                history = f"{history}\n{agent.model}: {agent.content}\n"
                print(f"{Fore.YELLOW}{agent.model}: {Style.RESET_ALL}{agent.content}\n-----------------------")
            responding_agents = []

    def clear_history(self):
        self.history = str()

    def endpoint_str(self, model, descstr, is_pricy):
        connected_model = model_by_id(model)
        msg = f"{Fore.GREEN}_These are {descstr} endpoints for {connected_model[ModelHead.name.value]} (/models/{connected_model[ModelHead.id.value]})."
        if is_pricy:
            msg += " They may have higher prices."
        msg += f"_{Style.RESET_ALL}\n-----------------------"
        print(msg)

    def connect_msg(self, connected_model):
        print(f"{Fore.GREEN}*{connected_model} connected to the chat*")
        if "llama" in connected_model:
            print("~ Usage of this model is subject to Meta's Acceptable Use Policy: https://www.llama.com/llama3/use-policy/ ~")

        if "extended" in connected_model:
            self.endpoint_str(connected_model, "extended-context", True)

        elif "free" in connected_model:
            print(f"{Fore.GREEN}_Outputs may be cached. Read about rate limits in ./docs/limits._")
            self.endpoint_str(connected_model, "free, rate-limited", False)

        elif "nitro" in connected_model:
            self.endpoint_str(connected_model, "higher-throughput", True)

    def help(self):
        print(f"{Fore.MAGENTA}Available commands:{Style.RESET_ALL}")
        print("""
        %exit - exit the chat
        %help - show this message
        %clear - clear the chat history
        %file_read - show a file's contents to an agent
        %new_agent - create a new agent
        %remove_agent - remove an agent
        %list_agents - list all agents
        %agent_settings - change agent settings
        %set_global_system_prompt - set the system prompt for all agents
        %set_agent_system_prompt - set the system prompt for a specific agent
        """)

    def list_agents(self):
        for i in range(len(self.agents)):
            print(f'{i}. {self.agents[i].model} as {self.agents[i].nickname} with {self.agents[i].color} hair and {self.agents[i].font} font')


if __name__ == "__main__":
    chat = TerminalChat()
    chat.chat('I-8b, What is the capital of the moon?')
