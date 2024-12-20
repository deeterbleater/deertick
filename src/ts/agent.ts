import * as fs from 'fs';
import * as path from 'path';
import * as ini from 'ini';
import axios from 'axios';
import OpenAI from 'openai';
import {Model, validateProvider, modelById, providers, voiceSamples, listAll} from './modelData';

// Load and parse config.ini
const config = ini.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'config.ini'), 'utf-8'));

// Load Keys from config
const REPLICATE_API_TOKEN = config.keys.REPLICATE_API_TOKEN;
const OPENAI_API_TOKEN = config.keys.OPENAI_API_TOKEN; 
const ANTHROPIC_API_KEY = config.keys.ANTHROPIC_API_KEY;
const HUGGINGFACE_API_KEY = config.keys.HUGGINGFACE_API_KEY;
const OPENROUTER_API_KEY = config.keys.OPENROUTER_API_KEY;
const MISTRAL_API_KEY = config.keys.MISTRAL_API_KEY;
const GOOGLE_API_KEY = config.keys.GOOGLE_API_KEY;

interface AgentSettings {
    top_k: number;
    top_p: number;
    prompt: string;
    max_tokens: number;
    min_tokens: number;
    temperature: number;
    system_prompt: string;
    presence_penalty: number;
    frequency_penalty: number;
    prompt_template: string;
}

interface Tool {
    type: string;
    function: {
        name: string;
        description: string;
        parameters: {
            type: string;
            properties: Record<string, any>;
            required: string[];
            additionalProperties: boolean;
        };
    };
}

export class Agent {
    model: string;
    private provider: string;
    content: string;
    private modelKey: string;
    nickname: string;
    color: string | null;
    font: string | null;
    private request: any;
    private lastResponse: string;
    private lastPrompt: string;
    private conversation: {
        system: string[];
        user: string[];
        agent: string[];
    };
    private history: boolean;
    systemPrompt: string;
    private response: any;
    private ttsPath: string;
    private imgPath: string;
    private outputFormat: string;
    private numOutputs: number;
    private loraScale: number;
    private aspectRatio: string;
    private guidanceScale: number;
    private numInferenceSteps: number;
    private disableSafetyChecker: boolean;
    private seed: number;
    audioPath: string;
    private maxTokens: number;
    private minTokens: number;
    private temperature: number;
    private presencePenalty: number;
    private frequencyPenalty: number;
    private topK: number;
    private topP: number;
    private repetitionPenalty: number;
    private minP: number;
    private topA: number;
    private logitBias: Record<string, number>;
    private logprobs: boolean;
    private topLogprobs: number | null;
    private responseFormat: any;
    private stop: string[];
    private toolChoice: any;
    private promptTemplate: string;
    settings: AgentSettings;
    private tools: Tool[];
    private toolTemplate: Tool;
    private apiUrl: string;
    private headers: Record<string, string>;
    private rateLimitMs: number;
    private maxConcurrent: number;
    private lastRequestTime: number;
    private client: OpenAI | undefined;

    constructor(
        model: string,
        systemPrompt: string = '',
        provider: string = '',
        settings: Partial<AgentSettings> | null = null,
        rateLimitMs: number = 2000,
        maxConcurrent: number = 5
    ) {
        this.model = model;
        this.provider = validateProvider(provider, model);
        this.content = '';
        this.modelKey = model;
        this.nickname = model;
        this.color = null;
        this.font = null;
        this.request = null;
        this.lastResponse = '';
        this.lastPrompt = '';
        this.conversation = { system: [], user: [], agent: [] };
        this.history = false;
        this.systemPrompt = systemPrompt;
        this.response = null;
        this.ttsPath = 'tts';
        this.imgPath = 'img';
        this.outputFormat = 'webp';
        this.numOutputs = 1;
        this.loraScale = 0.6;
        this.aspectRatio = "square";
        this.guidanceScale = 7.5;
        this.numInferenceSteps = 50;
        this.disableSafetyChecker = true;
        this.seed = Math.floor(Math.random() * (1000000 - 9000) + 9000);
        this.audioPath = '';
        this.maxTokens = 256;
        this.minTokens = 0;
        this.temperature = 0.6;
        this.presencePenalty = 0;
        this.frequencyPenalty = 0;
        this.topK = 50;
        this.topP = 0.9;
        this.repetitionPenalty = 1.0;
        this.minP = 0.0;
        this.topA = 0.0;
        this.logitBias = {};
        this.logprobs = false;
        this.topLogprobs = null;
        this.responseFormat = null;
        this.stop = [];
        this.toolChoice = null;
        this.promptTemplate = "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n";
        
        this.settings = {
            top_k: this.topK,
            top_p: this.topP,
            prompt: this.conversation.user.length > 0 ? this.conversation.user[this.conversation.user.length - 1] : '',
            max_tokens: this.maxTokens,
            min_tokens: this.minTokens,
            temperature: this.temperature,
            system_prompt: systemPrompt,
            presence_penalty: this.presencePenalty,
            frequency_penalty: this.frequencyPenalty,
            prompt_template: this.promptTemplate,
            ...settings
        };

        this.tools = [];
        this.toolTemplate = {
            type: "function",
            function: {
                name: "",
                description: "",
                parameters: {
                    type: "object",
                    properties: {},
                    required: [],
                    additionalProperties: false,
                }
            }
        };

        this.apiUrl = this.getApiUrl();
        this.headers = this.getHeaders();
        this.rateLimitMs = rateLimitMs;
        this.maxConcurrent = maxConcurrent;
        this.lastRequestTime = 0;

        this.updateProvider(provider);
    }

    public updateProvider(provider: string): void {
        const modelData = modelById(this.model);
        if (modelData) {
            if (providers.includes(this.provider)) {
                console.log(`${this.provider}: ${this.model}`);
                if (this.provider === 'openai') {
                    this.client = new OpenAI({
                        apiKey: config.keys.OPENAI_API_TOKEN
                    });
                }
            } else {
                console.log(`This provider has not been implemented: ${provider}`);
            }
        }
    }

    public createTool(name: string, description: string, parameters: any): void {
        const newTool = { ...this.toolTemplate };
        newTool.function.name = name;
        newTool.function.description = description;

        for (const [key, value] of Object.entries(parameters)) {
            if (key === 'properties') {
                newTool.function.parameters.properties = {
                    ...newTool.function.parameters.properties,
                    ...value
                };
            } else if (key === 'required') {
                newTool.function.parameters.required = [...value];
            } else {
                (newTool.function.parameters as any)[key] = value;
            }
        }

        const tool = {
            type: "function",
            function: {
                name,
                description,
                parameters
            }
        };

        this.tools.push(tool);
    }

    private getApiUrl(): string {
        const providerUrls: Record<string, string> = {
            "openai": "https://api.openai.com/v1/chat/completions",
            "openrouter": "https://openrouter.ai/api/v1/chat/completions",
            "anthropic": "https://api.anthropic.com/v1/messages",
            "replicate": "https://api.replicate.com/v1/predictions",
            "huggingface": "https://api-inference.huggingface.co/models/",
            "mistral": "https://api.mistral.ai/v1/chat/completions"
        };
        return providerUrls[this.provider] || '';
    }

    private getHeaders(): Record<string, string> {
        const headers: Record<string, Record<string, string>> = {
            "openai": {
                "Authorization": `Bearer ${OPENAI_API_TOKEN}`,
                "Content-Type": "application/json"
            },
            "openrouter": {
                "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
                "HTTP-Referer": "https://deertick.io",
                "X-Title": "DeerTick",
                "Content-Type": "application/json"
            },
            "anthropic": {
                "Authorization": `Bearer ${ANTHROPIC_API_KEY}`,
                "Content-Type": "application/json"
            },
            "mistral": {
                "Authorization": `Bearer ${MISTRAL_API_KEY}`,
                "Content-Type": "application/json"
            },
            "replicate": {
                "Authorization": `Bearer ${REPLICATE_API_TOKEN}`,
                "Content-Type": "application/json"
            },
            "huggingface": {
                "Authorization": `Bearer ${HUGGINGFACE_API_KEY}`,
                "Content-Type": "application/json"
            },
            "google": {
                "Authorization": `Bearer ${GOOGLE_API_KEY}`,
                "Content-Type": "application/json"
            }
        };

        return headers[this.provider] || {};
    }

    public async generateResponse(systemPrompt: string, prompt: string): Promise<string> {
        if (!this.history) {
            this.conversation.system.push(systemPrompt);
            this.conversation.user.push(prompt);
            this.settings.system_prompt = systemPrompt;
            this.settings.prompt = prompt;
            this.lastPrompt = prompt;
        } else {
            let context = '';
            if (this.conversation.user.length > 0) {
                for (let i = 0; i < this.conversation.user.length; i++) {
                    context += `user: ${this.conversation.user[i]}\n`;
                    if (this.conversation.agent.length > i) {
                        context += `assistant: ${this.conversation.agent[i]}\n`;
                    }
                }
            }
            this.settings.system_prompt = systemPrompt;
            this.settings.prompt = context + prompt;
            prompt = context + prompt;
        }

        try {
            const response = await this.makeRequest(systemPrompt, prompt);
            return this.processResponse(response);
        } catch (error) {
            console.error('Error generating response:', error);
            throw error;
        }
    }

    private async makeRequest(systemPrompt: string, prompt: string): Promise<any> {
        const now = Date.now();
        const timeSinceLastRequest = now - this.lastRequestTime;
        
        if (timeSinceLastRequest < this.rateLimitMs) {
            await new Promise(resolve => setTimeout(resolve, this.rateLimitMs - timeSinceLastRequest));
        }

        this.lastRequestTime = Date.now();

        const messages = [
            { role: "system", content: systemPrompt },
            { role: "user", content: prompt }
        ];

        let requestBody;
        if (this.provider === 'openrouter') {
            requestBody = {
                model: this.model,
                messages: messages,
                max_tokens: this.settings.max_tokens,
                temperature: this.settings.temperature,
                top_p: this.settings.top_p,
                presence_penalty: this.settings.presence_penalty,
                frequency_penalty: this.settings.frequency_penalty
            };
        } else {
            requestBody = {
                model: this.model,
                messages,
                ...this.settings
            };
        }

        const response = await axios.post(this.apiUrl, requestBody, { headers: this.headers });
        return response.data;
    }

    private processResponse(response: any): string {
        let content: string;
        
        if (this.provider === 'openai') {
            content = response.choices[0].message.content;
        } else {
            // Handle other provider responses
            content = response.choices?.[0]?.message?.content || '';
        }

        this.content = content;
        this.lastResponse = content;
        this.conversation.agent.push(content);
        return content;
    }

    public async poke(prompt: string): Promise<string> {
        return await this.generateResponse(this.systemPrompt, prompt);
    }

    public async ttsPoke(prompt: string, voice: string = "michael_voice"): Promise<string> {
        const voiceUrl = voiceSamples.get(voice);
        if (!voiceUrl) {
            throw new Error(`Voice sample ${voice} not found`);
        }
        return await this.tts(prompt, voiceUrl);
    }

    public saveConversation(): void {
        // Create a DataFrame from the conversation history
        const conversationId = crypto.randomUUID();
        const filename = `conversation_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
        
        const conversationData = {
            id: conversationId,
            system: this.conversation.system,
            user: this.conversation.user,
            agent: this.conversation.agent
        };

        // Generate filename with current datetime, Save the conversation to a JSON file
        fs.writeFileSync(filename, JSON.stringify(conversationData, null, 2));
        console.log(`Conversation saved to ${filename}`);
    }

    public loadConversation(filename: string): void {
        const data = JSON.parse(fs.readFileSync(filename, 'utf-8'));
        this.conversation.system = data.system;
        this.conversation.user = data.user;
        this.conversation.agent = data.agent;
        console.log(`Conversation loaded from ${filename}`);
    }

    private imgError(prompt: string, rejectedPrompt: string): void {
        console.log(`Rejected image prompt: ${rejectedPrompt}`);
        const admonish = "sorry, this description was flagged for not being safe for work," +
            "please tone it down for the heartless censors. describe it again, please.";
        const imgPrompt = `${prompt}your rejected prompt:${rejectedPrompt}${admonish}`;
        this.generateImage(imgPrompt);
    }

    public async generateImage(prompt: string, filePath?: string): Promise<string | string[]> {
        if (!this.seed) {
            this.seed = Math.floor(Math.random() * (1000000 - 9000) + 9000);
        }

        let output: string | string[] = [];

        if (this.provider === 'replicate') {
            const input: any = {
                prompt,
                num_outputs: this.numOutputs,
                seed: this.seed,
                output_format: this.outputFormat
            };

            if (this.model === 'flux-dev-lora') {
                input.hf_lora = this.model;
                input.lora_scale = this.loraScale;
                input.aspect_ratio = this.aspectRatio;
                input.guidance_scale = this.guidanceScale;
                input.num_inference_steps = this.numInferenceSteps;
                input.disable_safety_checker = this.disableSafetyChecker;
                
                // Call replicate API
                const response = await axios.post('https://api.replicate.com/v1/predictions', {
                    version: "a22c463f11808638ad5e2ebd582e07a469031f48dd567366fb4c6fdab91d614d",
                    input
                }, {
                    headers: this.headers
                });
                output = response.data.urls || [];
            } else if (this.modelKey === 'animate-diff') {
                const response = await axios.post('https://api.replicate.com/v1/predictions', {
                    version: this.model,
                    input: {
                        path: "toonyou_beta3.safetensors",
                        seed: this.seed,
                        steps: this.numInferenceSteps,
                        prompt: prompt,
                        n_prompt: "badhandv4, easynegative, ng_deepnegative_v1_75t, verybadimagenegative_v1.3, bad-artist, bad_prompt_version2-neg, teeth",
                        motion_module: "mm_sd_v14",
                        guidance_scale: this.guidanceScale
                    }
                }, {
                    headers: this.headers
                });
                output = response.data.urls || [];
            } else {
                console.log(`seed: ${this.seed}`);
                try {
                    const response = await axios.post('https://api.replicate.com/v1/predictions', {
                        version: this.model,
                        input: {
                            ...input,
                            quality: "standard"
                        }
                    }, {
                        headers: this.headers
                    });
                    output = response.data.urls || [];
                } catch (error) {
                    console.error(error);
                    this.imgError(prompt, output as string);
                }
            }

            if (output && (typeof output === 'string' || output.length > 0)) {
                const urls = Array.isArray(output) ? output : [output];
                for (const imageUrl of urls) {
                    const imagePath = filePath || `${this.imgPath}${this.imgPath ? '/' : ''}${this.modelKey}_image_${new Date().toISOString().replace(/[:.]/g, '-')}.${this.outputFormat}`;
                    
                    try {
                        const response = await axios.get(imageUrl, { responseType: 'arraybuffer' });
                        fs.writeFileSync(imagePath, response.data);
                        console.log(`Image saved to: ${imagePath}`);
                    } catch (error) {
                        console.error(`Failed to download image: ${error}`);
                    }
                }
            } else {
                console.log("No valid image URL received");
            }
        } else {
            console.log(`Invalid provider: ${this.provider}`);
            return '';
        }

        this.content = output;
        return output;
    }

    public async tts(text: string, audioUrl: string, filePath?: string): Promise<string> {
        console.log(`text: ${text}`);
        console.log(`audio_url: ${audioUrl}`);

        const input = {
            speaker: audioUrl,
            text: text
        };

        try {
            const response = await axios.post('https://api.replicate.com/v1/predictions', {
                version: this.model,
                input
            }, {
                headers: this.headers
            });

            const output = response.data.urls?.[0] || '';

            // Download the audio file
            if (output) {
                const audioPath = filePath || `${this.ttsPath}/${new Date().toISOString().replace(/[:.]/g, '-')}.wav`;
                
                const audioResponse = await axios.get(output, { responseType: 'arraybuffer' });
                fs.writeFileSync(audioPath, audioResponse.data);
                console.log(`Audio saved to: ${audioPath}`);
                
                this.content = output;
                return output;
            } else {
                console.log("No valid audio URL received");
                return '';
            }
        } catch (error) {
            console.error('Error generating audio:', error);
            return '';
        }
    }

    public help(): void {
        listAll();
    }
}
