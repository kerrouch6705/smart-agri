"""
frontend/pages/5_Parametres.py

Page de paramètres : nom affiché, thème, adresse du backend, test de
disponibilité, vidage de l'historique local, déconnexion.
"""

import streamlit as st

from components.styles import apply_custom_css, header_banner
from components.sidebar import render_sidebar
from utils.auth import require_login, logout
from utils.storage import clear_history
from services.api_service import get_api_base_url, check_backend_health

st.set_page_config(page_title="Smart-Agri — Paramètres", page_icon="🌱", layout="wide")
apply_custom_css()
require_login()
render_sidebar()

header_banner("Paramètres")

# --- Profil ------------------------------------------------------------
st.markdown("### 👤 Profil")
display_name = st.text_input(
    "Nom affiché dans l'application",
    value=st.session_state.get("display_name", "Utilisateur Smart-Agri"),
)
if st.button("Enregistrer le nom"):
    st.session_state["display_name"] = display_name
    st.success("Nom mis à jour.")

st.markdown("---")

# --- Apparence -----------------------------------------------------------
st.markdown("### 🎨 Apparence")
theme_choice = st.radio(
    "Mode d'affichage",
    ["Clair", "Sombre"],
    index=0 if st.session_state.get("theme", "Clair") == "Clair" else 1,
    horizontal=True,
)
st.session_state["theme"] = theme_choice
st.caption(
    "ℹ️ Streamlit gère le thème sombre nativement via le menu ⋮ (Settings > "
    "Theme) en haut à droite de l'application. Cette option enregistre "
    "votre préférence, mais son application automatique n'est pas garantie "
    "sur toutes les versions de Streamlit."
)

st.markdown("---")

# --- Backend -------------------------------------------------------------
st.markdown("### 🔌 Connexion au backend")
st.write(f"**Adresse actuelle du backend :** `{get_api_base_url()}`")
st.caption("Pour changer cette adresse, définissez la variable d'environnement API_BASE_URL avant de lancer Streamlit.")

if st.button("Tester la disponibilité du backend"):
    with st.spinner("Test en cours..."):
        ok, message = check_backend_health()
    if ok:
        st.success(message)
    else:
        st.error(message)

st.markdown("---")

# --- Données locales -------------------------------------------------------
st.markdown("### 🗂️ Données locales")
st.caption("L'historique est stocké dans un fichier JSON local (frontend/data/history.json), pas dans une vraie base de données.")

confirm_clear = st.checkbox("Je confirme vouloir supprimer tout l'historique local.")
if st.button("🗑️ Vider l'historique local", disabled=not confirm_clear):
    clear_history()
    st.success("Historique local vidé.")

st.markdown("---")

# --- Deconnexion -----------------------------------------------------------
st.markdown("### 🚪 Session")
if st.button("Se déconnecter", type="primary"):
    logout()
    st.switch_page("app.py")
