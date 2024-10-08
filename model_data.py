from enum import Enum
import pandas as pd



class ModelHead(Enum):
    name = 0
    id = 1
    type = 2
    preferred_provider = 3
    providers = 4

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

# Populate the voice_samples dictionary
for _, row in df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']

# Print some information to verify the data loading
print(f"Loaded data for {len(models)} models")
print(f"Loaded {len(voice_samples)} voice samples")

# Example of how to access the data (WIP):
# print(model_data['Meta: Llama 3.2 3B Instruct']['id'])
# print(model_data['Meta: Llama 3.2 3B Instruct']['context_length'])
# print(model_index['Meta: Llama 3.2 3B Instruct'])  # Get index of a model
# print(index_to_model[0])  # Get model name for index 0
