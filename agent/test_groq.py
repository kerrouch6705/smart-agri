from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Charger les variables du fichier .env
load_dotenv()

# Créer le modèle LLM avec Groq
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Tester si Groq fonctionne
response = llm.invoke("Réponds seulement par : Groq fonctionne.")

print(response.content)