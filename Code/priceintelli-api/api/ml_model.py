import os
import json
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "models", "xgboost_price.pkl")
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH") or DEFAULT_MODEL_PATH
if not os.path.isabs(ML_MODEL_PATH):
    ML_MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, ML_MODEL_PATH))


@router.get("/metrics")
def get_model_metrics():
    # Load metrics from JSON file
    metrics_path = os.path.join(os.path.dirname(ML_MODEL_PATH), "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(status_code=404, detail="Metrics file not found")
    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/feature-importance")
def get_feature_importance():
    # Feature importance from model
    if not os.path.exists(ML_MODEL_PATH):
        raise HTTPException(status_code=404, detail="Model not found")

    model = joblib.load(ML_MODEL_PATH)
    if hasattr(model, "feature_importances_"):
        importance = model.feature_importances_
        feature_names = getattr(model, "feature_names_in_", None)
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(importance))]
        df = pd.DataFrame({
            "feature": feature_names,
            "importance": importance,
        }).sort_values("importance", ascending=False)
        return df.to_dict(orient="records")
    else:
        raise HTTPException(status_code=400, detail="Model has no feature_importances_")


class PredictRequest(BaseModel):
    features: dict


@router.post("/predict")
def predict_price(req: PredictRequest):
    # Predict price from features
    if not os.path.exists(ML_MODEL_PATH):
        raise HTTPException(status_code=404, detail="Model not found")

    model = joblib.load(ML_MODEL_PATH)
    df = pd.DataFrame([req.features])
    prediction = model.predict(df)[0]
    return {"predicted_price": float(prediction)}
