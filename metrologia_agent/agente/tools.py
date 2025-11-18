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
    Verifica si la consulta del usuario está relacionada con metrología y mediciones.
    
    El agente puede responder sobre:
    - Conceptos fundamentales de metrología (error, exactitud, precisión, resolución, etc.)
    - Instrumentos de medición (uso, tipos, especificaciones, mantenimiento)
    - Normas técnicas (ISO, NTC, GUM, VIM, ISO 17025, etc.)
    - Procedimientos de calibración y medición
    - Análisis de datos metrológicos (incertidumbre, estadística, validación)
    - Trazabilidad y patrones de medida
    - Sistema Internacional de Unidades (SI)
    - Servicios y procedimientos del laboratorio
    - Seguridad y buenas prácticas
    
    Args:
        query: La pregunta o consulta del usuario
        
    Returns:
        Indicación de si la consulta está relacionada con metrología
    """
    try:
        logger.info(f"[TOOL] Verificando alcance de: '{query}'")
        
        # Palabras clave ampliadas para incluir conceptos metrológicos generales
        keywords_metrologia = [
            # Conceptos fundamentales
            'calibracion', 'calibración', 'metrologia', 'metrología',
            'medicion', 'medición', 'medir', 'medida', 'medidas',
            'error', 'exactitud', 'precision', 'precisión', 'resolucion', 'resolución',
            'incertidumbre', 'trazabilidad', 'repetibilidad', 'reproducibilidad',
            'sensibilidad', 'deriva', 'estabilidad', 'linealidad',
            
            # Errores y análisis
            'paralaje', 'sistematico', 'sistemático', 'aleatorio', 'desviacion', 'desviación',
            'varianza', 'media', 'promedio', 'estadistica', 'estadística',
            
            # Instrumentos generales
            'instrumento', 'equipo', 'aparato', 'dispositivo',
            'calibrador', 'vernier', 'pie de rey', 'micrometro', 'micrómetro',
            'comparador', 'balanza', 'termometro', 'termómetro', 'multimetro', 'multímetro',
            'rugosimetro', 'rugosímetro', 'nivel', 'goniometro', 'goniómetro',
            'bloque patron', 'bloque patrón', 'galga', 'patrón',
            
            # Magnitudes
            'temperatura', 'presion', 'presión', 'masa', 'peso', 'volumen',
            'longitud', 'distancia', 'altura', 'diametro', 'diámetro',
            'velocidad', 'fuerza', 'corriente', 'voltaje', 'resistencia',
            'humedad', 'flujo', 'caudal', 'angular', 'angulo', 'ángulo',
            
            # Normas y documentos
            'norma', 'iso', 'ntc', 'vim', 'gum', '17025', 'certificado',
            'datasheet', 'especificacion', 'especificación',
            
            # Sistema Internacional
            'si', 'kilogramo', 'metro', 'segundo', 'kelvin', 'ampere', 'mol', 'candela',
            'unidad', 'unidades',
            
            # Procedimientos
            'procedimiento', 'protocolo', 'metodo', 'método',
            'ensayo', 'prueba', 'verificacion', 'verificación', 'validacion', 'validación',
            
            # Laboratorio
            'laboratorio', 'servicio', 'prestamo', 'préstamo',
            'horario', 'costo', 'precio', 'requisito',
            'seguridad', 'limpieza', 'almacenamiento', 'bata', 'guantes',
            
            # Análisis de incertidumbre
            'tipo a', 'tipo b', 'combinada', 'expandida', 'presupuesto',
            
            # Condiciones ambientales
            'ambiental', 'condiciones', 'humedad relativa',
            
            # Conceptos de calidad
            'conformidad', 'no conforme', 'auditoria', 'auditoría',
            
            # Informe y documentación
            'informe', 'practica', 'práctica', 'datos', 'registro', 'reporte'
        ]
        
        query_lower = query.lower()
        matches = sum(1 for keyword in keywords_metrologia if keyword in query_lower)
        
        # Verificar también si contiene palabras que indiquen que NO es de metrología
        non_metrologia_keywords = [
            'receta', 'cocina', 'politica', 'política', 'futbol', 'fútbol',
            'musica', 'música', 'pelicula', 'película', 'juego', 'videojuego',
            'moda', 'ropa', 'chiste', 'adivinanza'
        ]
        
        non_matches = sum(1 for keyword in non_metrologia_keywords if keyword in query_lower)
        
        if non_matches > 0:
            logger.info("[TOOL] Consulta claramente fuera del alcance")
            return "FUERA_DEL_ALCANCE"
        elif matches > 0:
            logger.info(f"[TOOL] Consulta relacionada con metrología ({matches} coincidencias)")
            return "DENTRO_DEL_ALCANCE"
        else:
            # Si no hay coincidencias claras pero tampoco es obviamente ajeno,
            # dejamos que el agente lo maneje (puede ser una pregunta genérica sobre medición)
            logger.info("[TOOL] Consulta sin palabras clave claras - permitiendo al agente evaluar")
            return "DENTRO_DEL_ALCANCE"
            
    except Exception as e:
        logger.error(f"[TOOL] Error verificando alcance: {e}")
        return "ERROR_VERIFICACION"

tools_metrologia = [buscar_conocimiento_metrologia, verificar_alcance_consulta]
