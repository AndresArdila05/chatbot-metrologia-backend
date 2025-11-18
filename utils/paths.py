import os
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

# Configuración de GCP
PROJECT_ID = os.getenv("GCP_PROJECT", "sodium-pager-473602-n7")
LOCATION = "us-east1"

print(f"[PATHS] GCP Project: {PROJECT_ID}")
print(f"[PATHS] Location: {LOCATION}")

# LLM - Usando Vertex AI (Gemini 2.5 Flash)
llm_model_gemini = ChatVertexAI(
    model_name="gemini-2.5-flash",
    temperature=0.3,
    project=PROJECT_ID,
    location=LOCATION
)

# Embeddings - DEBE SER EL MISMO que en el notebook de ingesta
# ⚠️ IMPORTANTE: Usar gemini-embedding-001 (mismo que ingesta_pdfs_qdrant.ipynb)
embedding_model = VertexAIEmbeddings(
    model_name="gemini-embedding-001",  # ← Mismo modelo que el notebook
    project=PROJECT_ID,
    location=LOCATION  # ← Mismo location que el notebook
)

print("[PATHS] LLM: Vertex AI - Gemini 2.5 Flash")
print("[PATHS] Embeddings: Vertex AI - gemini-embedding-001 (MISMO QUE INGESTA)")
print("[PATHS] Modelos inicializados correctamente")
