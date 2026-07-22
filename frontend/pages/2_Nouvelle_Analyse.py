"""
frontend/pages/2_Nouvelle_Analyse.py

Formulaire de saisie d'une nouvelle analyse.
Aucun champ latitude/longitude : la région suffit, le backend récupère
automatiquement la météo via Open-Meteo.
"""

import streamlit as st

from components.styles import apply_custom_css, header_banner
from components.sidebar import render_sidebar
from components.cards import render_analysis_result
from utils.auth import require_login
from utils.storage import add_analysis
from services.api_service import analyze_field

st.set_page_config(page_title="Smart-Agri — Nouvelle analyse", page_icon="🌱", layout="wide")
apply_custom_css()
require_login()
render_sidebar()

header_banner("Nouvelle analyse")

# Ces listes correspondent aux catégories explicitement reconnues dans la
# logique métier du backend (core/prediction_service.py). Elles ne doivent
# pas être modifiées sans vérifier qu'elles correspondent bien aux
# catégories utilisées pour entraîner models/rf_pipeline.pkl.
REGIONS = ["Souss-Massa", "Agadir", "Taroudant", "Marrakech", "Casablanca"]
SOIL_TYPES = ["Sandy", "Loamy", "Silt", "Clay"]
CROP_TYPES = ["Rice", "Sugarcane", "Cotton", "Maize", "Wheat", "Soybean"]
GROWTH_STAGES = ["Sowing", "Vegetative", "Flowering", "Harvest"]
SEASONS = ["Summer", "Winter", "Spring", "Autumn"]
MULCHING_OPTIONS = ["Yes", "No"]

with st.form("nouvelle_analyse_form", clear_on_submit=False):

    st.markdown("#### 1️⃣ Identification de la parcelle")
    col1, col2 = st.columns(2)
    with col1:
        nom_parcelle = st.text_input("Nom / identifiant de la parcelle", placeholder="Ex : Parcelle Nord")
    with col2:
        region = st.selectbox("Région", REGIONS)

    st.caption("La météo (température, humidité, pluie, vent, ensoleillement) est récupérée automatiquement pour cette région — aucune coordonnée GPS n'est nécessaire.")

    st.markdown("#### 2️⃣ Informations du sol")
    col3, col4, col5 = st.columns(3)
    with col3:
        soil_type = st.selectbox("Type de sol", SOIL_TYPES)
        soil_moisture = st.number_input("Humidité actuelle du sol (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.1)
    with col4:
        soil_ph = st.number_input("pH du sol", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
        organic_carbon = st.number_input("Carbone organique (%)", min_value=0.0, max_value=10.0, value=1.2, step=0.1)
    with col5:
        electrical_conductivity = st.number_input("Conductivité électrique (dS/m)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)

    st.markdown("#### 3️⃣ Informations de la culture")
    col6, col7, col8 = st.columns(3)
    with col6:
        crop_type = st.selectbox("Type de culture", CROP_TYPES)
        season = st.selectbox("Saison", SEASONS)
    with col7:
        crop_growth_stage = st.selectbox("Stade de croissance", GROWTH_STAGES)
        mulching_used = st.selectbox("Paillage utilisé", MULCHING_OPTIONS)
    with col8:
        previous_irrigation_mm = st.number_input("Irrigation précédente (mm)", min_value=0.0, value=5.0, step=0.5)

    submitted = st.form_submit_button("🌾 Lancer l'analyse intelligente", type="primary", use_container_width=True)

if submitted:
    if not nom_parcelle.strip():
        st.error("Merci de donner un nom à la parcelle avant de lancer l'analyse.")
        st.stop()

    payload = {
        "Soil_Type": soil_type,
        "Soil_pH": soil_ph,
        "Soil_Moisture": soil_moisture,
        "Organic_Carbon": organic_carbon,
        "Electrical_Conductivity": electrical_conductivity,
        "Crop_Type": crop_type,
        "Crop_Growth_Stage": crop_growth_stage,
        "Season": season,
        "Mulching_Used": mulching_used,
        "Previous_Irrigation_mm": previous_irrigation_mm,
        "Region": region,
    }

    with st.spinner("Analyse en cours : récupération météo, prédiction ML et génération de la recommandation..."):
        success, result = analyze_field(payload)

    if not success:
        st.error(f"❌ L'analyse a échoué : {result}")
    else:
        record = {**payload, "Nom_Parcelle": nom_parcelle.strip(), **result}
        saved_record = add_analysis(record)
        st.session_state["last_result_id"] = saved_record["id"]
        st.success("✅ Analyse terminée avec succès.")
        st.markdown("---")
        render_analysis_result(saved_record)
