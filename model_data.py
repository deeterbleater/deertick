import pandas as pd


# Load the models CSV file
models_df = pd.read_csv('models.csv')

# Initialize dictionaries to store all model data
model_data = {}
model_index = {}
index_to_model = {}

# Iterate through each row in the DataFrame
for index, row in models_df.iterrows():
    model_name = row['name']
    model_data[model_name] = {}
    
    # Populate the dictionary with all columns for each model
    for column in models_df.columns:
        model_data[model_name][column] = row[column]
    
    # Add index mapping
    model_index[model_name] = index
    index_to_model[index] = model_name

# Load the samples CSV file
samples_df = pd.read_csv('samples.csv')

# Initialize a dictionary for voice samples
voice_samples = {}

# Populate the voice_samples dictionary
for _, row in samples_df.iterrows():
    voice_name = row['voice_name']
    voice_samples[voice_name] = row['url']

# Print some information to verify the data loading
print(f"Loaded data for {len(model_data)} models")
print(f"Loaded {len(voice_samples)} voice samples")

# Example of how to access the data:
# print(model_data['Meta: Llama 3.2 3B Instruct']['id'])
# print(model_data['Meta: Llama 3.2 3B Instruct']['context_length'])
# print(model_index['Meta: Llama 3.2 3B Instruct'])  # Get index of a model
# print(index_to_model[0])  # Get model name for index 0
