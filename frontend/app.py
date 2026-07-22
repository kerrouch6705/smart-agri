"""
frontend/app.py

Point d'entree de l'application Streamlit Smart-Agri.
Cette page gere la connexion (authentification de DEMONSTRATION, voir
utils/auth.py). Une fois connecte, l'utilisateur est redirige vers le
tableau de bord. La navigation entre les autres pages se trouve ensuite
automatiquement dans la barre laterale (dossier pages/).
"""

import streamlit as st

from components.styles import apply_custom_css, header_banner
from utils.auth import try_login, is_logged_in

st.set_page_config(
    page_title="Smart-Agri — Connexion",
    page_icon="🌱",
    layout="centered",
)

apply_custom_css()

# Si deja connecte, on va directement au tableau de bord.
if is_logged_in():
    st.switch_page("pages/1_Dashboard.py")

header_banner("Connexion à votre espace Smart-Agri")

st.markdown(
    """
    Bienvenue sur **Smart-Agri**, votre assistant intelligent pour
    décider quand et comment irriguer vos parcelles, en combinant
    Machine Learning, données météo en temps réel et intelligence
    artificielle agentique.
    """
)

st.info(
    "🔐 **Authentification de démonstration** — il ne s'agit pas d'une "
    "connexion sécurisée réelle (le backend ne contient pas encore de "
    "système d'utilisateurs). Utilisez les identifiants ci-dessous pour "
    "tester l'application.\n\n"
    "**E-mail :** demo@smartagri.ma  \n"
    "**Mot de passe :** smartagri2026"
)

with st.form("login_form"):
    email = st.text_input("Adresse e-mail", placeholder="demo@smartagri.ma")
    password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
    remember_me = st.checkbox("Se souvenir de moi")
    submitted = st.form_submit_button("Se connecter", use_container_width=True)

if submitted:
    if try_login(email, password):
        if remember_me:
            # NB : "Se souvenir de moi" est simulé ici — st.session_state
            # ne persiste que pendant la session du navigateur en cours.
            # Une vraie implémentation nécessiterait un cookie ou un token
            # côté backend.
            st.session_state["remember_me"] = True
        st.success("Connexion réussie. Redirection en cours...")
        st.switch_page("pages/1_Dashboard.py")
    else:
        st.error("E-mail ou mot de passe incorrect. Réessayez avec les identifiants de démonstration ci-dessus.")
