import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_vertexai import VertexAIEmbeddings

# Obtener API Key de Gemini desde variable de entorno
gemini_api_key = os.getenv("GEMINI_API_KEY", "")

if not gemini_api_key:
    print("[PATHS] WARNING: GEMINI_API_KEY no está configurada")
else:
    print("[PATHS] API Key de Gemini cargada desde variable de entorno")

# LLM - Sigue usando Google Generative AI (API Key gratuita)
llm_model_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0.3,
    convert_system_message_to_human=True
)

# Embeddings - DEBE SER EL MISMO que en el notebook de ingesta
# ⚠️ IMPORTANTE: Usar gemini-embedding-001 (mismo que ingesta_pdfs_qdrant.ipynb)
embedding_model = VertexAIEmbeddings(
    model_name="gemini-embedding-001",  # ← Mismo modelo que el notebook
    project=os.getenv("GCP_PROJECT", "sodium-pager-473602-n7"),
    location="us-east1"  # ← Mismo location que el notebook
)

print("[PATHS] LLM: Gemini 2.5 Flash (API Key)")
print("[PATHS] Embeddings: Vertex AI gemini-embedding-001 (GCP) - MISMO QUE INGESTA")
print("[PATHS] Modelos inicializados correctamente")
