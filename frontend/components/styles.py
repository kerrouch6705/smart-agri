"""
frontend/components/styles.py

CSS centralise pour toute l'application Smart-Agri.
Palette de couleurs demandee :
- vert fonce, vert naturel, vert clair, blanc, gris tres clair
- orange pour les avertissements, rouge uniquement pour les risques eleves
"""

import streamlit as st

COLORS = {
    "dark_green": "#1B4332",
    "green": "#2D6A4F",
    "light_green": "#95D5B2",
    "pale_green": "#F1F8F4",
    "white": "#FFFFFF",
    "light_gray": "#F5F6F7",
    "gray_text": "#556B66",
    "orange": "#E8871E",
    "red": "#D64545",
}


def apply_custom_css():
    st.markdown(
        f"""
        <style>
        :root {{
            --sa-dark-green: {COLORS["dark_green"]};
            --sa-green: {COLORS["green"]};
            --sa-light-green: {COLORS["light_green"]};
            --sa-pale-green: {COLORS["pale_green"]};
            --sa-orange: {COLORS["orange"]};
            --sa-red: {COLORS["red"]};
        }}

        /* Fond general */
        .stApp {{
            background-color: {COLORS["light_gray"]};
        }}

        /* Barre laterale */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS["dark_green"]};
        }}
        section[data-testid="stSidebar"] * {{
            color: {COLORS["white"]} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.2);
        }}

        /* Boutons principaux */
        div.stButton > button, div.stFormSubmitButton > button {{
            background-color: {COLORS["green"]};
            color: {COLORS["white"]};
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.2rem;
            font-weight: 600;
        }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background-color: {COLORS["dark_green"]};
            color: {COLORS["white"]};
        }}

        /* Titres */
        h1, h2, h3 {{
            color: {COLORS["dark_green"]};
        }}

        /* Cartes / conteneurs */
        div[data-testid="stMetric"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["light_green"]};
            border-radius: 10px;
            padding: 0.8rem;
        }}

        .sa-header-banner {{
            background: linear-gradient(90deg, {COLORS["dark_green"]}, {COLORS["green"]});
            color: {COLORS["white"]};
            padding: 1.4rem 1.6rem;
            border-radius: 12px;
            margin-bottom: 1.4rem;
        }}
        .sa-header-banner h1 {{
            color: {COLORS["white"]} !important;
            margin: 0;
        }}
        .sa-header-banner p {{
            margin: 0.2rem 0 0 0;
            opacity: 0.9;
        }}

        .sa-badge {{
            display: inline-block;
            padding: 0.25rem 0.8rem;
            border-radius: 20px;
            font-weight: 700;
            color: white;
            font-size: 0.9rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header_banner(subtitle: str = "Système intelligent d'aide à la décision pour l'irrigation"):
    st.markdown(
        f"""
        <div class="sa-header-banner">
            <h1>🌱 Smart-Agri</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_color(risk_level: str) -> str:
    mapping = {
        "Faible": COLORS["green"],
        "Moyen": COLORS["orange"],
        "Élevé": COLORS["red"],
        "Eleve": COLORS["red"],
    }
    return mapping.get(risk_level, COLORS["gray_text"])
