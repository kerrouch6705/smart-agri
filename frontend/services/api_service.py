"""
frontend/services/api_service.py

Ce fichier centralise TOUS les appels HTTP vers le backend FastAPI.
Aucun autre fichier du frontend ne doit appeler `requests` directement
vers le backend : cela evite de repeter l'adresse du backend partout
et centralise la gestion des erreurs.
"""

import os
import requests

# Adresse du backend FastAPI. Peut etre surchargee avec la variable
# d'environnement API_BASE_URL (utile si le backend tourne ailleurs
# qu'en local, par exemple sur un serveur de demonstration).
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Delai d'attente (en secondes). Plus long que la normale car l'endpoint
# /analyze appelle la meteo (Open-Meteo) ET le LLM (Groq), ce qui peut
# prendre plusieurs secondes.
DEFAULT_TIMEOUT = 45


def get_api_base_url() -> str:
    return API_BASE_URL


def check_backend_health():
    """
    Verifie que le backend FastAPI repond.

    Retourne un tuple (ok: bool, message: str).
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, "Le backend FastAPI est disponible."
        return False, f"Le backend a repondu avec un code inattendu : {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Impossible de se connecter au backend. Verifiez qu'il est demarre (uvicorn main:app)."
    except requests.exceptions.Timeout:
        return False, "Le backend met trop de temps a repondre (timeout)."
    except Exception as error:
        return False, f"Erreur inattendue lors du test du backend : {error}"


def analyze_field(payload: dict):
    """
    Appelle POST /analyze sur le backend FastAPI : execute le workflow
    LangGraph complet (prediction ML + meteo + analyses + decision +
    recommandation Groq).

    Retourne un tuple (success: bool, data_or_message).
    - Si success est True, data_or_message est le dictionnaire de resultat.
    - Si success est False, data_or_message est un message d'erreur simple,
      pret a etre affiche avec st.error().
    """
    url = f"{API_BASE_URL}/analyze"

    try:
        response = requests.post(url, json=payload, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.ConnectionError:
        return False, (
            "Impossible de se connecter au backend FastAPI. "
            "Verifiez qu'il est bien demarre sur "
            f"{API_BASE_URL} (commande : uvicorn main:app --reload)."
        )
    except requests.exceptions.Timeout:
        return False, "Le backend met trop de temps a repondre (timeout). Reessayez."
    except requests.exceptions.RequestException as error:
        return False, f"Erreur reseau lors de l'appel au backend : {error}"

    # Erreur de validation des donnees envoyees (champ manquant, type invalide, etc.)
    if response.status_code == 422:
        return False, "Les donnees envoyees ne sont pas valides (erreur 422). Verifiez le formulaire."

    # Erreur interne du backend (modele, meteo, Groq, LangGraph...)
    if response.status_code == 500:
        try:
            detail = response.json().get("detail", "Erreur interne du serveur.")
        except ValueError:
            detail = "Erreur interne du serveur (reponse illisible)."
        return False, f"Erreur cote backend : {detail}"

    if response.status_code == 400:
        try:
            detail = response.json().get("detail", "Requete invalide.")
        except ValueError:
            detail = "Requete invalide."
        return False, detail

    if response.status_code != 200:
        return False, f"Le backend a repondu avec un code inattendu : {response.status_code}"

    try:
        data = response.json()
    except ValueError:
        return False, "La reponse du backend n'est pas un JSON valide (reponse incomplete)."

    if not isinstance(data, dict):
        return False, "Reponse du backend inattendue."

    if not data.get("success", False):
        return False, data.get("error", "L'analyse a echoue pour une raison inconnue.")

    return True, data
