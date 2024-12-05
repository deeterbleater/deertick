// Type definitions for DeerTick
declare module 'deertick' {
  export interface AgentConfig {
    model: string;
    systemPrompt?: string;
    provider?: string;
    settings?: Partial<AgentSettings>;
    rateLimitMs?: number;
    maxConcurrent?: number;
  }

  export interface AgentSettings {
    topK: number;
    topP: number;
    prompt: string;
    maxTokens: number;
    minTokens: number;
    temperature: number;
    systemPrompt: string;
    presencePenalty: number;
    frequencyPenalty: number;
    promptTemplate: string;
  }

  export interface Tool {
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

  export interface VoiceSample {
    voiceName: string;
    url: string;
  }

  export interface DatabaseConfig {
    host: string;
    port: number;
    database: string;
    user: string;
    password: string;
  }
}
