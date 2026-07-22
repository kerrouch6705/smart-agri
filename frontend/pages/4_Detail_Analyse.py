"""
frontend/pages/4_Detail_Analyse.py

Affiche le détail complet d'une analyse choisie depuis l'historique.
"""

import streamlit as st

from components.styles import apply_custom_css, header_banner
from components.sidebar import render_sidebar
from components.cards import render_analysis_result
from utils.auth import require_login
from utils.storage import get_analysis_by_id

st.set_page_config(page_title="Smart-Agri — Détail de l'analyse", page_icon="🌱", layout="wide")
apply_custom_css()
require_login()
render_sidebar()

header_banner("Détail de l'analyse")

analysis_id = st.session_state.get("selected_analysis_id")

if not analysis_id:
    st.info("Aucune analyse sélectionnée. Choisissez-en une depuis l'historique.")
    if st.button("Aller à l'historique"):
        st.switch_page("pages/3_Historique.py")
    st.stop()

record = get_analysis_by_id(analysis_id)

if not record:
    st.error("Cette analyse est introuvable (elle a peut-être été supprimée).")
    if st.button("Retour à l'historique"):
        st.switch_page("pages/3_Historique.py")
    st.stop()

render_analysis_result(record)

st.markdown("---")
if st.button("⬅️ Retour à l'historique"):
    st.switch_page("pages/3_Historique.py")
