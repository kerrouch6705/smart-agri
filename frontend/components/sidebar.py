"""
frontend/components/sidebar.py

Barre laterale commune a toutes les pages protegees.
La navigation entre pages (Tableau de bord, Nouvelle analyse, Historique,
Parametres) est generee automatiquement par Streamlit a partir du dossier
`pages/`. Ce composant ajoute simplement l'identite Smart-Agri et le
bouton de deconnexion.
"""

import streamlit as st
from utils.auth import logout


def render_sidebar():
    with st.sidebar:
        st.markdown("## 🌱 Smart-Agri")
        st.caption("Aide à la décision pour l'irrigation")

        display_name = st.session_state.get("display_name", "Utilisateur Smart-Agri")
        user_email = st.session_state.get("user_email", "")
        st.markdown(f"**Connecté(e) :** {display_name}")
        if user_email:
            st.caption(user_email)

        st.markdown("---")

        if st.button("🚪 Se déconnecter", use_container_width=True):
            logout()
            st.switch_page("app.py")
