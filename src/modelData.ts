import { readFileSync } from 'fs';

export enum ModelHead {
  id = 0,
  name = 1,
  created = 2,
  description = 3,
  contextLength = 4,
  requestLimits = 5,
  modality = 6,
  tokenizer = 7,
  instructType = 8,
  costPrompt = 9,
  costCompletion = 10,
  costImage = 11,
  costRequest = 12,
  contextLengthTopProvider = 13,
  maxCompletionTokensTopProvider = 14,
  isModerated = 15,
  preferredProvider = 16,
  type = 17,
  incompatible = 18
}

export interface Model {
  id: string;
  name: string;
  created: number;
  description: string;
  contextLength: number;
  // requests per minute
  requestLimits: number;
  modality: string;
  tokenizer: string;
  instructType: string;
  costPrompt: number;
  costCompletion: number;
  costImage: number;
  costRequest: number;
  contextLengthTopProvider: number;
  maxCompletionTokensTopProvider: number;
  isModerated: boolean;
  preferredProvider: string;
  type: string;
  incompatible: string[];
}

export const claudeDesc = "Anthropic's model for low-latency, high throughput text generation. Supports hundreds of pages of text.";
export const gptDesc = "GPT-3.5 Turbo is OpenAI's fastest model. It can understand and generate natural language or code, and is optimized for chat and traditional completion tasks. Training data up to Sep 2021.";
export const openaiDesc = "The latest and strongest model family from OpenAI, o1 is designed to spend more time thinking before responding. The o1 models are optimized for math, science, programming, and other STEM-related tasks. They consistently exhibit PhD-level accuracy on benchmarks in physics, chemistry, and biology. Learn more in the [launch announcement](https://openai.com/o1). Note: This model is currently experimental and not suitable for production use-cases, and may be heavily rate-limited.";

// Models data defined as TypeScript objects
export const models: Model[] = [
  {
    id: "anthropic/claude-2.1",
    name: "Claude 2.1",
    created: 1699488000,
    description: claudeDesc,
    contextLength: 200000,
    requestLimits: 5,
    modality: "text",
    tokenizer: "claude",
    instructType: "claude",
    costPrompt: 0.008,
    costCompletion: 0.024,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 200000,
    maxCompletionTokensTopProvider: 4096,
    isModerated: true,
    preferredProvider: "anthropic",
    type: "chat",
    incompatible: []
  },
  {
    id: "openai/gpt-3.5-turbo",
    name: "GPT-3.5 Turbo",
    created: 1677649200,
    description: gptDesc,
    contextLength: 16385,
    requestLimits: 3500,
    modality: "text",
    tokenizer: "gpt-3.5-turbo",
    instructType: "gpt",
    costPrompt: 0.0015,
    costCompletion: 0.002,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 16385,
    maxCompletionTokensTopProvider: 4096,
    isModerated: true,
    preferredProvider: "openai",
    type: "chat",
    incompatible: []
  },
  {
    id: "openai/gpt-4-0125-preview",
    name: "GPT-4 Turbo",
    created: 1705968000,
    description: openaiDesc,
    contextLength: 128000,
    requestLimits: 500,
    modality: "text",
    tokenizer: "gpt-4",
    instructType: "gpt",
    costPrompt: 0.01,
    costCompletion: 0.03,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 128000,
    maxCompletionTokensTopProvider: 4096,
    isModerated: true,
    preferredProvider: "openai",
    type: "chat",
    incompatible: []
  }
];

export const providers = [
  'openrouter',
  'replicate', 
  'mistral',
  'huggingface',
  'openai'
];

export function modelFind(field: any, head: ModelHead): Model | undefined {
  return models.find(model => model[Object.keys(model)[head]] === field);
}

export function modelByName(modelName: string): Model | undefined {
  return modelFind(modelName, ModelHead.name);
}

export function modelById(modelId: string): Model | undefined {
  return modelFind(modelId, ModelHead.id);
}

export function validateProvider(provider: string, model: string): string {
  if (!provider) {
    const foundModel = modelByName(model);
    return foundModel ? foundModel.preferredProvider : 'openrouter';
  }
  
  const providerIndex = parseInt(provider);
  if (!isNaN(providerIndex) && providerIndex >= 0 && providerIndex < providers.length) {
    return providers[providerIndex];
  }
  
  return provider;
}

// Load voice samples from CSV
export const voiceSamples: { [key: string]: string } = {};
try {
  const samplesData = readFileSync('samples.csv', 'utf-8');
  const lines = samplesData.split('\n').slice(1); // Skip header
  lines.forEach(line => {
    const [voiceName, url] = line.split(',');
    if (voiceName && url) {
      voiceSamples[voiceName.trim()] = url.trim();
    }
  });
} catch (error) {
  console.error('Error loading voice samples:', error);
}

export function listAll(): void {
  console.log("\nmodels:\n");
  models.forEach(model => {
    console.log(`"${model.name}": "${model.id}",`);
  });
  
  console.log("\nproviders:\n");
  providers.forEach((provider, index) => {
    console.log(`${index}. ${provider}`);
  });
}
