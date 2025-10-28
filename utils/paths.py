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
    model="gemini-2.0-flash-exp",
    google_api_key=gemini_api_key,
    temperature=0.3,
    convert_system_message_to_human=True
)

# Embeddings - Cambio a Vertex AI (cuotas más altas, requiere billing)
embedding_model = VertexAIEmbeddings(
    model_name="text-embedding-004",
    project=os.getenv("GCP_PROJECT", "sodium-pager-473602-n7"),
    location="us-central1"
)

print("[PATHS] LLM: Gemini 2.5 Flash (API Key)")
print("[PATHS] Embeddings: Vertex AI text-embedding-004 (GCP)")
print("[PATHS] Modelos inicializados correctamente")
