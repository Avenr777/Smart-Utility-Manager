import os
import joblib
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "myapp", "models")

asset_models = {}

if os.path.exists(MODEL_PATH):

    for file in os.listdir(MODEL_PATH):

        if file.endswith("_model.pkl"):

            # Example filename:
            # transformer_block_a_voltage_model.pkl

            base_name = file.replace("_model.pkl", "")

            # Split from right to separate reading_type
            parts = base_name.split("_")

            # Last part is reading_type
            reading_type = parts[-1]

            # Everything else is asset name
            asset_name = "_".join(parts[:-1])

            model_path = os.path.join(MODEL_PATH, file)
            scaler_filename = f"{asset_name}_{reading_type}_scaler.pkl"
            scaler_path = os.path.join(MODEL_PATH, scaler_filename)

            if not os.path.exists(scaler_path):
                print(f"⚠ Missing scaler for {file}")
                continue

            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)

            if asset_name not in asset_models:
                asset_models[asset_name] = {}

            asset_models[asset_name][reading_type] = {
                "model": model,
                "scaler": scaler
            }

print("Loaded structure:")
for asset in asset_models:
    print(f"{asset} → {list(asset_models[asset].keys())}")