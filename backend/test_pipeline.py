"""Stage 5: run the saved model directly (no Flask) on the sample payload."""
from pathlib import Path
import json

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
bundle = joblib.load(ROOT / "backend/models/model_bundle.joblib")
with (ROOT / "backend/test_payload.json").open(encoding="utf-8") as f:
    payload = json.load(f)

features = bundle["features"]
assert set(features) == set(payload), "Payload keys must match features"
frame = pd.DataFrame([[payload[f] for f in features]], columns=features)
model = bundle["pipeline"]
print("Prediction:", model.predict(frame).tolist())
print("Probabilities:", model.predict_proba(frame).tolist())
print("PASS: local inference")
