import pandas as pd


df = pd.read_csv('model_data.csv')

model = {}
model_type = {}
preferred_providers = {}
providers = {}

for _, row in df.iterrows():
    model_name = row['model_name']
    model[model_name] = row['model_id']
    model_type[model_name] = row['model_type']
    preferred_providers[model_name] = row['preferred_provider']
    providers[model_name] = row['providers'].split(', ')



df = pd.read_csv('samples.csv')

voice_samples = {}

for _, row in df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']
