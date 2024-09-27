from pathlib import Path

import pandas as pd

df = pd.read_csv((Path(__file__).parent / ".." / "model_data.csv").resolve())

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
