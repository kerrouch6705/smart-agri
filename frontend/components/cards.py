"""
frontend/components/cards.py

Composants d'affichage reutilises par :
- pages/2_Nouvelle_Analyse.py (juste apres une analyse)
- pages/4_Detail_Analyse.py (consultation depuis l'historique)

Cela evite de dupliquer le code d'affichage du resultat a deux endroits.
"""

import streamlit as st
from components.styles import risk_color


def render_risk_badge(risk_level: str):
    color = risk_color(risk_level)
    st.markdown(
        f'<span class="sa-badge" style="background-color:{color};">Risque : {risk_level}</span>',
        unsafe_allow_html=True,
    )


def render_analysis_result(record: dict):
    """
    Affiche un resultat d'analyse complet (identique pour la page de
    resultat juste apres l'analyse et pour la page de detail depuis
    l'historique).

    `record` est un dictionnaire qui contient a la fois :
    - les donnees saisies dans le formulaire (Nom_Parcelle, Region, sol, culture...)
    - le resultat renvoye par l'API /analyze (prediction, stress, decision...)
    """

    nom_parcelle = record.get("Nom_Parcelle", "Parcelle sans nom")
    created_at = record.get("created_at", "")

    st.subheader(f"📍 {nom_parcelle}")
    if created_at:
        st.caption(f"Analyse réalisée le {created_at.replace('T', ' à ')}")

    # --- Indicateurs cles ---------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Humidité actuelle du sol", f"{record.get('Soil_Moisture', '—')} %")
    with col2:
        prediction = record.get("soil_moisture_prediction")
        st.metric("Humidité prévue (J+1)", f"{prediction} %" if prediction is not None else "—")
    with col3:
        stress = record.get("stress_index")
        st.metric("Indice de stress hydrique", f"{stress} / 100" if stress is not None else "—")
    with col4:
        st.metric("Niveau d'irrigation conseillé", record.get("irrigation_level", "—"))

    render_risk_badge(record.get("risk_level", "Inconnu"))
    st.write("")

    decision = record.get("decision", "—")
    risk_level = record.get("risk_level", "Inconnu")

    if risk_level == "Faible":
        st.success(f"**Décision :** {decision}")
    elif risk_level == "Moyen":
        st.warning(f"**Décision :** {decision}")
    elif risk_level in ("Élevé", "Eleve"):
        st.error(f"**Décision :** {decision}")
    else:
        st.info(f"**Décision :** {decision}")

    if record.get("reason"):
        st.caption(f"Raison (règle de décision) : {record.get('reason')}")

    # --- Recommandation Groq -------------------------------------------
    st.markdown("#### 🤖 Recommandation générée par l'agent IA (Groq)")
    final_response = record.get("final_response")
    if final_response:
        st.info(final_response)
    else:
        st.caption("Aucune recommandation générée.")

    # --- Details par origine (transparence) -----------------------------
    with st.expander("🔎 Détails et origine de chaque résultat"):
        st.markdown("**Prédiction du modèle Machine Learning (RandomForest)**")
        st.write(f"- Humidité du sol prévue à J+1 : {record.get('soil_moisture_prediction')} %")

        st.markdown("**Indice de stress hydrique (calcul par règles)**")
        st.write(f"- Valeur : {record.get('stress_index')} / 100")

        st.markdown("**Météo utilisée (Open-Meteo, temps réel)**")
        weather = record.get("weather_data_used") or {}
        if weather:
            wcol1, wcol2, wcol3, wcol4, wcol5 = st.columns(5)
            wcol1.metric("Température", f"{weather.get('Temperature_C', '—')} °C")
            wcol2.metric("Humidité air", f"{weather.get('Humidity', '—')} %")
            wcol3.metric("Pluie", f"{weather.get('Rainfall_mm', '—')} mm")
            wcol4.metric("Vent", f"{weather.get('Wind_Speed_kmh', '—')} km/h")
            wcol5.metric("Ensoleillement", f"{weather.get('Sunlight_Hours', '—')} h")
        else:
            st.caption("Donnée météo indisponible.")

        st.markdown("**Analyse de l'agent Météorologue (règles)**")
        st.write(record.get("weather_analysis", "—"))

        st.markdown("**Analyse de l'agent Agronome (règles)**")
        st.write(record.get("agronomic_analysis", "—"))

        st.markdown("**Décision de l'agent Décisionnel (règles)**")
        st.write(
            f"- Décision : {record.get('decision', '—')}\n"
            f"- Niveau de risque : {record.get('risk_level', '—')}\n"
            f"- Niveau d'irrigation : {record.get('irrigation_level', '—')}\n"
            f"- Raison : {record.get('reason', '—')}"
        )

        st.markdown("**Formulation finale (LLM Groq — llama-3.3-70b-versatile)**")
        st.write(final_response or "—")

    # --- Donnees de la parcelle / culture --------------------------------
    with st.expander("🌾 Données du sol et de la culture saisies"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Sol**")
            st.write(f"- Type de sol : {record.get('Soil_Type', '—')}")
            st.write(f"- pH du sol : {record.get('Soil_pH', '—')}")
            st.write(f"- Carbone organique : {record.get('Organic_Carbon', '—')}")
            st.write(f"- Conductivité électrique : {record.get('Electrical_Conductivity', '—')}")
        with col_b:
            st.write("**Culture**")
            st.write(f"- Type de culture : {record.get('Crop_Type', '—')}")
            st.write(f"- Stade de croissance : {record.get('Crop_Growth_Stage', '—')}")
            st.write(f"- Saison : {record.get('Season', '—')}")
            st.write(f"- Paillage utilisé : {record.get('Mulching_Used', '—')}")
            st.write(f"- Irrigation précédente : {record.get('Previous_Irrigation_mm', '—')} mm")
        st.write(f"**Région :** {record.get('Region', '—')}")
