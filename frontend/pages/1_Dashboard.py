"""
frontend/pages/1_Dashboard.py

Tableau de bord : vue d'ensemble de toutes les analyses enregistrées
localement (fichier frontend/data/history.json).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from components.styles import apply_custom_css, header_banner
from components.sidebar import render_sidebar
from utils.auth import require_login
from utils.storage import load_history

st.set_page_config(page_title="Smart-Agri — Tableau de bord", page_icon="🌱", layout="wide")
apply_custom_css()
require_login()
render_sidebar()

header_banner("Tableau de bord")

history = load_history()

if not history:
    st.info("Aucune analyse enregistrée pour le moment.")
    if st.button("➕ Créer ma première analyse", use_container_width=False):
        st.switch_page("pages/2_Nouvelle_Analyse.py")
    st.stop()

df = pd.DataFrame(history)

# --- Indicateurs generaux ------------------------------------------------
last = history[0]  # load_history() trie deja du plus recent au plus ancien
total_analyses = len(history)
high_risk_count = int((df["risk_level"] == "Élevé").sum()) if "risk_level" in df else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Analyses totales", total_analyses)
col2.metric("Dernière humidité prévue", f"{last.get('soil_moisture_prediction', '—')} %")
col3.metric("Dernier indice de stress", f"{last.get('stress_index', '—')} / 100")
col4.metric("Dernier niveau de risque", last.get("risk_level", "—"))
col5.metric("Analyses à risque élevé", high_risk_count)

st.markdown(f"**Dernière décision enregistrée :** {last.get('decision', '—')} ({last.get('Nom_Parcelle', 'parcelle inconnue')})")

st.markdown("---")

if st.button("➕ Nouvelle analyse", type="primary"):
    st.switch_page("pages/2_Nouvelle_Analyse.py")

st.markdown("### 📋 Dernières analyses")
display_columns = [
    "created_at", "Nom_Parcelle", "Region", "Crop_Type",
    "soil_moisture_prediction", "stress_index", "risk_level", "decision",
]
available_columns = [c for c in display_columns if c in df.columns]
st.dataframe(
    df[available_columns].head(10).rename(columns={
        "created_at": "Date",
        "Nom_Parcelle": "Parcelle",
        "Region": "Région",
        "Crop_Type": "Culture",
        "soil_moisture_prediction": "Humidité prévue (%)",
        "stress_index": "Stress",
        "risk_level": "Risque",
        "decision": "Décision",
    }),
    use_container_width=True,
    hide_index=True,
)

st.markdown("### 📈 Évolution de l'humidité prévue")
chart_df = df.sort_values("created_at")
if "soil_moisture_prediction" in chart_df.columns:
    fig_line = px.line(
        chart_df,
        x="created_at",
        y="soil_moisture_prediction",
        markers=True,
        labels={"created_at": "Date", "soil_moisture_prediction": "Humidité prévue (%)"},
        color_discrete_sequence=["#2D6A4F"],
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.markdown("### 🥧 Répartition des niveaux de risque")
if "risk_level" in df.columns:
    risk_counts = df["risk_level"].value_counts().reset_index()
    risk_counts.columns = ["Niveau de risque", "Nombre"]
    color_map = {"Faible": "#2D6A4F", "Moyen": "#E8871E", "Élevé": "#D64545", "Inconnu": "#9AA5A0"}
    fig_pie = px.pie(
        risk_counts,
        names="Niveau de risque",
        values="Nombre",
        color="Niveau de risque",
        color_discrete_map=color_map,
    )
    st.plotly_chart(fig_pie, use_container_width=True)
