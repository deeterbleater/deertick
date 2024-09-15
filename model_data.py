providers = ['replicate', 'mistral', 'huggingface', 'openai', 'openrouter']


voice_samples = {
    "michael_voice": "https://replicate.delivery/mgxm/671f3086-382f-4850-be82-db853e5f05a8/nixon.mp3",
    "jose_voice": "https://replicate.delivery/pbxt/Jt79w0xsT64R1JsiJ0LQRL8UcWspg5J4RFrU6YwEKpOT1ukS/male.wav",
    "anaya_voice": "https://replicate.delivery/pbxt/Kh3PJuzs2xNgaaNOU6fD3jTz0Xx2dE1zpdXpT2k19fzsB8qE/84_121550_000074_000000.wav",
    "tanya_voice": "https://replicate.delivery/pbxt/JXAkGteYRvJbjwcxA2btRpsd8hfEDuS7slrEgZoinxOUzU9q/female.wav",
    "kale_voice": "https://replicate.delivery/pbxt/K30ke0FQUcGCa4gQdyhEPaEeGvEwDZmEK3SMtXaoujJSMlSE/reference_1.wav",
    "doe_voice": "https://resources.us-ord-1.linodeobjects.com/puppy%20asmr%202-001.wav"
}

# Models
model = {
    "I-8b": "meta/meta-llama-3-8b-instruct",
    "I-70b": "meta/meta-llama-3-70b-instruct",
    "405b-base": "meta-llama/llama-3.1-405b",
    "I-405b": "meta/meta-llama-3.1-405b-instruct",
    "flux-schnell": "black-forest-labs/flux-schnell",
    "xtts-v2": "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
    "gpt-4o-or": "openai/gpt-4o",
    "gpt-4o-mini-or": "openai/gpt-4o-mini",
    "gpt-4-turbo-or": "openai/gpt-4-turbo",
    "gpt-4-or": "openai/gpt-4",
    "gpt-3.5-turbo-or": "openai/gpt-3.5-turbo",
    "llava-13b": "yorickvp/llava-13b",
    "flux-dev-lora": "lucataco/flux-dev-lora",
    "gemini-pro-exp": "google/gemini-pro-1.5-exp",
    "gemini-flash-exp": "google/gemini-flash-8b-1.5-exp",
    "gemini-pro": "google/gemini-pro-1.5",
    "gemini-flash": "google/gemini-flash-8b-1.5",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4o": "gpt-4o",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4": "gpt-4",
    "gpt-3.5-turbo": "gpt-3.5-turbo",
    "animate-diff": "lucataco/animate-diff:beecf59c4aee8d81bf04f0381033dfa10dc16e845b4ae00d281e2fa377e48a9f",
    "dolphin": "cognitivecomputations/dolphin-llama-3-70b",
    "codestral": "codestral-latest"
}

model_type = {
    "I-8b": "llm",
    "I-70b": "llm",
    "405b-base": "llm",
    "I-405b": "llm",
    "flux-schnell": "image",
    "xtts-v2": "tts",
    "gpt-4o-or": "llm",
    "gpt-4o-mini-or": "llm",
    "gpt-4-turbo-or": "llm",
    "gpt-4-or": "llm",
    "gpt-3.5-turbo-or": "llm",
    "llava-13b": "image",
    "flux-dev-lora": "image",
    "gemini-pro-exp": "llm",
    "gemini-flash-exp": "llm",
    "gemini-pro": "llm",
    "gemini-flash": "llm",
    "gpt-4o-mini": "llm",
    "gpt-4o": "llm",
    "gpt-4-turbo": "llm",
    "gpt-4": "llm",
    "gpt-3.5-turbo": "llm",
    "animate-diff": "video",
    "dolphin": "llm",
    "codestral": "llm"
}

preferred_providers = {
    "I-8b": "replicate",
    "I-70b": "replicate",
    "405b-base": "openrouter",
    "I-405b": "replicate",
    "flux-schnell": "replicate",
    "xtts-v2": "replicate",
    "gpt-4o-or": "openrouter",
    "gpt-4o-mini-or": "openrouter",
    "gpt-4-turbo-or": "openrouter",
    "gpt-4-or": "openrouter",
    "gpt-3.5-turbo-or": "openrouter",
    "llava-13b": "replicate",
    "flux-dev-lora": "replicate",
    "gemini-pro-exp": "openrouter",
    "gemini-flash-exp": "openrouter",
    "gemini-pro": "openrouter",
    "gemini-flash": "openrouter",
    "gpt-4o-mini": "openai",
    "gpt-4o": "openai",
    "gpt-4-turbo": "openai",
    "gpt-4": "openai",
    "gpt-3.5-turbo": "openai",
    "animate-diff": "replicate",
    "dolphin": "openrouter",
    "codestral": "mistral"
}