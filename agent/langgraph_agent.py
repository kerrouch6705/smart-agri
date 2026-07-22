"""
agent/langgraph_agent.py

Workflow agentique LangGraph de Smart-Agri.
C'est LA version officielle de l'agent IA, utilisee par l'application finale.

MODIFICATIONS APPORTEES PAR RAPPORT A LA VERSION ORIGINALE :
--------------------------------------------------------------
1. Le noeud check_ml_prediction n'appelle plus l'API FastAPI par HTTP
   (requests.post vers /predict-with-weather). Il appelle maintenant
   directement la fonction Python partagee
   core.prediction_service.run_prediction_with_weather().
   Raison : eviter que le backend s'appelle lui-meme inutilement par HTTP
   quand le flux est Streamlit -> FastAPI (/analyze) -> LangGraph -> FastAPI.
   Ce dernier appel HTTP est desormais remplace par un appel de fonction
   Python direct, plus rapide, plus simple et plus fiable.
2. Ajout de la fonction reutilisable run_smart_agri_analysis(field_data),
   qui encapsule la construction de l'etat initial, l'execution du graphe
   et la mise en forme du resultat final. C'est cette fonction que
   backend/main.py (endpoint /analyze) appelle.
3. Le bloc if __name__ == "__main__" est conserve tel quel pour pouvoir
   toujours tester l'agent seul depuis le terminal.
"""

from typing import TypedDict, Dict, Any
import os
import sys

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# On ajoute la racine du projet au chemin Python, pour pouvoir importer le
# module "core" (dossier frere de "agent"), que ce fichier soit lance
# directement (python agent/langgraph_agent.py) ou importe par le backend.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.prediction_service import run_prediction_with_weather  # noqa: E402


# Charger les variables depuis le fichier .env (cle GROQ_API_KEY)
load_dotenv()


# Initialisation du modele LLM Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
)


class AgentState(TypedDict):
    """
    Cette classe represente l'etat partage entre les agents du workflow LangGraph.
    Chaque agent lit et ajoute des informations dans cet etat.
    """

    field_data: Dict[str, Any]
    api_result: Dict[str, Any]
    weather_analysis: str
    agronomic_analysis: str
    decision_result: Dict[str, Any]
    final_response: str


def check_ml_prediction(state: AgentState) -> AgentState:
    """
    Node 1 : Agent de prediction ML.

    Ce node appelle directement la fonction partagee
    run_prediction_with_weather() (pas de HTTP). Elle recupere :
    - la prediction de l'humidite du sol au jour suivant
    - les donnees meteorologiques
    - l'indice de stress hydrique
    """

    field_data = state["field_data"]

    try:
        result = run_prediction_with_weather(field_data)
        state["api_result"] = {
            "success": True,
            "data": result,
        }
    except Exception as error:
        state["api_result"] = {
            "success": False,
            "error": str(error),
        }

    return state


def meteorologist_agent(state: AgentState) -> AgentState:
    """
    Node 2 : Agent Meteorologue.

    Ce node analyse les donnees meteorologiques recuperees.
    Il produit une explication simple du contexte climatique.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["weather_analysis"] = "Analyse meteo impossible a cause d'une erreur de prediction."
        return state

    data = api_result["data"]
    weather = data["weather_data_used"]

    temperature = weather["Temperature_C"]
    humidity = weather["Humidity"]
    rainfall = weather["Rainfall_mm"]
    wind_speed = weather["Wind_Speed_kmh"]

    analysis_parts = []

    if rainfall > 0:
        analysis_parts.append("Une pluie a ete detectee, ce qui peut reduire legerement le besoin d'irrigation.")
    else:
        analysis_parts.append("Aucune pluie n'a ete detectee actuellement.")

    if temperature >= 30:
        analysis_parts.append("La temperature est elevee, ce qui peut augmenter l'evaporation de l'eau.")
    else:
        analysis_parts.append("La temperature n'est pas tres elevee.")

    if humidity < 40:
        analysis_parts.append("L'humidite de l'air est faible, ce qui peut favoriser le dessechement du sol.")
    else:
        analysis_parts.append("L'humidite de l'air est acceptable.")

    if wind_speed > 15:
        analysis_parts.append("Le vent est relativement fort, ce qui peut augmenter la perte d'eau.")
    else:
        analysis_parts.append("Le vent n'est pas tres fort.")

    state["weather_analysis"] = " ".join(analysis_parts)

    return state


def agronomist_agent(state: AgentState) -> AgentState:
    """
    Node 3 : Agent Agronome.

    Ce node analyse la prediction ML et les informations agricoles.
    Il produit une analyse agronomique simple.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["agronomic_analysis"] = "Analyse agronomique impossible a cause d'une erreur de prediction."
        return state

    data = api_result["data"]
    field_data = state["field_data"]

    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]
    stress_index = data["calculated_stress_index"]

    soil_type = field_data["Soil_Type"]
    crop_type = field_data["Crop_Type"]
    crop_growth_stage = field_data["Crop_Growth_Stage"]

    if predicted_soil_moisture < 20:
        moisture_status = "L'humidite du sol prevue pour demain est faible."
    elif predicted_soil_moisture < 35:
        moisture_status = "L'humidite du sol prevue pour demain est moyenne."
    else:
        moisture_status = "L'humidite du sol prevue pour demain est suffisante."

    if stress_index >= 60:
        stress_status = "L'indice de stress hydrique est eleve."
    elif stress_index >= 35:
        stress_status = "L'indice de stress hydrique est moyen."
    else:
        stress_status = "L'indice de stress hydrique est faible."

    state["agronomic_analysis"] = (
        f"{moisture_status} "
        f"{stress_status} "
        f"La culture analysee est {crop_type}, au stade {crop_growth_stage}, "
        f"sur un sol de type {soil_type}."
    )

    return state


def decision_agent(state: AgentState) -> AgentState:
    """
    Node 4 : Agent Decisionnel.

    Ce node prend la prediction de l'humidite du sol
    et produit une decision d'irrigation.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["decision_result"] = {
            "decision": "Decision impossible",
            "risk_level": "Inconnu",
            "irrigation_level": "Inconnu",
            "reason": "Impossible de prendre une decision a cause d'une erreur de prediction.",
        }
        return state

    data = api_result["data"]
    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]

    if predicted_soil_moisture < 20:
        state["decision_result"] = {
            "decision": "Irrigation recommandee",
            "risk_level": "Eleve",
            "irrigation_level": "Forte",
            "reason": "L'humidite du sol prevue pour demain est tres faible.",
        }

    elif predicted_soil_moisture < 35:
        state["decision_result"] = {
            "decision": "Surveillance recommandee",
            "risk_level": "Moyen",
            "irrigation_level": "Legere a moderee",
            "reason": "L'humidite du sol prevue pour demain est moyenne.",
        }

    else:
        state["decision_result"] = {
            "decision": "Pas d'irrigation urgente",
            "risk_level": "Faible",
            "irrigation_level": "Aucune",
            "reason": "L'humidite du sol prevue pour demain est suffisante.",
        }

    return state


def final_response_agent(state: AgentState) -> AgentState:
    """
    Node 5 : Agent de reponse finale.

    Ce node utilise le LLM Groq pour transformer les analyses
    des agents precedents en recommandation claire pour l'agriculteur.
    """

    api_result = state["api_result"]

    if not api_result["success"]:
        state["final_response"] = (
            "Impossible de generer une recommandation, car la prediction n'a pas abouti. "
            f"Detail : {api_result.get('error', 'erreur inconnue')}"
        )
        return state

    data = api_result["data"]

    predicted_soil_moisture = data["Soil_Moisture_J1_prediction"]
    stress_index = data["calculated_stress_index"]

    weather_analysis = state["weather_analysis"]
    agronomic_analysis = state["agronomic_analysis"]
    decision_result = state["decision_result"]

    prompt = f"""
Tu es un assistant agronome virtuel dans un systeme Smart-Agri.

Tu dois donner une recommandation d'irrigation claire et simple pour un agriculteur.

Resultats du modele :
- Humidite du sol prevue pour demain : {predicted_soil_moisture} %
- Indice de stress hydrique : {stress_index}

Analyse de l'agent meteorologue :
{weather_analysis}

Analyse de l'agent agronome :
{agronomic_analysis}

Decision de l'agent decisionnel :
- Decision : {decision_result["decision"]}
- Niveau de risque : {decision_result["risk_level"]}
- Niveau d'irrigation : {decision_result["irrigation_level"]}
- Raison : {decision_result["reason"]}

Reponds exactement avec cette structure :

Decision :
...

Niveau de risque :
...

Niveau d'irrigation :
...

Explication simple :
...

Conseil pratique :
...

Regles importantes :
- Utilise un francais tres simple.
- La reponse doit etre courte.
- Ne donne pas de quantite exacte d'eau.
- Ne parle pas de litres, de millimetres ou de duree d'irrigation.
- Explique que la decision est basee principalement sur l'humidite du sol prevue pour demain.
- Ne termine pas par "Cordialement".
"""

    response = llm.invoke(prompt)

    state["final_response"] = response.content

    return state


def build_graph():
    """
    Construire le workflow LangGraph.

    Ce workflow organise les agents dans l'ordre suivant :
    1. Agent de prediction ML
    2. Agent Meteorologue
    3. Agent Agronome
    4. Agent Decisionnel
    5. Agent de reponse finale avec LLM
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


def run_smart_agri_analysis(field_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fonction reutilisable principale de l'agent Smart-Agri.

    C'est cette fonction que le backend FastAPI appelle (endpoint /analyze),
    et que Streamlit declenche indirectement via cet endpoint.

    Etapes :
    1. recoit les donnees agricoles sous forme de dictionnaire ;
    2. cree l'etat initial LangGraph ;
    3. appelle build_graph() ;
    4. execute le workflow avec invoke() ;
    5. recupere l'etat final ;
    6. verifie les erreurs ;
    7. retourne un dictionnaire Python structure et pret a etre affiche
       par le frontend Streamlit.
    """

    initial_state: AgentState = {
        "field_data": field_data,
        "api_result": {},
        "weather_analysis": "",
        "agronomic_analysis": "",
        "decision_result": {},
        "final_response": "",
    }

    graph_app = build_graph()

    try:
        final_state = graph_app.invoke(initial_state)
    except Exception as error:
        return {
            "success": False,
            "error": f"Erreur pendant l'execution du workflow LangGraph : {error}",
        }

    api_result = final_state.get("api_result", {})

    if not api_result.get("success", False):
        return {
            "success": False,
            "error": api_result.get("error", "Erreur inconnue lors de la prediction."),
        }

    prediction_data = api_result["data"]
    decision_result = final_state.get("decision_result", {})

    return {
        "success": True,
        "soil_moisture_prediction": prediction_data.get("Soil_Moisture_J1_prediction"),
        "stress_index": prediction_data.get("calculated_stress_index"),
        "region": prediction_data.get("region"),
        "weather_source": prediction_data.get("weather_source"),
        "weather_data_used": prediction_data.get("weather_data_used"),
        "weather_analysis": final_state.get("weather_analysis"),
        "agronomic_analysis": final_state.get("agronomic_analysis"),
        "decision": decision_result.get("decision"),
        "risk_level": decision_result.get("risk_level"),
        "irrigation_level": decision_result.get("irrigation_level"),
        "reason": decision_result.get("reason"),
        "final_response": final_state.get("final_response"),
    }


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
        "Region": "Souss-Massa",
    }

    result = run_smart_agri_analysis(field_data)

    print("\n======================================")
    print("Agent IA Smart-Agri avec LangGraph")
    print("======================================\n")

    if result["success"]:
        print(result["final_response"])
    else:
        print("Erreur :", result["error"])
