import pandas as pd


df = pd.read_csv('model_data.csv')

models = df.iterrows()
providers = []

for _, row in models:
    #store any new providers
    new_provider = True
    for row_provider in row['providers'].split(', '):
        for provider in providers:
            if provider == row_provider:
                new_provider = False
        if new_provider:
            providers.append(row_provider)



df = pd.read_csv('samples.csv')

voice_samples = {}

for _, row in df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']
