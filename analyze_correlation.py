import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

print("="*80)
print("ANALYSE DE CORRÉLATION - Dataset d'Irrigation")
print("="*80)

# Charger les données et convertir tous les types en string puis encoder
print("\n📥 Chargement des données...")
df = pd.read_csv('data/processed/irrigation_prediction_clean.csv')

print(f"✅ Dataset chargé: {df.shape[0]} lignes, {df.shape[1]} colonnes\n")

# Encoder avec LabelEncoder pour toutes les colonnes
print("🔄 Encodage des variables...")
df_encoded = df.copy()

for col in df_encoded.columns:
    le = LabelEncoder()
    # Convertir en string, puis encoder
    df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))

print("✅ Encodage terminé\n")

# Calculer la matrice de corrélation (tout est maintenant numérique)
print("📊 Calcul de la matrice de corrélation...")
corr_matrix = df_encoded.corr()
print("✅ Matrice de corrélation calculée\n")

# Afficher les résultats
print("="*80)
print("CORRÉLATIONS AVEC IRRIGATION_NEED (Votre Cible)")
print("="*80)

target_corr = corr_matrix['Irrigation_Need'].drop('Irrigation_Need').sort_values(ascending=False)

print("\nImportance de chaque colonne:\n")
for i, (col, corr_val) in enumerate(target_corr.items(), 1):
    abs_val = abs(corr_val)
    if abs_val < 0.1:
        importance = "🔴 TRÈS FAIBLE (peut supprimer)"
    elif abs_val < 0.2:
        importance = "🟠 FAIBLE (peut supprimer)"
    elif abs_val < 0.4:
        importance = "🟡 MODÉRÉ (à réfléchir)"
    elif abs_val < 0.6:
        importance = "🟢 IMPORTANT"
    else:
        importance = "🟢🟢 TRÈS IMPORTANT"
    
    print(f"{i:2d}. {col:30} : {corr_val:7.3f}  {importance}")

# Corrélations fortes entre colonnes
print("\n" + "="*80)
print("COLONNES REDONDANTES (Corrélations fortes)")
print("="*80)

strong_pairs = []
for i in range(len(corr_matrix.columns)):
    for j in range(i+1, len(corr_matrix.columns)):
        col1 = corr_matrix.columns[i]
        col2 = corr_matrix.columns[j]
        corr_val = corr_matrix.iloc[i, j]
        
        if abs(corr_val) > 0.7:
            strong_pairs.append((col1, col2, corr_val))

if strong_pairs:
    print("\nCorrélations FORTES (|r| > 0.7):\n")
    for col1, col2, corr_val in strong_pairs:
        print(f"   {col1:30} <--> {col2:30} : {corr_val:7.3f}")
else:
    print("\n✅ Aucune corrélation très forte (c'est bon!)")

# Recommandations
print("\n" + "="*80)
print("RECOMMANDATIONS - QUELLES COLONNES SUPPRIMER?")
print("="*80)

print("\n🟢 À SUPPRIMER SANS RISQUE:")
print("   • Water_Source          (corrélation: {:.3f})".format(target_corr.get('Water_Source', 0)))
print("   • Field_Area_hectare    (corrélation: {:.3f})".format(target_corr.get('Field_Area_hectare', 0)))
print("   • Irrigation_Type       (corrélation: {:.3f})".format(target_corr.get('Irrigation_Type', 0)))

print("\n🟡 À TESTER AVANT SUPPRESSION:")
print("   • Region                (corrélation: {:.3f})".format(target_corr.get('Region', 0)))
print("   • Wind_Speed_kmh        (corrélation: {:.3f})".format(target_corr.get('Wind_Speed_kmh', 0)))

print("\n🔵 À RÉFLÉCHIR:")
print("   • Previous_Irrigation_mm (corrélation: {:.3f})".format(target_corr.get('Previous_Irrigation_mm', 0)))

print("\n🟢 À GARDER ABSOLUMENT:")
essentielles = ['Soil_Moisture', 'Crop_Type', 'Crop_Growth_Stage', 'Temperature_C', 
                'Humidity', 'Rainfall_mm', 'Sunlight_Hours', 'Soil_Type']
for col in essentielles:
    if col in target_corr.index:
        print(f"   • {col:30} (corrélation: {target_corr[col]:7.3f})")

print("\n" + "="*80)
print("📝 Résumé:")
print("="*80)
print(f"✅ Total colonnes: {len(df.columns)}")
print(f"✅ Peut supprimer directement: 3 colonnes")
print(f"✅ À tester avant: 2 colonnes")
print(f"✅ À garder: ~{len(essentielles)} colonnes essentielles")
print("\n" + "="*80)
