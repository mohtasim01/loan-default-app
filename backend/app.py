"""Flask REST API - Loan Default Risk Checker (Lab manual Stage 6)."""
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request

BASE = Path(__file__).resolve().parent
BUNDLE = joblib.load(BASE / "models/model_bundle.joblib")   # trusted artifact we trained
MODEL = BUNDLE["pipeline"]                                  # preprocessing + XGBoost
FEATURES = BUNDLE["features"]                               # exact input order
TASK = BUNDLE.get("task", "classification")
CLASSES = BUNDLE.get("classes", {})

app = Flask(__name__)


@app.get("/health")
def health():
    """Quick check that the server and model are alive."""
    return jsonify(status="ok", features=len(FEATURES), task=TASK,
                   model_version=BUNDLE.get("model_version"))


@app.get("/schema")
def schema():
    """Feature names, types and allowed values (used to build the form)."""
    return jsonify(BUNDLE.get("schema", []))


@app.post("/predict")
def predict():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object"), 400

    missing = [f for f in FEATURES if f not in data]
    extra = [f for f in data if f not in FEATURES]
    if missing or extra:
        return jsonify(error="Input schema mismatch", missing=missing, extra=extra), 400

    frame = pd.DataFrame([[data[f] for f in FEATURES]], columns=FEATURES)
    try:
        prediction = int(MODEL.predict(frame)[0])
        probabilities = MODEL.predict_proba(frame)[0].tolist()
        return jsonify(prediction=prediction,
                       label=CLASSES.get(str(prediction), str(prediction)),
                       default_probability=round(probabilities[1], 4),
                       probabilities=probabilities, task=TASK,
                       disclaimer="Research/teaching prototype only - not a real credit decision.")
    except (ValueError, TypeError) as exc:
        return jsonify(error="Invalid input", detail=str(exc)), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify(error="Prediction processing failed"), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
