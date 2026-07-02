from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import requests 

app = FastAPI(
    title="Smart-Agri API",
    description="API de prédiction de l'humidité du sol au jour suivant",
    version="1.0"
)


MODEL_PATH = os.path.join("..", "models", "rf_pipeline.pkl")

pipeline = joblib.load(MODEL_PATH)

REGION_COORDINATES = {
    "Souss-Massa": {"latitude": 30.4278, "longitude": -9.5981},
    "Agadir": {"latitude": 30.4278, "longitude": -9.5981},
    "Taroudant": {"latitude": 30.4703, "longitude": -8.8769},
    "Marrakech": {"latitude": 31.6295, "longitude": -7.9811},
    "Casablanca": {"latitude": 33.5731, "longitude": -7.5898}
}


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
  
class IrrigationWithWeatherInput(BaseModel):
    
    Soil_Type: str
    Soil_pH: float
    Soil_Moisture: float
    Organic_Carbon: float
    Electrical_Conductivity: float

    Crop_Type: str
    Crop_Growth_Stage: str
    Season: str
    Mulching_Used: str
    Previous_Irrigation_mm: float
    Region: str

    Stress_Index: float






def get_weather_from_open_meteo(latitude: float, longitude: float):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m,sunshine_duration",
        "wind_speed_unit": "kmh"
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    current = data["current"]

    weather_data = {
        "Temperature_C": current.get("temperature_2m", 0),
        "Humidity": current.get("relative_humidity_2m", 0),
        "Rainfall_mm": current.get("rain", 0),
        "Wind_Speed_kmh": current.get("wind_speed_10m", 0),
        "Sunlight_Hours": current.get("sunshine_duration", 0) / 3600
    }

    return weather_data




@app.get("/")
def home():
    return {
        "message": "Bienvenue dans l'API Smart-Agri",
        "objectif": "Prédire l'humidité du sol au jour suivant."
    }


@app.get("/health")
def health_check():
    return {
        "status": "API is running",
        "model": "rf_pipeline.pkl loaded successfully"
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



@app.post("/predict-with-weather")
def predict_with_weather(data: IrrigationWithWeatherInput):

    if data.Region not in REGION_COORDINATES:
        raise HTTPException(
            status_code=400,
            detail=f"Region '{data.Region}' non supportée. Régions disponibles : {list(REGION_COORDINATES.keys())}"
        )

    coordinates = REGION_COORDINATES[data.Region]

    weather_data = get_weather_from_open_meteo(
        latitude=coordinates["latitude"],
        longitude=coordinates["longitude"]
    )

    input_data = {
        "Soil_Type": data.Soil_Type,
        "Soil_pH": data.Soil_pH,
        "Soil_Moisture": data.Soil_Moisture,
        "Organic_Carbon": data.Organic_Carbon,
        "Electrical_Conductivity": data.Electrical_Conductivity,

        "Temperature_C": weather_data["Temperature_C"],
        "Humidity": weather_data["Humidity"],
        "Rainfall_mm": weather_data["Rainfall_mm"],
        "Sunlight_Hours": weather_data["Sunlight_Hours"],
        "Wind_Speed_kmh": weather_data["Wind_Speed_kmh"],

        "Crop_Type": data.Crop_Type,
        "Crop_Growth_Stage": data.Crop_Growth_Stage,
        "Season": data.Season,
        "Mulching_Used": data.Mulching_Used,
        "Previous_Irrigation_mm": data.Previous_Irrigation_mm,
        "Region": data.Region,
        "Stress_Index": data.Stress_Index
    }

    input_df = pd.DataFrame([input_data])

    prediction = pipeline.predict(input_df)[0]

    return {
        "weather_source": "Open-Meteo",
        "region": data.Region,
        "coordinates_used": coordinates,
        "weather_data_used": weather_data,
        "Soil_Moisture_J1_prediction": round(float(prediction), 2),
        "unit": "%",
        "message": "Prédiction effectuée avec les données météo Open-Meteo."
    }