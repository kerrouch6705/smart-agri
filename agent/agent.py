import requests

# Lien de l'API FastAPI
API_URL = "http://127.0.0.1:8000/predict-with-weather"


def get_prediction_from_api(field_data):
    """
    Cette fonction envoie les données du champ à l'API FastAPI
    et récupère la prédiction du modèle ML.
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
            "error": "Impossible de se connecter à l'API. Vérifie que FastAPI est bien démarrée."
        }


def make_irrigation_decision(predicted_soil_moisture):
    """
    Cette fonction prend uniquement la prédiction de l'humidité du sol
    et donne une décision d'irrigation.

    La décision est basée sur Soil_Moisture_J1_prediction.
    Les seuils utilisés sont heuristiques pour une première version du prototype.
    """

    if predicted_soil_moisture < 20:
        return {
            "decision": "Irrigation recommandée",
            "risk_level": "Élevé",
            "reason": "L'humidité du sol prévue pour demain est faible."
        }

    elif predicted_soil_moisture < 35:
        return {
            "decision": "Surveillance recommandée",
            "risk_level": "Moyen",
            "reason": "L'humidité du sol prévue est moyenne. Il faut surveiller la parcelle."
        }

    else:
        return {
            "decision": "Pas d'irrigation urgente",
            "risk_level": "Faible",
            "reason": "L'humidité du sol prévue est suffisante."
        }


def estimate_irrigation_level(predicted_soil_moisture):
    """
    Cette fonction estime le niveau général d'irrigation
    à partir de l'humidité du sol prévue pour demain.

    Il s'agit d'une recommandation qualitative pour le prototype,
    pas d'un calcul exact de volume d'eau.
    """

    if predicted_soil_moisture < 15:
        return {
            "irrigation_level": "Forte",
            "explanation": "Le déficit d'humidité prévu est important."
        }

    elif predicted_soil_moisture < 25:
        return {
            "irrigation_level": "Modérée",
            "explanation": "Le déficit d'humidité prévu est moyen."
        }

    elif predicted_soil_moisture < 35:
        return {
            "irrigation_level": "Légère",
            "explanation": "Le déficit d'humidité prévu est faible."
        }

    else:
        return {
            "irrigation_level": "Aucune",
            "explanation": "L'humidité prévue est suffisante."
        }


def generate_advice(api_result, decision_result, irrigation_level_result):
    """
    Cette fonction transforme les résultats techniques en message simple
    pour l'agriculteur.
    """

    predicted_soil_moisture = api_result["Soil_Moisture_J1_prediction"]
    stress_index = api_result["calculated_stress_index"]
    weather = api_result["weather_data_used"]

    advice = f"""
==============================
Conseil d'irrigation Smart-Agri
==============================

Décision : {decision_result["decision"]}

Niveau de risque : {decision_result["risk_level"]}

Niveau d'irrigation : {irrigation_level_result["irrigation_level"]}

Explication :
{decision_result["reason"]}
{irrigation_level_result["explanation"]}

Résultat principal du modèle :
- Humidité du sol prévue demain : {predicted_soil_moisture} %

Informations contextuelles :
- Indice de stress hydrique calculé : {stress_index}
- Température actuelle : {weather["Temperature_C"]} °C
- Humidité de l'air : {weather["Humidity"]} %
- Pluie détectée : {weather["Rainfall_mm"]} mm
- Vitesse du vent : {weather["Wind_Speed_kmh"]} km/h

Remarque :
La décision d'irrigation est basée principalement sur l'humidité du sol prévue.
Le niveau d'irrigation proposé est qualitatif pour cette version du prototype.
Les données météo et l'indice de stress sont affichés pour expliquer le contexte.
"""

    return advice


if __name__ == "__main__":

    # Exemple de données envoyées à l'API
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

    # 1. Appeler l'API
    prediction_result = get_prediction_from_api(field_data)

    # 2. Vérifier si l'API a bien répondu
    if prediction_result["success"]:

        api_data = prediction_result["data"]

        # 3. Récupérer seulement la prédiction du modèle
        predicted_soil_moisture = api_data["Soil_Moisture_J1_prediction"]

        # 4. Prendre la décision à partir de la prédiction
        decision = make_irrigation_decision(predicted_soil_moisture)

        # 5. Estimer le niveau qualitatif d'irrigation
        irrigation_level = estimate_irrigation_level(predicted_soil_moisture)

        # 6. Générer un message clair
        advice = generate_advice(api_data, decision, irrigation_level)

        print(advice)

    else:
        print("Erreur lors de l'appel à l'API :")
        print(prediction_result["error"])