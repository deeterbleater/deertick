import { ConfigParser } from 'configparser';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { Model, ModelHead, validateProvider, modelById } from './modelData';

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
    private model: string;
    private provider: string;
    private content: string;
    private modelKey: string;
    private nickname: string;
    private color: string | null;
    private font: string | null;
    private request: any;
    private lastResponse: string;
    private lastPrompt: string;
    private conversation: {
        system: string[];
        user: string[];
        agent: string[];
    };
    private history: boolean;
    private systemPrompt: string;
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
    private audioPath: string;
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
    private settings: AgentSettings;
    private tools: Tool[];
    private toolTemplate: Tool;
    private apiUrl: string;
    private headers: Record<string, string>;
    private rateLimitMs: number;
    private maxConcurrent: number;
    private lastRequestTime: number;

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
        this.seed = null;
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
        const config = new ConfigParser();
        config.read('config.ini');

        const headers: Record<string, Record<string, string>> = {
            "openai": {
                "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
                "Content-Type": "application/json"
            },
            "openrouter": {
                "Authorization": `Bearer ${config.get("keys", "OPENROUTER_API_KEY")}`,
                "HTTP-Referer": "https://deertick.io",
                "X-Title": "DeerTick",
                "Content-Type": "application/json"
            },
            "anthropic": {
                "Authorization": `Bearer ${process.env.ANTHROPIC_API_KEY}`,
                "Content-Type": "application/json"
            },
            "mistral": {
                "Authorization": `Bearer ${process.env.MISTRAL_API_KEY}`,
                "Content-Type": "application/json"
            },
            "replicate": {
                "Authorization": `Bearer ${process.env.REPLICATE_API_KEY}`,
                "Content-Type": "application/json"
            },
            "huggingface": {
                "Authorization": `Bearer ${config.get("keys", "HUGGINGFACE_API_KEY")}`,
                "Content-Type": "application/json"
            }
        };

        return headers[this.provider] || {};
    }

    public updateProvider(provider: string): void {
        const modelData = modelById(this.model);
        if (modelData) {
            if (this.provider in providers) {
                console.log(`${this.provider}: ${this.model}`);
                if (this.provider === 'openai') {
                    // Initialize OpenAI client
                }
            } else {
                console.log(`This provider has not been implemented: ${provider}`);
            }
        }
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

        const requestBody = {
            model: this.model,
            messages,
            ...this.settings
        };

        const response = await axios.post(this.apiUrl, requestBody, { headers: this.headers });
        return response.data;
    }

    private processResponse(response: any): string {
        let content = '';
        
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
        const response = await this.generateResponse(this.systemPrompt, prompt);
        return typeof response === 'string' ? response : Array.isArray(response) ? response.join('') : '';
    }

    // Additional methods for image generation, TTS, etc. would go here
}
