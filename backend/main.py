from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import os


app = FastAPI(
    title="Smart-Agri API",
    description="API de prédiction de l'humidité du sol au jour suivant",
    version="1.0"
)


MODEL_PATH = os.path.join("..", "models", "rf_pipeline.pkl")

pipeline = joblib.load(MODEL_PATH)


class IrrigationInput(BaseModel):
    Soil_Type: str
    Soil_pH: float
    Soil_Moisture: float
    Organic_Carbon: float
    Electrical_Conductivity: float
    Temperature_C: float
    Humidity: float
    Rainfall_mm: float
    Sunlight_Hours: float
    Wind_Speed_kmh: float
    Crop_Type: str
    Crop_Growth_Stage: str
    Season: str
    Mulching_Used: str
    Previous_Irrigation_mm: float
    Region: str
    Stress_Index: float


@app.get("/")
def home():
    return {
        "message": "Bienvenue dans l'API Smart-Agri",
        "objectif": "Prédire l'humidité du sol au jour suivant."
    }


@app.post("/predict")
def predict(data: IrrigationInput):
    input_data = pd.DataFrame([data.model_dump()])

    prediction = pipeline.predict(input_data)[0]

    return {
        "Soil_Moisture_J1_prediction": round(float(prediction), 2),
        "unit": "%",
        "message": "Prédiction effectuée avec succès."
    }
@app.get("/health")
def health_check():
    return {
        "status": "API is running",
        "model": "rf_pipeline.pkl loaded successfully"
    }