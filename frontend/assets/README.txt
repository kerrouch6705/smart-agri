Ce dossier est prévu pour accueillir un futur logo Smart-Agri (fichier .png ou .svg).

Pour l'instant, l'application utilise l'emoji 🌱 comme logo (voir
components/styles.py -> header_banner()), pour rester simple et ne
dépendre d'aucun fichier binaire externe.

Si vous ajoutez un vrai logo, par exemple assets/logo.png, vous pouvez
l'afficher avec :

    import streamlit as st
    st.image("assets/logo.png", width=120)
