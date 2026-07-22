"""
frontend/pages/3_Historique.py

Historique des analyses, avec recherche, filtres, tri et suppression.
Les données proviennent du fichier local frontend/data/history.json
(voir utils/storage.py).
"""

import streamlit as st
import pandas as pd

from components.styles import apply_custom_css, header_banner
from components.sidebar import render_sidebar
from utils.auth import require_login
from utils.storage import load_history, delete_analysis

st.set_page_config(page_title="Smart-Agri — Historique", page_icon="🌱", layout="wide")
apply_custom_css()
require_login()
render_sidebar()

header_banner("Historique des analyses")

history = load_history()

if not history:
    st.info("Aucune analyse enregistrée pour le moment.")
    if st.button("➕ Créer ma première analyse"):
        st.switch_page("pages/2_Nouvelle_Analyse.py")
    st.stop()

df = pd.DataFrame(history)

# --- Filtres --------------------------------------------------------------
st.markdown("#### 🔍 Recherche et filtres")
f1, f2, f3, f4 = st.columns(4)

with f1:
    search_term = st.text_input("Nom de la parcelle contient…", "")
with f2:
    crop_options = ["Toutes"] + sorted(df["Crop_Type"].dropna().unique().tolist()) if "Crop_Type" in df else ["Toutes"]
    crop_filter = st.selectbox("Culture", crop_options)
with f3:
    risk_options = ["Tous"] + sorted(df["risk_level"].dropna().unique().tolist()) if "risk_level" in df else ["Tous"]
    risk_filter = st.selectbox("Niveau de risque", risk_options)
with f4:
    sort_option = st.selectbox("Trier par", ["Plus récent d'abord", "Plus ancien d'abord"])

date_range = st.date_input("Filtrer par date (période)", value=())

filtered = df.copy()

if search_term:
    filtered = filtered[filtered["Nom_Parcelle"].str.contains(search_term, case=False, na=False)]

if crop_filter != "Toutes" and "Crop_Type" in filtered:
    filtered = filtered[filtered["Crop_Type"] == crop_filter]

if risk_filter != "Tous" and "risk_level" in filtered:
    filtered = filtered[filtered["risk_level"] == risk_filter]

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered["_date_only"] = pd.to_datetime(filtered["created_at"]).dt.date
    filtered = filtered[(filtered["_date_only"] >= start_date) & (filtered["_date_only"] <= end_date)]
    filtered = filtered.drop(columns=["_date_only"])

filtered = filtered.sort_values("created_at", ascending=(sort_option == "Plus ancien d'abord"))

st.markdown(f"#### 📋 Résultats ({len(filtered)} analyse(s))")

if filtered.empty:
    st.warning("Aucune analyse ne correspond à ces filtres.")
else:
    display_columns = [
        "created_at", "Nom_Parcelle", "Region", "Crop_Type",
        "Soil_Moisture", "soil_moisture_prediction", "stress_index",
        "risk_level", "decision",
    ]
    available_columns = [c for c in display_columns if c in filtered.columns]
    st.dataframe(
        filtered[available_columns].rename(columns={
            "created_at": "Date",
            "Nom_Parcelle": "Parcelle",
            "Region": "Région",
            "Crop_Type": "Culture",
            "Soil_Moisture": "Humidité actuelle (%)",
            "soil_moisture_prediction": "Humidité prévue (%)",
            "stress_index": "Stress",
            "risk_level": "Risque",
            "decision": "Décision",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# --- Voir le détail d'une analyse ------------------------------------------
st.markdown("#### 🔎 Voir le détail d'une analyse")
options = {
    f"{row['Nom_Parcelle']} — {row['created_at']}": row["id"]
    for _, row in filtered.iterrows()
} if not filtered.empty else {}

if options:
    selected_label = st.selectbox("Choisir une analyse", list(options.keys()))
    if st.button("Voir les détails"):
        st.session_state["selected_analysis_id"] = options[selected_label]
        st.switch_page("pages/4_Detail_Analyse.py")

st.markdown("---")

# --- Supprimer une analyse --------------------------------------------------
st.markdown("#### 🗑️ Supprimer une analyse")
if options:
    delete_label = st.selectbox("Choisir l'analyse à supprimer", list(options.keys()), key="delete_select")
    confirm_delete = st.checkbox("Je confirme vouloir supprimer définitivement cette analyse.")
    if st.button("Supprimer", disabled=not confirm_delete):
        deleted = delete_analysis(options[delete_label])
        if deleted:
            st.success("Analyse supprimée.")
            st.rerun()
        else:
            st.error("Impossible de supprimer cette analyse (introuvable).")
