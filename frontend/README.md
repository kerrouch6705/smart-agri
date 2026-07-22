# 🌱 Smart-Agri — Frontend Streamlit

Interface web du projet Smart-Agri, développée en **Python + Streamlit**
(aucun React, Vite, JavaScript ou Node.js).

## 🗂️ Structure

```
frontend/
├── app.py                     # Page de connexion (point d'entrée)
├── pages/
│   ├── 1_Dashboard.py         # Tableau de bord
│   ├── 2_Nouvelle_Analyse.py  # Formulaire + lancement de l'analyse
│   ├── 3_Historique.py        # Historique, recherche, filtres, suppression
│   ├── 4_Detail_Analyse.py    # Détail d'une analyse
│   └── 5_Parametres.py        # Paramètres (profil, backend, historique, déconnexion)
├── components/
│   ├── sidebar.py              # Barre latérale commune (identité + déconnexion)
│   ├── cards.py                 # Affichage réutilisable du résultat d'une analyse
│   └── styles.py                 # CSS centralisé (palette Smart-Agri)
├── services/
│   └── api_service.py          # TOUS les appels HTTP vers le backend FastAPI
├── utils/
│   ├── auth.py                  # Authentification de démonstration (session_state)
│   └── storage.py               # Historique local (fichier JSON)
├── data/
│   └── history.json             # Historique local (créé/mis à jour automatiquement)
├── assets/
└── requirements.txt
```

## ⚙️ Installation

Depuis la racine du projet `smart_agri_claude/` :

```bash
# 1. Créer un environnement virtuel (une seule fois)
python -m venv .venv

# 2. Activer l'environnement virtuel
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate

# 3. Installer les dépendances du backend
pip install -r backend/requirements.txt

# 4. Installer les dépendances du frontend
pip install -r frontend/requirements.txt
```

## 🔑 Configuration

1. Copier `.env.example` en `.env` à la racine du projet.
2. Remplacer `votre_cle_groq_ici` par votre vraie clé Groq (https://console.groq.com).
3. Ne jamais commiter ce fichier `.env` (il est déjà ignoré par `.gitignore`).
4. Remettre le fichier du modèle à l'emplacement exact : `models/rf_pipeline.pkl`.

## ▶️ Lancer l'application

Il faut **deux terminaux** (le backend doit tourner avant le frontend).

**Terminal 1 — Backend FastAPI** (depuis le dossier `backend/`) :

```bash
cd backend
uvicorn main:app --reload
```

L'API est disponible sur http://127.0.0.1:8000 — vérifiez avec http://127.0.0.1:8000/health

**Terminal 2 — Frontend Streamlit** (depuis le dossier `frontend/`) :

```bash
cd frontend
streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur (par défaut http://localhost:8501).

## 🔐 Connexion (démonstration)

- **E-mail :** `demo@smartagri.ma`
- **Mot de passe :** `smartagri2026`

Cette authentification est **simulée** avec `st.session_state` : elle
protège l'accès aux pages pendant la démonstration, mais ce n'est pas
une vraie sécurité (pas de base d'utilisateurs, pas de hachage de mot
de passe, pas de token). Voir la section "Ce qui est réel / simulé"
ci-dessous.

## 🧪 Tests à effectuer

1. **Backend seul** :
   - `GET http://127.0.0.1:8000/health` → doit renvoyer `status: API is running`.
   - `POST http://127.0.0.1:8000/predict-with-weather` avec un corps JSON respectant `IrrigationWithWeatherInput` → doit renvoyer une prédiction.
   - `POST http://127.0.0.1:8000/analyze` avec le même corps → doit renvoyer le résultat complet du workflow LangGraph (peut prendre quelques secondes à cause de l'appel à Groq).
2. **Agent seul** (sans FastAPI) : `python agent/langgraph_agent.py` depuis la racine — doit afficher une recommandation dans le terminal.
3. **Frontend** :
   - Se connecter avec les identifiants de démonstration.
   - Aller sur "Nouvelle analyse", remplir le formulaire, cliquer sur "Lancer l'analyse intelligente".
   - Vérifier que le résultat s'affiche (prédiction, stress, météo, décision, recommandation Groq).
   - Aller sur "Tableau de bord" : vérifier que les métriques et graphiques se mettent à jour.
   - Aller sur "Historique" : rechercher, filtrer, consulter le détail, supprimer une analyse.
   - Aller sur "Paramètres" : tester la disponibilité du backend, vider l'historique.
   - Couper le backend (Ctrl+C dans le terminal 1) et relancer une analyse : un message d'erreur clair doit s'afficher (pas de plantage de l'application).

## 🔗 Connexion Streamlit ↔ FastAPI (explication simple)

Le frontend Streamlit n'appelle **jamais** directement le modèle
Machine Learning, Open-Meteo, LangGraph ou Groq. Il appelle uniquement
le backend FastAPI, via un seul point d'entrée centralisé :
`frontend/services/api_service.py`, à l'adresse définie par
`API_BASE_URL` (par défaut `http://127.0.0.1:8000`).

Quand vous cliquez sur "Lancer l'analyse intelligente" :

```
Streamlit (formulaire)
   │  POST /analyze  (requests, via api_service.py)
   ▼
FastAPI (backend/main.py)
   │  appelle directement (import Python, pas de HTTP)
   ▼
LangGraph (agent/langgraph_agent.py -> run_smart_agri_analysis)
   │  appelle directement (import Python, pas de HTTP)
   ▼
core/prediction_service.py (Open-Meteo + stress + modèle ML)
```

Le résultat structuré (dictionnaire Python / JSON) remonte ensuite
jusqu'à Streamlit, qui l'enregistre dans `data/history.json` et
l'affiche.

## ✅ Ce qui est réel / ❌ ce qui est simulé

| Élément | Statut |
|---|---|
| Prédiction Machine Learning (RandomForest) | ✅ Réel |
| Récupération météo (Open-Meteo) | ✅ Réel, en temps réel |
| Calcul de l'indice de stress hydrique | ✅ Réel (règles métier) |
| Décision d'irrigation (règles) | ✅ Réel (règles métier) |
| Recommandation en langage naturel | ✅ Réel (appel à Groq / Llama 3.3) |
| Historique des analyses | ⚠️ Réel mais stocké dans un simple fichier JSON local, pas dans une base de données |
| Authentification | ❌ Simulée (`st.session_state`, un seul compte de démonstration codé en dur) |
| "Se souvenir de moi" | ❌ Simulé (aucune persistance réelle au-delà de la session du navigateur) |
| Mode sombre | ⚠️ Partiel — dépend du thème natif de Streamlit |

## 🚀 Améliorations futures possibles

- Remplacer le fichier JSON par une vraie base de données (SQLite + SQLAlchemy), avec des endpoints FastAPI dédiés à l'historique (`GET/POST/DELETE /history`).
- Ajouter une vraie authentification (table d'utilisateurs, mots de passe hachés, JWT).
- Ajouter d'autres régions dans `REGION_COORDINATES` (actuellement limité à 5 régions marocaines).
- Ajouter des tests automatisés (pytest) sur `core/prediction_service.py` et sur `agent/langgraph_agent.py`.
- Déployer le backend et le frontend séparément (ex. backend sur un serveur, frontend sur Streamlit Community Cloud) en configurant `API_BASE_URL`.
