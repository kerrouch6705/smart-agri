"""
frontend/utils/auth.py

Authentification de DEMONSTRATION uniquement.

Analyse effectuee avant de coder cette partie : le backend FastAPI fourni
(backend/main.py) ne contient AUCUN systeme d'authentification reel
(pas de gestion d'utilisateurs, pas de mots de passe, pas de token JWT).

Cette page de connexion ne doit donc jamais laisser croire qu'il s'agit
d'une authentification securisee. Elle sert uniquement a :
- proteger l'acces aux pages de l'application pendant la demonstration ;
- illustrer comment une vraie authentification pourrait etre branchee
  plus tard (voir la section "Ameliorations futures" du README).

Identifiants de demonstration (a afficher a l'ecran de connexion) :
    email    : demo@smartagri.ma
    mot de passe : smartagri2026
"""

import streamlit as st

DEMO_EMAIL = "demo@smartagri.ma"
DEMO_PASSWORD = "smartagri2026"


def try_login(email: str, password: str) -> bool:
    """
    Verifie les identifiants de demonstration.
    Retourne True et met a jour st.session_state si c'est correct.
    """
    if email.strip().lower() == DEMO_EMAIL and password == DEMO_PASSWORD:
        st.session_state["logged_in"] = True
        st.session_state["user_email"] = email.strip().lower()
        st.session_state.setdefault("display_name", "Utilisateur Smart-Agri")
        return True

    return False


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def logout():
    st.session_state["logged_in"] = False
    st.session_state.pop("user_email", None)


def require_login():
    """
    A appeler tout en haut de chaque page protegee (Dashboard, Nouvelle
    analyse, Historique, Detail, Parametres).

    Si l'utilisateur n'est pas connecte, affiche un message et arrete
    l'execution de la page avec st.stop().
    """
    if not is_logged_in():
        st.warning("Vous devez vous connecter pour acceder a cette page.")
        st.page_link("app.py", label="Aller a la page de connexion", icon="🔐")
        st.stop()
