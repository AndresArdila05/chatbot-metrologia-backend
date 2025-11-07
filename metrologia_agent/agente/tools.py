import logging
from typing import Annotated
from langchain_core.tools import tool
from utils.get_vectorstore import get_qdrant_client, get_collection_name
from utils.paths import embedding_model

logger = logging.getLogger(__name__)

@tool
def buscar_conocimiento_metrologia(query: Annotated[str, "Consulta del usuario sobre metrología"]) -> str:
    """
    Busca información relevante en la base de conocimiento vectorial sobre metrología.
    
    Utiliza embeddings de Gemini y similarity search con Qdrant Cloud para encontrar
    los documentos más relevantes sobre normas, instrumentos, procedimientos y
    aspectos administrativos del laboratorio de metrología.
    
    Args:
        query: La pregunta o consulta del usuario
        
    Returns:
        Información contextual relevante encontrada en la base de conocimiento
    """
    try:
        logger.info(f"[TOOL] Buscando en vectorstore: '{query}'")
        
        client = get_qdrant_client()
        collection_name = get_collection_name()
        
        query_embedding = embedding_model.embed_query(query)
        
        results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=5
        )
        
        if not results:
            logger.warning("[TOOL] No se encontraron documentos relevantes")
            return "No se encontró información relevante en la base de conocimiento."
        
        context_parts = []
        for i, hit in enumerate(results, 1):
            similarity_score = hit.score
            
            if similarity_score < 0.5:
                continue
            
            source = hit.payload.get('source', 'documento desconocido')
            page = hit.payload.get('page', 'N/A')
            text = hit.payload.get('text', '')
            
            # No incluir etiquetas de documento, solo el contenido
            context_parts.append(f"{text}\n")
        
        if not context_parts:
            logger.warning("[TOOL] Todos los documentos tienen baja similitud")
            return "No se encontró información suficientemente relevante."
        
        context = "\n".join(context_parts)
        logger.info(f"[TOOL] Se encontraron {len(context_parts)} documentos relevantes")
        
        return f"Información encontrada en la base de conocimiento:\n\n{context}"
        
    except Exception as e:
        logger.error(f"[TOOL] Error en búsqueda: {e}")
        return f"Error al buscar información: {str(e)}"

@tool
def verificar_alcance_consulta(query: Annotated[str, "Consulta del usuario"]) -> str:
    """
    Verifica si la consulta del usuario está dentro del alcance del laboratorio de metrología.
    
    El agente está limitado a responder sobre:
    - Normas técnicas de metrología (ISO, NTC, etc.)
    - Instrumentos de medición y calibración
    - Procedimientos de calibración y aseguramiento de calidad
    - Información administrativa del laboratorio
    - Servicios de metrología ofrecidos
    
    Args:
        query: La pregunta o consulta del usuario
        
    Returns:
        Indicación de si la consulta está dentro del alcance
    """
    try:
        logger.info(f"[TOOL] Verificando alcance de: '{query}'")
        
        keywords_metrologia = [
            'calibracion', 'calibración', 'metrologia', 'metrología',
            'norma', 'iso', 'ntc', 'instrumento', 'medicion', 'medición',
            'laboratorio', 'equipo', 'certificado', 'incertidumbre',
            'trazabilidad', 'patron', 'patrón', 'balanza', 'termómetro',
            'presión', 'temperatura', 'masa', 'volumen', 'servicio',
            'horario', 'costo', 'precio', 'administrativo'
        ]
        
        query_lower = query.lower()
        matches = sum(1 for keyword in keywords_metrologia if keyword in query_lower)
        
        if matches > 0:
            logger.info(f"[TOOL] Consulta dentro del alcance ({matches} coincidencias)")
            return "DENTRO_DEL_ALCANCE"
        else:
            logger.info("[TOOL] Consulta fuera del alcance")
            return "FUERA_DEL_ALCANCE"
            
    except Exception as e:
        logger.error(f"[TOOL] Error verificando alcance: {e}")
        return "ERROR_VERIFICACION"

tools_metrologia = [buscar_conocimiento_metrologia, verificar_alcance_consulta]
