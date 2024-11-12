import { Agent } from './agent';
import { listModels, voiceSamples, validateProvider, modelById } from './modelData';
import chalk from 'chalk';
import * as readline from 'readline';

export class TerminalChat {
    private agents: Agent[];
    private systemPrompt: string;

    constructor(initAgent: Agent) {
        this.agents = [initAgent];
        this.systemPrompt = initAgent.systemPrompt;
    }

    private connectMsg(connectedModel: string): void {
        console.log(chalk.green(`*${connectedModel} connected to the chat*`));
        
        // Print license related info
        if (connectedModel.includes("cohere")) {
            console.log("~ Use of this model is subject to Cohere's Acceptable Use Policy: https://docs.cohere.com/docs/c4ai-acceptable-use-policy ~");
        } else if (connectedModel.includes("gemma")) {
            console.log("~ Usage of Gemma is subject to Google's Gemma Terms of Use: https://ai.google.dev/gemma/terms ~");
        } else if (connectedModel.includes("google/g")) {
            console.log("~ Usage of Gemini is subject to Google's Gemini Terms of Use: https://ai.google.dev/terms ~");
        } else if (connectedModel.includes("llama")) {
            console.log("~ Usage of this model is subject to Meta's Acceptable Use Policy: https://www.llama.com/llama3/use-policy/ ~");
        } else if (connectedModel.includes("qwen/")) {
            console.log("~ Usage of this model is subject to Tongyi Qianwen LICENSE AGREEMENT: https://huggingface.co/Qwen/Qwen1.5-110B-Chat/blob/main/LICENSE ~");
        }

        // Print variant related info
        if (connectedModel.includes("extended")) {
            this.endpointStr(connectedModel, "extended-context", true);
        } else if (connectedModel.includes("free")) {
            console.log(chalk.green("_Outputs may be cached. Read about rate limits in ./docs/limits._"));
            this.endpointStr(connectedModel, "free, rate-limited", false);
        } else if (connectedModel.includes("nitro")) {
            this.endpointStr(connectedModel, "higher-throughput", true);
        }
    }

    private endpointStr(model: string, descstr: string, isPricy: boolean): void {
        const connectedModel = modelById(model);
        if (!connectedModel) return;

        let msg = chalk.green(`_These are ${descstr} endpoints for ${connectedModel.name} (/models/${connectedModel.id}).`);
        if (isPricy) {
            msg += " They may have higher prices.";
        }
        msg += "_\n-----------------------";
        console.log(msg);
    }

    private help(): void {
        console.log(chalk.magenta("Available commands:"));
        console.log(`
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
        `);
    }

    private listAgents(): void {
        this.agents.forEach((agent, i) => {
            console.log(`${i}. ${agent.model} as ${agent.nickname} with ${agent.color} hair and ${agent.font} font`);
        });
    }

    public async chat(prompt: string, nameMention: number = 0.5, randomResponse: number = 0.1): Promise<void> {
        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });

        const question = (query: string): Promise<string> => {
            return new Promise((resolve) => {
                rl.question(query, resolve);
            });
        };

        this.systemPrompt = await question('System Prompt (leave blank for default): ');
        const userName = await question('Username: ');
        let history = '';
        this.connectMsg(this.agents[0].model);
        let respondingAgents: Agent[] = [];

        while (true) {
            const prompt = await question(`${chalk.cyan(`${userName}:`)} `);
            const promptLow = prompt.toLowerCase();

            if (promptLow === '%exit') {
                break;
            } else if (promptLow === '%help') {
                this.help();
            } else if (promptLow === '%clear') {
                history = '';
            } else if (promptLow === '%file_read') {
                const inputFile = await question('Input file name: ');
                const agentNick = await question('Agent to show file to (l to list agents): ');
                
                if (agentNick === 'l') {
                    this.listAgents();
                    const selectedAgent = await question('Agent: ');
                    respondingAgents.push(this.agents[parseInt(selectedAgent)]);
                }
            } else if (promptLow === '%new_agent') {
                const modelNick = await question('Model (l to list models): ');
                if (modelNick === 'l') {
                    listModels();
                    const selectedModel = await question('Model: ');
                    const provider = validateProvider('', selectedModel);
                    this.agents.push(new Agent(selectedModel, this.systemPrompt, provider));
                    this.connectMsg(this.agents[this.agents.length - 1].model);
                }
            } else if (promptLow === '%remove_agent') {
                const index = parseInt(await question('Index: '));
                this.agents.splice(index, 1);
                console.log(chalk.green(`*${this.agents[0].model} disconnected from the chat*\n-----------------------`));
            } else if (promptLow === '%list_agents') {
                this.listAgents();
            } else if (promptLow === '%agent_settings') {
                const agentIndex = parseInt(await question('Index: '));
                const settings = await question('Settings: ');
                // Parse and apply settings
                try {
                    const settingsObj = JSON.parse(settings);
                    Object.assign(this.agents[agentIndex].settings, settingsObj);
                } catch (e) {
                    console.error('Invalid settings format');
                }
            } else if (promptLow === '%set_global_system_prompt') {
                this.systemPrompt = await question('System Prompt: ');
                this.agents.forEach(agent => {
                    agent.systemPrompt = this.systemPrompt;
                });
            } else if (promptLow === '%set_agent_system_prompt') {
                this.listAgents();
                const agentIndex = parseInt(await question('Select Agent Index: '));
                const systemPrompt = await question('System Prompt: ');
                this.agents[agentIndex].systemPrompt = systemPrompt;
            } else {
                // Handle normal chat interaction
                for (const element of this.agents) {
                    if (prompt.includes(`@${element.model}`) || prompt.includes(`@${element.nickname}`)) {
                        respondingAgents.push(element);
                    } else if (prompt.includes(`${element.nickname}>`) || prompt.includes(`<${element.model}`)) {
                        if (!respondingAgents.includes(element)) {
                            if (Math.random() < nameMention) {
                                respondingAgents.push(element);
                            }
                        }
                    } else if (Math.random() < randomResponse) {
                        if (!respondingAgents.includes(element)) {
                            respondingAgents.push(element);
                        }
                    }
                }

                for (const agent of respondingAgents) {
                    const agentPrompt = `${history}\n${prompt}\n`;
                    console.log("-----------------------");
                    history = agentPrompt;

                    try {
                        const model = modelById(agent.nickname);
                        if (model) {
                            switch (model.type) {
                                case 'llm':
                                    if (this.systemPrompt && !agent.systemPrompt) {
                                        agent.systemPrompt = this.systemPrompt;
                                    }
                                    await agent.generateResponse(agent.systemPrompt, agentPrompt);
                                    break;
                                case 'tts':
                                    if (!agent.audioPath) {
                                        console.log('Available voices:');
                                        for (const [key, value] of voiceSamples.entries()) {
                                            console.log(`${key}: ${value}`);
                                        }
                                        const voiceSample = await question('Select a voice sample by key name: ');
                                        agent.audioPath = voiceSamples.get(voiceSample) || '';
                                    }
                                    await agent.tts(prompt, agent.audioPath);
                                    break;
                                case 'image':
                                    await agent.generateImage(prompt);
                                    break;
                                case 'video':
                                    await agent.generateImage(prompt);
                                    break;
                            }
                        }
                    } catch (e) {
                        console.error(chalk.red(`Error: ${e}`));
                        continue;
                    }

                    history = `${history}\n${agent.model}: ${agent.content}\n`;
                    console.log(`${chalk.yellow(agent.model)}: ${agent.content}\n-----------------------`);
                }
                respondingAgents = [];
            }
        }

        rl.close();
    }
}
