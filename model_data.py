import pandas as pd


df = pd.read_csv('model_data.csv')

models = []

for _, row in df.iterrows():
    #store row of data
    models.append([
        row['model_name'],
        row['model_id'],
        row['model_type'],
        row['preferred_provider'],
        row['providers'].split(', ')
    ])



df = pd.read_csv('samples.csv')

voice_samples = {}

for _, row in df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']
