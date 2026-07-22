"""
frontend/utils/storage.py

Stockage local de l'historique des analyses.

Pourquoi un fichier JSON et pas st.session_state ?
----------------------------------------------------
- st.session_state est reinitialise a chaque nouveau demarrage du serveur
  Streamlit, et n'est pas partage entre plusieurs onglets/sessions.
- Un fichier JSON local (frontend/data/history.json) persiste sur le
  disque : l'historique reste disponible meme apres avoir ferme et
  rouvert l'application, tant que c'est le meme ordinateur/serveur.

C'est une solution TEMPORAIRE pour la demonstration de stage. Il n'y a
pas de vraie base de donnees. Une evolution future recommandee est
d'utiliser SQLite + SQLAlchemy avec de vrais endpoints FastAPI dedies a
l'historique (voir README).
"""

import json
import os
import uuid
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")


def _ensure_storage_ready():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)


def load_history() -> list:
    """Retourne la liste de toutes les analyses enregistrees, la plus recente en premier."""
    _ensure_storage_ready()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        history = []

    history.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return history


def _save_history(history: list):
    _ensure_storage_ready()
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


def add_analysis(record: dict) -> dict:
    """
    Ajoute une nouvelle analyse a l'historique.

    `record` doit contenir les donnees du formulaire (parcelle, region,
    sol, culture...) ET le resultat retourne par l'API (/analyze).

    Retourne le record complet, avec un identifiant unique et une date.
    """
    history = load_history()

    record = dict(record)
    record["id"] = str(uuid.uuid4())
    record["created_at"] = datetime.now().isoformat(timespec="seconds")

    history.append(record)
    _save_history(history)

    return record


def get_analysis_by_id(analysis_id: str):
    history = load_history()
    for record in history:
        if record.get("id") == analysis_id:
            return record
    return None


def delete_analysis(analysis_id: str) -> bool:
    history = load_history()
    new_history = [record for record in history if record.get("id") != analysis_id]

    if len(new_history) == len(history):
        return False

    _save_history(new_history)
    return True


def clear_history():
    _save_history([])
