from google.cloud import firestore
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fs_log(database: str, collection_name: str, values_dict: dict) -> None:
    """
    Guarda un registro en Firestore.
    
    Args:
        database: Nombre de la base de datos de Firestore
        collection_name: Nombre de la colección
        values_dict: Diccionario con los valores a guardar
    """
    try:
        db = firestore.Client(database=database)
        doc_ref = db.collection(collection_name).document()
        doc_ref.set(values_dict)
        logger.info(f"[FIRESTORE] Log guardado en {database}/{collection_name}")
    except Exception as e:
        logger.error(f"[FIRESTORE] Error guardando log: {e}")
