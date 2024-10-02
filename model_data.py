import pandas as pd


df = pd.read_csv('model_data.csv')

models = []
providers = []

for _, row in df.iterrows():
    row_providers = row['providers'].split(', ')
    #store model
    models.append([
        row['model_name'],
        row['model_id'],
        row['model_type'],
        row['preferred_provider'],
        row_providers
    ])
    #store any new providers
    for row_provider in row_providers:
        for provider in providers:
            if provider == row_provider:
                break
        else:
            providers.append(row_provider)

def list_all():
    """
    Display available models and providers.

    This function prints the available models and providers to the console.
    It helps users understand the options for model and provider selection.
    """
    print("\nmodels:\n")
    for model in models:
        print(f'"{model[0]}": "{model[1]}",')
    print("\nproviders:\n")
    index = 0
    for x in providers:
        print(f'{index}. {x}')
        index += 1



df = pd.read_csv('samples.csv')

voice_samples = {}

for _, row in df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']
