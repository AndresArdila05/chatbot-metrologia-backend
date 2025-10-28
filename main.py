import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import pytz
import uvicorn
from google.cloud import firestore

# Cargar variables de entorno desde .env
load_dotenv()

from metrologia_agent.agente.agente import agente_metrologia
from utils.fs_logs import fs_log

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Chatbot Metrología",
    description="Sistema de chatbot inteligente para consultas sobre metrología utilizando RAG y LangGraph",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    """Modelo de entrada para el endpoint de chat."""
    mensaje: str = Field(..., description="Mensaje del usuario", example="¿Qué es la calibración de instrumentos?")
    conversation_id: str = Field(..., description="ID único de la conversación", example="conv-123-456")

class ChatResponse(BaseModel):
    """Modelo de respuesta para el endpoint de chat."""
    respuesta: str = Field(..., description="Respuesta del agente")
    conversation_id: str = Field(..., description="ID de la conversación")
    timestamp: str = Field(..., description="Marca de tiempo de la respuesta")

class MessageHistory(BaseModel):
    """Modelo para un mensaje en el historial."""
    role: str = Field(..., description="Rol del mensaje: user o assistant")
    content: str = Field(..., description="Contenido del mensaje")
    timestamp: str = Field(..., description="Marca de tiempo del mensaje")

class HistorialResponse(BaseModel):
    """Modelo de respuesta para el endpoint de historial."""
    conversation_id: str = Field(..., description="ID de la conversación")
    messages: List[MessageHistory] = Field(..., description="Lista de mensajes de la conversación")

class HealthResponse(BaseModel):
    """Modelo de respuesta para el endpoint de health."""
    status: str = Field(..., description="Estado del servicio")
    timestamp: str = Field(..., description="Marca de tiempo de la verificación")
    version: str = Field(..., description="Versión de la API")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint principal para interactuar con el chatbot de metrología.
    
    El agente utiliza RAG para buscar información en la base de conocimiento
    y responde únicamente preguntas relacionadas con metrología.
    """
    try:
        logger.info(f"[CHAT] Nueva consulta - Conversation ID: {request.conversation_id}")
        logger.info(f"[CHAT] Mensaje: {request.mensaje}")
        
        config = {
            "configurable": {
                "thread_id": request.conversation_id
            }
        }
        
        result = agente_metrologia.invoke(
            {"messages": [("user", request.mensaje)]},
            config=config
        )
        
        if not result or "messages" not in result:
            raise HTTPException(status_code=500, detail="Error procesando la respuesta del agente")
        
        respuesta_texto = result["messages"][-1].content
        
        timestamp = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')
        
        log_dict = {
            "conversation_id": request.conversation_id,
            "timestamp": timestamp,
            "user_message": request.mensaje,
            "agent_response": respuesta_texto,
            "version": "1.0.0"
        }
        fs_log(
            database=os.getenv("FIRESTORE_DATABASE", "pln-proyecto"),
            collection_name=os.getenv("FIRESTORE_COLLECTION", "logs-agente"),
            values_dict=log_dict
        )
        
        logger.info(f"[CHAT] Respuesta generada exitosamente")
        
        return ChatResponse(
            respuesta=respuesta_texto,
            conversation_id=request.conversation_id,
            timestamp=timestamp
        )
        
    except Exception as e:
        logger.error(f"[CHAT] Error procesando solicitud: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/historial/{conversation_id}", response_model=HistorialResponse)
async def obtener_historial(conversation_id: str):
    """
    Obtiene el historial de una conversación específica.
    
    Recupera todos los mensajes de una conversación desde Firestore
    para que el frontend pueda mostrar el historial completo.
    """
    try:
        logger.info(f"[HISTORIAL] Consultando conversación: {conversation_id}")
        
        db = firestore.Client(database=os.getenv("FIRESTORE_DATABASE", "pln-proyecto"))
        
        docs = db.collection(os.getenv("FIRESTORE_COLLECTION", "logs-agente")).where(
            "conversation_id", "==", conversation_id
        ).order_by("timestamp").stream()
        
        messages = []
        for doc in docs:
            data = doc.to_dict()
            
            messages.append(MessageHistory(
                role="user",
                content=data.get("user_message", ""),
                timestamp=data.get("timestamp", "")
            ))
            
            messages.append(MessageHistory(
                role="assistant",
                content=data.get("agent_response", ""),
                timestamp=data.get("timestamp", "")
            ))
        
        logger.info(f"[HISTORIAL] Se encontraron {len(messages)} mensajes")
        
        return HistorialResponse(
            conversation_id=conversation_id,
            messages=messages
        )
        
    except Exception as e:
        logger.error(f"[HISTORIAL] Error consultando historial: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando historial: {str(e)}")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Endpoint de verificación de estado del servicio.
    
    Utilizado para monitoreo y verificación de disponibilidad.
    """
    timestamp = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')
    
    return HealthResponse(
        status="healthy",
        timestamp=timestamp,
        version="1.0.0"
    )

@app.get("/", response_class=RedirectResponse, include_in_schema=False)
async def redirect_to_docs():
    """Redirige al root a la documentación interactiva."""
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"[MAIN] Iniciando API en puerto {port}")
    logger.info("[MAIN] Endpoints disponibles:")
    logger.info("  - POST /chat")
    logger.info("  - GET /historial/{conversation_id}")
    logger.info("  - GET /health")
    logger.info("  - GET /docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
