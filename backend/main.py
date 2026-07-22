"""
backend/main.py

API FastAPI de Smart-Agri.

MODIFICATIONS APPORTEES PAR RAPPORT A LA VERSION ORIGINALE :
--------------------------------------------------------------
1. Toute la logique (chargement du modele, meteo Open-Meteo, calcul du
   stress hydrique, prediction) a ete deplacee dans core/prediction_service.py
   pour etre partagee avec l'agent LangGraph, sans duplication de code et
   sans que le backend ait besoin de s'appeler lui-meme par HTTP.
2. Un nouvel endpoint POST /analyze a ete ajoute : il execute le workflow
   complet LangGraph (prediction ML + analyse meteo + analyse agronomique +
   decision + recommandation Groq) et retourne un resultat structure.
   C'est cet endpoint que le frontend Streamlit appelle pour "Nouvelle analyse".
3. Le chemin et le nom du modele (models/rf_pipeline.pkl) n'ont PAS ete
   modifies.
"""

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

# On ajoute la racine du projet (le dossier parent de backend/) au chemin
# Python. Cela permet d'importer "core" et "agent", qui sont des dossiers
# freres de "backend", peu importe le dossier depuis lequel uvicorn est lance.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.prediction_service import run_prediction_with_weather, pipeline  # noqa: E402


app = FastAPI(
    title="Smart-Agri API",
    description="API de prediction de l'humidite du sol et de recommandation d'irrigation",
    version="1.1",
)

# CORS ouvert : utile pour que le frontend Streamlit (autre port) puisse
# appeler l'API sans etre bloque par le navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# MODELES PYDANTIC (schemas des requetes)
# ==================================================
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


# ==================================================
# ROUTES DE BASE
# ==================================================
@app.get("/")
def home():
    return {
        "message": "Bienvenue dans l'API Smart-Agri",
        "objectif": "Predire l'humidite du sol au jour suivant et recommander une irrigation.",
    }


@app.get("/health")
def health_check():
    return {
        "status": "API is running",
        "model": "rf_pipeline.pkl loaded successfully",
    }


# ==================================================
# PREDICTION SIMPLE (donnees meteo fournies manuellement)
# ==================================================
@app.post("/predict")
def predict(data: IrrigationInput):
    input_data = pd.DataFrame([data.model_dump()])
    prediction = pipeline.predict(input_data)[0]

    return {
        "Soil_Moisture_J1_prediction": round(float(prediction), 2),
        "unit": "%",
        "message": "Prediction effectuee avec succes.",
    }


# ==================================================
# PREDICTION AVEC METEO AUTOMATIQUE (Open-Meteo)
# ==================================================
@app.post("/predict-with-weather")
def predict_with_weather(data: IrrigationWithWeatherInput):
    try:
        return run_prediction_with_weather(data.model_dump())
    except ValueError as error:
        # Region non supportee
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Erreur de prediction : {error}")


# ==================================================
# ANALYSE COMPLETE (workflow agentique LangGraph + Groq)
# ==================================================
@app.post("/analyze")
def analyze(data: IrrigationWithWeatherInput):
    """
    Endpoint principal utilise par le frontend Streamlit.

    Il execute le workflow LangGraph complet :
    1. prediction ML + meteo (via core.prediction_service, appel direct,
       pas de HTTP) ;
    2. analyse meteorologique ;
    3. analyse agronomique ;
    4. decision d'irrigation ;
    5. recommandation finale generee par Groq.
    """
    # Import local pour eviter tout probleme d'ordre d'import au demarrage
    # (l'agent charge sa cle Groq via load_dotenv() a l'import).
    from agent.langgraph_agent import run_smart_agri_analysis

    try:
        result = run_smart_agri_analysis(data.model_dump())
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse agentique : {error}",
        )

    if not result.get("success", False):
        # On ne leve pas d'exception HTTP ici : le frontend affichera
        # proprement le message d'erreur contenu dans la reponse.
        return result

    return result
