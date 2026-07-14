import requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Charger les variables depuis le fichier .env
load_dotenv()

# Lien de l'API FastAPI
API_URL = "http://127.0.0.1:8000/predict-with-weather"


def get_prediction_from_api(field_data):
    """
    Tool 1 : appeler l'API FastAPI pour récupérer
    la prédiction ML, la météo et l'indice de stress.
    """

    try:
        response = requests.post(API_URL, json=field_data)

        if response.status_code != 200:
            return {
                "success": False,
                "error": response.text
            }

        return {
            "success": True,
            "data": response.json()
        }

    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Impossible de se connecter à l'API FastAPI. Vérifie que le backend est démarré."
        }


def make_irrigation_decision(predicted_soil_moisture):
    """
    Tool 2 : analyser la prédiction de l'humidité du sol
    et produire une décision d'irrigation.
    """

    if predicted_soil_moisture < 20:
        return {
            "decision": "Irrigation recommandée",
            "risk_level": "Élevé",
            "irrigation_level": "Forte",
            "reason": "L'humidité du sol prévue pour demain est très faible."
        }

    elif predicted_soil_moisture < 35:
        return {
            "decision": "Surveillance recommandée",
            "risk_level": "Moyen",
            "irrigation_level": "Légère à modérée",
            "reason": "L'humidité du sol prévue pour demain est moyenne."
        }

    else:
        return {
            "decision": "Pas d'irrigation urgente",
            "risk_level": "Faible",
            "irrigation_level": "Aucune",
            "reason": "L'humidité du sol prévue pour demain est suffisante."
        }


def generate_llm_advice(api_result, decision_result):
    """
    Tool 3 : utiliser le LLM Groq pour transformer
    les résultats techniques en recommandation claire.
    """

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    predicted_soil_moisture = api_result["Soil_Moisture_J1_prediction"]
    stress_index = api_result["calculated_stress_index"]
    weather = api_result["weather_data_used"]

    prompt = f"""
Tu es un assistant agronome virtuel dans un système Smart-Agri.

Ta mission est d'aider un agriculteur à comprendre s'il doit irriguer demain ou non.

Données techniques du système :
- Humidité du sol prévue pour demain : {predicted_soil_moisture} %
- Indice de stress hydrique : {stress_index}
- Température actuelle : {weather["Temperature_C"]} °C
- Humidité de l'air : {weather["Humidity"]} %
- Pluie détectée : {weather["Rainfall_mm"]} mm
- Vitesse du vent : {weather["Wind_Speed_kmh"]} km/h

Décision calculée :
- Décision : {decision_result["decision"]}
- Niveau de risque : {decision_result["risk_level"]}
- Niveau d'irrigation : {decision_result["irrigation_level"]}
- Raison principale : {decision_result["reason"]}

Réponds exactement avec cette structure :

Décision :
...

Niveau de risque :
...

Niveau d'irrigation :
...

Explication simple :
...

Conseil pratique :
...

Règles importantes :
- Utilise un français très simple.
- Ne donne pas de quantité exacte d'eau.
- Ne parle pas de litres, mm ou durée d'irrigation.
- La réponse doit être courte.
- Explique que la décision est basée surtout sur l'humidité du sol prévue pour demain.
- Ne termine pas par "Cordialement".
"""

    response = llm.invoke(prompt)

    return response.content


if __name__ == "__main__":

    # Exemple de données du champ
    field_data = {
        "Soil_Type": "Clay",
        "Soil_pH": 7.85,
        "Soil_Moisture": 15.25,
        "Organic_Carbon": 1.18,
        "Electrical_Conductivity": 1.41,
        "Crop_Type": "Wheat",
        "Crop_Growth_Stage": "Vegetative",
        "Season": "Summer",
        "Mulching_Used": "Yes",
        "Previous_Irrigation_mm": 5,
        "Region": "Souss-Massa"
    }

    # 1. Appeler l'API ML
    prediction_result = get_prediction_from_api(field_data)

    if prediction_result["success"]:

        api_data = prediction_result["data"]

        # 2. Récupérer la prédiction
        predicted_soil_moisture = api_data["Soil_Moisture_J1_prediction"]

        # 3. Prendre la décision
        decision = make_irrigation_decision(predicted_soil_moisture)

        # 4. Générer la réponse avec Groq LLM
        final_advice = generate_llm_advice(api_data, decision)

        print("\n==============================")
        print("Agent IA Smart-Agri avec Groq")
        print("==============================\n")
        print(final_advice)

    else:
        print("Erreur lors de l'appel à l'API :")
        print(prediction_result["error"])