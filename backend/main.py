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


STRESS_RANGES = {
    "Soil_Moisture": {"min": 8.0, "max": 65.0},
    "Temperature_C": {"min": 12.0, "max": 42.0},
    "Humidity": {"min": 25.0, "max": 95.0},
    "Rainfall_mm": {"min": 0.38, "max": 2499.69},
    "Sunlight_Hours": {"min": 4.0, "max": 11.0},
    "Wind_Speed_kmh": {"min": 0.5, "max": 20.0},
    "Electrical_Conductivity": {"min": 0.1, "max": 3.5},
    "Previous_Irrigation_mm": {"min": 0.02, "max": 119.99},
}


def normalize_value(value: float, column_name: str):
    col_min = STRESS_RANGES[column_name]["min"]
    col_max = STRESS_RANGES[column_name]["max"]

    if col_max == col_min:
        return 0

    normalized = (value - col_min) / (col_max - col_min)

    return max(0, min(normalized, 1))



def calculate_stress_index(
    soil_moisture: float,
    temperature_c: float,
    humidity: float,
    rainfall_mm: float,
    sunlight_hours: float,
    wind_speed_kmh: float,
    electrical_conductivity: float,
    previous_irrigation_mm: float,
    soil_type: str,
    crop_type: str,
    crop_growth_stage: str,
    mulching_used: str
):
    soil_dryness = 1 - normalize_value(soil_moisture, "Soil_Moisture")
    high_temperature = normalize_value(temperature_c, "Temperature_C")
    low_humidity = 1 - normalize_value(humidity, "Humidity")
    low_rainfall = 1 - normalize_value(rainfall_mm, "Rainfall_mm")
    high_sunlight = normalize_value(sunlight_hours, "Sunlight_Hours")
    high_wind = normalize_value(wind_speed_kmh, "Wind_Speed_kmh")
    high_ec = normalize_value(electrical_conductivity, "Electrical_Conductivity")
    low_previous_irrigation = 1 - normalize_value(previous_irrigation_mm, "Previous_Irrigation_mm")

    soil_weight = {
        "Sandy": 1.00,
        "Loamy": 0.55,
        "Silt": 0.45,
        "Clay": 0.30
    }.get(soil_type, 0.50)

    stage_weight = {
        "Sowing": 0.75,
        "Vegetative": 1.00,
        "Flowering": 0.90,
        "Harvest": 0.45
    }.get(crop_growth_stage, 0.60)

    crop_weight = {
        "Rice": 1.00,
        "Sugarcane": 0.95,
        "Cotton": 0.85,
        "Maize": 0.75,
        "Wheat": 0.65,
        "Soybean": 0.60
    }.get(crop_type, 0.70)

    mulch_factor = {
        "Yes": 0.85,
        "No": 1.00
    }.get(mulching_used, 1.00)

    base_stress = (
        0.30 * soil_dryness +
        0.15 * high_temperature +
        0.12 * low_humidity +
        0.15 * low_rainfall +
        0.08 * high_sunlight +
        0.05 * high_wind +
        0.05 * high_ec +
        0.05 * low_previous_irrigation +
        0.05 * soil_weight
    )

    stress_index = (
        base_stress
        * (0.80 + 0.20 * crop_weight)
        * (0.85 + 0.15 * stage_weight)
        * mulch_factor
        * 100
    )

    stress_index = max(0, min(stress_index, 100))

    return round(stress_index, 2)


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
     

    stress_index = calculate_stress_index(
       soil_moisture=data.Soil_Moisture,
       temperature_c=weather_data["Temperature_C"],
       humidity=weather_data["Humidity"],
       rainfall_mm=weather_data["Rainfall_mm"],
       sunlight_hours=weather_data["Sunlight_Hours"],
       wind_speed_kmh=weather_data["Wind_Speed_kmh"],
       electrical_conductivity=data.Electrical_Conductivity,
       previous_irrigation_mm=data.Previous_Irrigation_mm,
       soil_type=data.Soil_Type,
      crop_type=data.Crop_Type,
       crop_growth_stage=data.Crop_Growth_Stage,
       mulching_used=data.Mulching_Used
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
        "Stress_Index": stress_index
    }

    input_df = pd.DataFrame([input_data])

    prediction = pipeline.predict(input_df)[0]

    return {
        "weather_source": "Open-Meteo",
        "region": data.Region,
        "coordinates_used": coordinates,
        "weather_data_used": weather_data,
        "calculated_stress_index": stress_index,
        "Soil_Moisture_J1_prediction": round(float(prediction), 2),
        "unit": "%",
        "message": "Prédiction effectuée avec les données météo Open-Meteo."
    }