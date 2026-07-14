import requests
from typing import TypedDict, Dict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END


# Charger les variables depuis le fichier .env
load_dotenv()

# Lien de l'API FastAPI
API_URL = "http://127.0.0.1:8000/predict-with-weather"


# Initialisation du modèle LLM Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


class AgentState(TypedDict):
    """
    Cette classe représente l'état partagé entre les agents du workflow LangGraph.
    Chaque agent lit et ajoute des informations dans cet état.
    """

    field_data: Dict[str, Any]
    api_result: Dict[str, Any]
    weather_analysis: str
    agronomic_analysis: str
    decision_result: Dict[str, Any]
    final_response: str



def check_ml_prediction(state: AgentState) -> AgentState:
    """
    Node 1 : Agent de prédiction ML.

    Ce node appelle l'API FastAPI /predict-with-weather.
    Il récupère :
    - la prédiction de l'humidité du sol au jour suivant
    - les données météorologiques
    - l'indice de stress hydrique
    """

    field_data = state["field_data"]

    try:
        response = requests.post(API_URL, json=field_data)

        if response.status_code != 200:
            state["api_result"] = {
                "success": False,
                "error": response.text
            }
            return state

        state["api_result"] = {
            "success": True,
            "data": response.json()
        }

        return state

    except requests.exceptions.ConnectionError:
        state["api_result"] = {
            "success": False,
            "error": "Impossible de se connecter à l'API FastAPI. Vérifie que le backend est démarré."
        }

        return state
    



def meteorologist_agent(state: AgentState) -> AgentState:
    """
    Node 2 : Agent Météorologue.

    Ce node analyse les données météorologiques récupérées par l'API.
    Il produit une explication simple du contexte climatique.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["weather_analysis"] = "Analyse météo impossible à cause d'une erreur API."
        return state

    data = api_result["data"]
    weather = data["weather_data_used"]

    temperature = weather["Temperature_C"]
    humidity = weather["Humidity"]
    rainfall = weather["Rainfall_mm"]
    wind_speed = weather["Wind_Speed_kmh"]

    analysis_parts = []

    if rainfall > 0:
        analysis_parts.append("Une pluie a été détectée, ce qui peut réduire légèrement le besoin d'irrigation.")
    else:
        analysis_parts.append("Aucune pluie n'a été détectée actuellement.")

    if temperature >= 30:
        analysis_parts.append("La température est élevée, ce qui peut augmenter l'évaporation de l'eau.")
    else:
        analysis_parts.append("La température n'est pas très élevée.")

    if humidity < 40:
        analysis_parts.append("L'humidité de l'air est faible, ce qui peut favoriser le dessèchement du sol.")
    else:
        analysis_parts.append("L'humidité de l'air est acceptable.")

    if wind_speed > 15:
        analysis_parts.append("Le vent est relativement fort, ce qui peut augmenter la perte d'eau.")
    else:
        analysis_parts.append("Le vent n'est pas très fort.")

    state["weather_analysis"] = " ".join(analysis_parts)

    return state





def agronomist_agent(state: AgentState) -> AgentState:
    """
    Node 3 : Agent Agronome.

    Ce node analyse la prédiction ML et les informations agricoles.
    Il produit une analyse agronomique simple.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["agronomic_analysis"] = "Analyse agronomique impossible à cause d'une erreur API."
        return state

    data = api_result["data"]
    field_data = state["field_data"]

    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]
    stress_index = data["calculated_stress_index"]

    soil_type = field_data["Soil_Type"]
    crop_type = field_data["Crop_Type"]
    crop_growth_stage = field_data["Crop_Growth_Stage"]

    if predicted_soil_moisture < 20:
        moisture_status = "L'humidité du sol prévue pour demain est faible."
    elif predicted_soil_moisture < 35:
        moisture_status = "L'humidité du sol prévue pour demain est moyenne."
    else:
        moisture_status = "L'humidité du sol prévue pour demain est suffisante."

    if stress_index >= 60:
        stress_status = "L'indice de stress hydrique est élevé."
    elif stress_index >= 35:
        stress_status = "L'indice de stress hydrique est moyen."
    else:
        stress_status = "L'indice de stress hydrique est faible."

    state["agronomic_analysis"] = (
        f"{moisture_status} "
        f"{stress_status} "
        f"La culture analysée est {crop_type}, au stade {crop_growth_stage}, "
        f"sur un sol de type {soil_type}."
    )

    return state


def decision_agent(state: AgentState) -> AgentState:
    """
    Node 4 : Agent Décisionnel.

    Ce node prend la prédiction de l'humidité du sol
    et produit une décision d'irrigation.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["decision_result"] = {
            "decision": "Décision impossible",
            "risk_level": "Inconnu",
            "irrigation_level": "Inconnu",
            "reason": "Impossible de prendre une décision à cause d'une erreur API."
        }
        return state

    data = api_result["data"]
    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]

    if predicted_soil_moisture < 20:
        state["decision_result"] = {
            "decision": "Irrigation recommandée",
            "risk_level": "Élevé",
            "irrigation_level": "Forte",
            "reason": "L'humidité du sol prévue pour demain est très faible."
        }

    elif predicted_soil_moisture < 35:
        state["decision_result"] = {
            "decision": "Surveillance recommandée",
            "risk_level": "Moyen",
            "irrigation_level": "Légère à modérée",
            "reason": "L'humidité du sol prévue pour demain est moyenne."
        }

    else:
        state["decision_result"] = {
            "decision": "Pas d'irrigation urgente",
            "risk_level": "Faible",
            "irrigation_level": "Aucune",
            "reason": "L'humidité du sol prévue pour demain est suffisante."
        }

    return state




def final_response_agent(state: AgentState) -> AgentState:
    """
    Node 5 : Agent de réponse finale.

    Ce node utilise le LLM Groq pour transformer les analyses
    des agents précédents en recommandation claire pour l'agriculteur.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["final_response"] = (
            "Impossible de générer une recommandation, car l'API n'a pas répondu correctement."
        )
        return state

    data = api_result["data"]

    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]
    stress_index = data["calculated_stress_index"]

    weather_analysis = state["weather_analysis"]
    agronomic_analysis = state["agronomic_analysis"]
    decision_result = state["decision_result"]

    prompt = f"""
Tu es un assistant agronome virtuel dans un système Smart-Agri.

Tu dois donner une recommandation d'irrigation claire et simple pour un agriculteur.

Résultats du modèle :
- Humidité du sol prévue pour demain : {predicted_soil_moisture} %
- Indice de stress hydrique : {stress_index}

Analyse de l'agent météorologue :
{weather_analysis}

Analyse de l'agent agronome :
{agronomic_analysis}

Décision de l'agent décisionnel :
- Décision : {decision_result["decision"]}
- Niveau de risque : {decision_result["risk_level"]}
- Niveau d'irrigation : {decision_result["irrigation_level"]}
- Raison : {decision_result["reason"]}

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
- La réponse doit être courte.
- Ne donne pas de quantité exacte d'eau.
- Ne parle pas de litres, de millimètres ou de durée d'irrigation.
- Explique que la décision est basée principalement sur l'humidité du sol prévue pour demain.
- Ne termine pas par "Cordialement".
"""

    response = llm.invoke(prompt)

    state["final_response"] = response.content

    return state



def build_graph():
    """
    Construire le workflow LangGraph.

    Ce workflow organise les agents dans l'ordre suivant :
    1. Agent de prédiction ML
    2. Agent Météorologue
    3. Agent Agronome
    4. Agent Décisionnel
    5. Agent de réponse finale avec LLM
    """

    graph = StateGraph(AgentState)

    graph.add_node("check_ml_prediction", check_ml_prediction)
    graph.add_node("meteorologist_agent", meteorologist_agent)
    graph.add_node("agronomist_agent", agronomist_agent)
    graph.add_node("decision_agent", decision_agent)
    graph.add_node("final_response_agent", final_response_agent)

    graph.set_entry_point("check_ml_prediction")

    graph.add_edge("check_ml_prediction", "meteorologist_agent")
    graph.add_edge("meteorologist_agent", "agronomist_agent")
    graph.add_edge("agronomist_agent", "decision_agent")
    graph.add_edge("decision_agent", "final_response_agent")
    graph.add_edge("final_response_agent", END)

    return graph.compile()


if __name__ == "__main__":

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

    initial_state = {
        "field_data": field_data,
        "api_result": {},
        "weather_analysis": "",
        "agronomic_analysis": "",
        "decision_result": {},
        "final_response": ""
    }

    app = build_graph()

    final_state = app.invoke(initial_state)

    print("\n======================================")
    print("Agent IA Smart-Agri avec LangGraph")
    print("======================================\n")

    print(final_state["final_response"])


    