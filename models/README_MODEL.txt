Le modèle final utilisé par le backend est un pipeline Scikit-learn
contenant le preprocessing et un RandomForestRegressor.

Nom du fichier dans le projet original :
models/rf_pipeline.pkl

Cible prédite :
Soil_Moisture_J1

L’endpoint FastAPI charge ce fichier avec joblib.

Le fichier .pkl n’est pas inclus dans ce ZIP uniquement pour réduire
la taille de l’envoi. Il existe bien dans le projet original.

Ne modifie pas son nom ni son chemin dans le code.