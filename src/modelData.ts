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
// Convert Python models array to TypeScript
// Models data defined as TypeScript objects
export const models: Model[] = [
  {
    id: "meta-llama/llama-3.1-405b",
    name: "Meta: Llama 3.1 405B (base)",
    created: 1722556800,
    description: "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This is the base 405B pre-trained version. It has demonstrated strong performance compared to leading closed-source models in human evaluations.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "none",
    costPrompt: 2e-06,
    costCompletion: 2e-06,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32768,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "nothingiisreal/mn-celeste-12b",
    name: "Mistral Nemo 12B Celeste",
    created: 1722556800,
    description: "A specialized story writing and roleplaying model based on Mistral's NeMo 12B Instruct. Fine-tuned on curated datasets including Reddit Writing Prompts and Opus Instruct 25K. This model excels at creative writing, offering improved NSFW capabilities, with smarter and more active narration. It demonstrates remarkable versatility in both SFW and NSFW scenarios, with strong Out of Character (OOC) steering capabilities, allowing fine-tuned control over narrative direction and character behavior. Check out the model's [HuggingFace page](https://huggingface.co/nothingiisreal/MN-12B-Celeste-V1.9) for details on what parameters and prompts work best!",
    contextLength: 32000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Mistral",
    instructType: "chatml",
    costPrompt: 1.5e-06,
    costCompletion: 1.5e-06,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "liquid/lfm-40b",
    name: "Liquid: LFM 40B MoE",
    created: 1727654400,
    description: "Liquid's 40.3B Mixture of Experts (MoE) model. Liquid Foundation Models (LFMs) are large neural networks built with computational units rooted in dynamic systems. LFMs are general-purpose AI models that can be used to model any kind of sequential data, including video, audio, text, time series, and signals. See the [launch announcement](https://www.liquid.ai/liquid-foundation-models) for benchmarks and more info.",
    contextLength: 32768,
    requestLimits: 0,
    modality: "text->text",
    tokenizer: "Other",
    instructType: "vicuna",
    costPrompt: 0,
    costCompletion: 0,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32768,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "thedrummer/rocinante-12b",
    name: "Rocinante 12B",
    created: 1727654400,
    description: "Rocinante 12B is designed for engaging storytelling and rich prose. Early testers have reported: - Expanded vocabulary with unique and expressive word choices - Enhanced creativity for vivid narratives - Adventure-filled and captivating stories",
    contextLength: 32768,
    requestLimits: 0,
    modality: "text->text", 
    tokenizer: "Qwen",
    instructType: "chatml",
    costPrompt: 2.5e-7,
    costCompletion: 5e-7,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32768,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "eva-unit-01/eva-qwen-2.5-14b",
    name: "EVA Qwen2.5 14B",
    created: 1727654400,
    description: "A model specializing in RP and creative writing, this model is based on Qwen2.5-14B, fine-tuned with a mixture of synthetic and natural data. It is trained on 1.5M tokens of role-play data, and fine-tuned on 1.5M tokens of synthetic data.",
    contextLength: 32768,
    requestLimits: 0,
    modality: "text->text",
    tokenizer: "Qwen",
    instructType: "chatml", 
    costPrompt: 2.5e-7,
    costCompletion: 5e-7,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32768,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "openai/gpt-3.5-turbo",
    name: "GPT-3.5 Turbo",
    created: 1679584800,
    description: "OpenAI's GPT-3.5 Turbo language model.",
    contextLength: 4096,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "gpt-3",
    instructType: "gpt",
    costPrompt: 0.002,
    costCompletion: 0.004,
    costImage: 0,
    costRequest: 0.002,
    contextLengthTopProvider: 4096,
    maxCompletionTokensTopProvider: 1024,
    isModerated: true,
    preferredProvider: "openai",
    type: "llm",
    incompatible: []
  },
  {
    id: "openai/gpt-4",
    name: "GPT-4",
    created: 1679584800,
    description: "OpenAI's GPT-4 language model.",
    contextLength: 8192,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "gpt-4",
    instructType: "gpt",
    costPrompt: 0.03,
    costCompletion: 0.06,
    costImage: 0,
    costRequest: 0.03,
    contextLengthTopProvider: 8192,
    maxCompletionTokensTopProvider: 2048,
    isModerated: true,
    preferredProvider: "openai",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-2",
    name: "Claude 2",
    created: 1679584800,
    description: "Anthropic's Claude 2 language model.",
    contextLength: 16384,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "claude",
    instructType: "claude",
    costPrompt: 0.008,
    costCompletion: 0.024,
    costImage: 0,
    costRequest: 0.008,
    contextLengthTopProvider: 16384,
    maxCompletionTokensTopProvider: 4096,
    isModerated: true,
    preferredProvider: "anthropic",
    type: "llm",
    incompatible: []
  },
  {
    id: "google/flan-t5-large",
    name: "Flan T5 Large",
    created: 1679584800,
    description: "Google's Flan T5 Large language model.",
    contextLength: 1024,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "t5",
    instructType: "t5",
    costPrompt: 0.006,
    costCompletion: 0.015,
    costImage: 0,
    costRequest: 0.006,
    contextLengthTopProvider: 1024,
    maxCompletionTokensTopProvider: 512,
    isModerated: true,
    preferredProvider: "google",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-1",
    name: "Claude 1",
    created: 1679584800,
    description: "Anthropic's Claude 1 language model.",
    contextLength: 8192,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "claude",
    instructType: "claude",
    costPrompt: 0.004,
    costCompletion: 0.012,
    costImage: 0,
    costRequest: 0.004,
    contextLengthTopProvider: 8192,
    maxCompletionTokensTopProvider: 2048,
    isModerated: true,
    preferredProvider: "anthropic",
    type: "llm",
    incompatible: []
  },
  {
    id: "google/flan-t5-base",
    name: "Flan T5 Base",
    created: 1679584800,
    description: "Google's Flan T5 Base language model.",
    contextLength: 512,
    requestLimits: 1,
    modality: "text->text",
    tokenizer: "t5",
    instructType: "t5",
    costPrompt: 0.003,
    costCompletion: 0.0075,
    costImage: 0,
    costRequest: 0.003,
    contextLengthTopProvider: 512,
    maxCompletionTokensTopProvider: 256,
    isModerated: true,
    preferredProvider: "google",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-instant-1.1",
    name: "Claude Instant v1.1",
    created: 1700611200,
    description: claudeDesc,
    contextLength: 100000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Claude",
    instructType: "claude",
    costPrompt: 8e-07,
    costCompletion: 2.4e-06,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 100000,
    maxCompletionTokensTopProvider: 2048,
    isModerated: true,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-2.1",
    name: "Claude v2.1",
    created: 1700611200,
    description: "Claude 2 delivers advancements in key capabilities for enterprises—including an industry-leading 200K token context window, significant reductions in rates of model hallucination, system prompts and a new beta feature: tool use.",
    contextLength: 200000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Claude",
    instructType: "nan",
    costPrompt: 8e-06,
    costCompletion: 2.4e-05,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 200000,
    maxCompletionTokensTopProvider: 4096,
    isModerated: true,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-2.1:beta",
    name: "Claude v2.1 (self-moderated)",
    created: 1700611200,
    description: "Claude 2 delivers advancements in key capabilities for enterprises—including an industry-leading 200K token context window, significant reductions in rates of model hallucination, system prompts and a new beta feature: tool use._This is a faster endpoint, made available in collaboration with Anthropic, that is self-moderated: response moderation happens on the provider's side instead of OpenRouter's. For requests that pass moderation, it's identical to the [Standard](/models/anthropic/claude-2.1) variant._",
    contextLength: 200000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Claude",
    instructType: "nan",
    costPrompt: 8e-06,
    costCompletion: 2.4e-05,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 200000,
    maxCompletionTokensTopProvider: 4096,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-3.5-sonnet",
    name: "Anthropic: Claude 3.5 Sonnet",
    created: 1718841600,
    description: "Claude 3.5 Sonnet delivers better-than-Opus capabilities, faster-than-Sonnet speeds, at the same Sonnet prices. Sonnet is particularly good at: - Coding: Autonomously writes, edits, and runs code with reasoning and troubleshooting - Data science: Augments human data science expertise; navigates unstructured data while using multiple tools for insights - Visual processing: excelling at interpreting charts, graphs, and images, accurately transcribing text to derive insights beyond just the text alone - Agentic tasks: exceptional tool use, making it great at agentic tasks (i.e. complex, multi-step problem solving tasks that require engaging with other systems) #multimodal",
    contextLength: 200000,
    requestLimits: "",
    modality: "text+image->text",
    tokenizer: "Claude",
    instructType: "nan",
    costPrompt: 3e-06,
    costCompletion: 1.5e-05,
    costImage: 0.0048,
    costRequest: 0,
    contextLengthTopProvider: 200000,
    maxCompletionTokensTopProvider: 8192,
    isModerated: true,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "anthropic/claude-3.5-sonnet:beta",
    name: "Anthropic: Claude 3.5 Sonnet (self-moderated)", 
    created: 1718841600,
    description: "Claude 3.5 Sonnet delivers better-than-Opus capabilities, faster-than-Sonnet speeds, at the same Sonnet prices. Sonnet is particularly good at: - Coding: Autonomously writes, edits, and runs code with reasoning and troubleshooting - Data science: Augments human data science expertise; navigates unstructured data while using multiple tools for insights - Visual processing: excelling at interpreting charts, graphs, and images, accurately transcribing text to derive insights beyond just the text alone - Agentic tasks: exceptional tool use, making it great at agentic tasks (i.e. complex, multi-step problem solving tasks that require engaging with other systems) #multimodal_This is a faster endpoint, made available in collaboration with Anthropic, that is self-moderated: response moderation happens on the provider's side instead of OpenRouter's. For requests that pass moderation, it's identical to the [Standard](/models/anthropic/claude-3.5-sonnet) variant._",
    contextLength: 200000,
    requestLimits: "",
    modality: "text+image->text",
    tokenizer: "Claude",
    instructType: "nan", 
    costPrompt: 3e-06,
    costCompletion: 1.5e-05,
    costImage: 0.0048,
    costRequest: 0,
    contextLengthTopProvider: 200000,
    maxCompletionTokensTopProvider: 8192,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "sao10k/l3-euryale-70b",
    name: "Llama 3 Euryale 70B v2.1",
    created: 1718668800,
    description: "Euryale 70B v2.1 is a model focused on creative roleplay from [Sao10k](https://ko-fi.com/sao10k). - Better prompt adherence. - Better anatomy / spatial awareness. - Adapts much better to unique and custom formatting / reply formats. - Very creative, lots of unique swipes. - Is not restrictive during roleplays.",
    contextLength: 8192,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "llama3",
    costPrompt: 3.5e-07,
    costCompletion: 4e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 8192,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "cognitivecomputations/dolphin-mixtral-8x22b",
    name: "Dolphin 2.9.2 Mixtral 8x22B 🐬",
    created: 1717804800,
    description: "Dolphin 2.9 is designed for instruction following, conversational, and coding. This model is a finetune of [Mixtral 8x22B Instruct](/models/mistralai/mixtral-8x22b-instruct). It features a 64k context length and was fine-tuned with a 16k sequence length using ChatML templates. This model is a successor to [Dolphin Mixtral 8x7B](/models/cognitivecomputations/dolphin-mixtral-8x7b). The model is uncensored and is stripped of alignment and bias. It requires an external alignment layer for ethical use. Users are cautioned to use this highly compliant model responsibly, as detailed in a blog post about uncensored models at [erichartford.com/uncensored-models](https://erichartford.com/uncensored-models). #moe #uncensored",
    contextLength: 65536,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Mistral",
    instructType: "chatml",
    costPrompt: 9e-07,
    costCompletion: 9e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 16000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "qwen/qwen-2-72b-instruct",
    name: "Qwen 2 72B Instruct",
    created: 1717718400,
    description: "Qwen2 72B is a transformer-based model that excels in language understanding, multilingual capabilities, coding, mathematics, and reasoning. It features SwiGLU activation, attention QKV bias, and group query attention. It is pretrained on extensive data with supervised finetuning and direct preference optimization. For more details, see this [blog post](https://qwenlm.github.io/blog/qwen2/) and [GitHub repo](https://github.com/QwenLM/Qwen2).",
    contextLength: 32768,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Qwen",
    instructType: "chatml",
    costPrompt: 3.4e-07,
    costCompletion: 3.9e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32768,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "google/gemini-pro-1.5-exp",
    name: "Google: Gemini Pro 1.5 Experimental",
    created: 1722470400,
    description: "Gemini 1.5 Pro (0827) is an experimental version of the [Gemini 1.5 Pro](/models/google/gemini-pro-1.5) model. #multimodal Note: This model is currently experimental and not suitable for production use-cases, and may be heavily rate-limited.",
    contextLength: 1000000,
    requestLimits: "",
    modality: "text+image->text",
    tokenizer: "Gemini",
    instructType: "nan",
    costPrompt: 0,
    costCompletion: 0,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 1000000,
    maxCompletionTokensTopProvider: 8192,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "perplexity/llama-3.1-sonar-large-128k-online",
    name: "Perplexity: Llama 3.1 Sonar 70B Online",
    created: 1722470400,
    description: "Llama 3.1 Sonar is Perplexity's latest model family. It surpasses their earlier Sonar models in cost-efficiency, speed, and performance. This is the online version of the [offline chat model](/models/perplexity/llama-3.1-sonar-large-128k-chat). It is focused on delivering helpful, up-to-date, and factual responses. #online",
    contextLength: 127072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "nan",
    costPrompt: 1e-06,
    costCompletion: 1e-06,
    costImage: 0,
    costRequest: 0.005,
    contextLengthTopProvider: 127072,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "perplexity/llama-3.1-sonar-large-128k-chat",
    name: "Perplexity: Llama 3.1 Sonar 70B",
    created: 1722470400,
    description: "Llama 3.1 Sonar is Perplexity's latest model family. It surpasses their earlier Sonar models in cost-efficiency, speed, and performance. This is a normal offline LLM, but the [online version](/models/perplexity/llama-3.1-sonar-large-128k-online) of this model has Internet access.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "nan",
    costPrompt: 1e-06,
    costCompletion: 1e-06,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 131072,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "perplexity/llama-3.1-sonar-small-128k-online",
    name: "Perplexity: Llama 3.1 Sonar 8B Online",
    created: 1722470400,
    description: "Llama 3.1 Sonar is Perplexity's latest model family. It surpasses their earlier Sonar models in cost-efficiency, speed, and performance. This is the online version of the [offline chat model](/models/perplexity/llama-3.1-sonar-small-128k-chat). It is focused on delivering helpful, up-to-date, and factual responses. #online",
    contextLength: 127072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3", 
    instructType: "nan",
    costPrompt: 2e-07,
    costCompletion: 2e-07,
    costImage: 0,
    costRequest: 0.005,
    contextLengthTopProvider: 127072,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "perplexity/llama-3.1-sonar-small-128k-chat",
    name: "Perplexity: Llama 3.1 Sonar 8B",
    created: 1722470400,
    description: "Llama 3.1 Sonar is Perplexity's latest model family. It surpasses their earlier Sonar models in cost-efficiency, speed, and performance. This is a normal offline LLM, but the [online version](/models/perplexity/llama-3.1-sonar-small-128k-online) of this model has Internet access.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "nan",
    costPrompt: 2e-07,
    costCompletion: 2e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 131072,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "meta-llama/llama-3.1-70b-instruct",
    name: "Meta: Llama 3.1 70B Instruct",
    created: 1721692800,
    description: "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 70B instruct-tuned version is optimized for high quality dialogue usecases. It has demonstrated strong performance compared to leading closed-source models in human evaluations.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "llama3",
    costPrompt: 3e-07,
    costCompletion: 3e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 131072,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "meta-llama/llama-3.1-8b-instruct",
    name: "Meta: Llama 3.1 8B Instruct", 
    created: 1721692800,
    description: "Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 8B instruct-tuned version is fast and efficient. It has demonstrated strong performance compared to leading closed-source models in human evaluations.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Llama3",
    instructType: "llama3",
    costPrompt: 5.5e-08,
    costCompletion: 5.5e-08,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 100000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "meta-llama/llama-3.1-405b-instruct",
    name: "Meta: Llama 3.1 405B Instruct",
    created: 1721692800,
    description: "The highly anticipated 400B class of Llama3 is here! Clocking in at 128k context with impressive eval scores, the Meta AI team continues to push the frontier of open-source LLMs. Meta's latest class of model (Llama 3.1) launched with a variety of sizes & flavors. This 405B instruct-tuned version is optimized for high quality dialogue usecases. It has demonstrated strong performance compared to leading closed-source models in human evaluations.",
    contextLength: 131072,
    requestLimits: "",
    modality: "text->text", 
    tokenizer: "Llama3",
    instructType: "llama3",
    costPrompt: 1.79e-06,
    costCompletion: 1.79e-06,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 32000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "mistralai/codestral-mamba",
    name: "Mistral: Codestral Mamba",
    created: 1721347200,
    description: "A 7.3B parameter Mamba-based model designed for code and reasoning tasks. - Linear time inference, allowing for theoretically infinite sequence lengths - 256k token context window - Optimized for quick responses, especially beneficial for code productivity - Performs comparably to state-of-the-art transformer models in code and reasoning tasks - Available under the Apache 2.0 license for free use, modification, and distribution",
    contextLength: 256000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Mistral",
    instructType: "mistral",
    costPrompt: 2.5e-07,
    costCompletion: 2.5e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 256000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "mistralai/mistral-nemo",
    name: "Mistral: Mistral Nemo",
    created: 1721347200, 
    description: "A 12B parameter model with a 128k token context length built by Mistral in collaboration with NVIDIA. The model is multilingual, supporting English, French, German, Spanish, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, and Hindi. It supports function calling and is released under the Apache 2.0 license.",
    contextLength: 128000,
    requestLimits: "",
    modality: "text->text",
    tokenizer: "Mistral",
    instructType: "mistral",
    costPrompt: 1.3e-07,
    costCompletion: 1.3e-07,
    costImage: 0,
    costRequest: 0,
    contextLengthTopProvider: 128000,
    maxCompletionTokensTopProvider: 0,
    isModerated: false,
    preferredProvider: "openrouter",
    type: "llm",
    incompatible: []
  },
  {
    id: "openai/gpt-4o-mini-2024-07-18",
    name: "OpenAI: GPT-4o-mini (2024-07-18)",
    created: 1721260800,
    description: "GPT-4o mini is OpenAI's newest model after [GPT-4 Omni](/models/openai/gpt-4o), supporting both text and image inputs with text outputs. As their most advanced small model, it is many multiples more affordable than other recent frontier models, and more than 60% cheaper than [GPT-3.5 Turbo](/models/openai/gpt-3.5-turbo). It maintains SOTA intelligence, while being significantly more cost-effective. GPT-4o mini achieves an 82% score on MMLU and presently ranks higher than GPT-4 on chat preferences [common leaderboards](https://arena.lmsys.org/). Check out the [launch announcement](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/) to learn more.",
    contextLength: 128000,
    requestLimits: "",
    modality: "text+image->text",
    tokenizer: "GPT",
    instructType: "nan",
    costPrompt: 1.5e-07,
    costCompletion: 6e-07,
    costImage: 0.007225,
    costRequest: 0,
    contextLengthTopProvider: 128000,
    maxCompletionTokensTopProvider: 16384,
    isModerated: true,
    preferredProvider: "openrouter",
    type: "llm",
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
