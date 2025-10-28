import os
from qdrant_client import QdrantClient

def get_qdrant_client() -> QdrantClient:
    """
    Crea y retorna un cliente de Qdrant Cloud.
    
    Returns:
        Cliente de Qdrant configurado
    """
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url or not qdrant_api_key:
        raise ValueError("QDRANT_URL y QDRANT_API_KEY deben estar configurados")
    
    print(f"[QDRANT] Conectando a Qdrant Cloud: {qdrant_url}")
    
    client = QdrantClient(
        url=qdrant_url,
        api_key=qdrant_api_key,
        timeout=60
    )
    
    print("[QDRANT] Conexión exitosa a Qdrant Cloud")
    return client

def get_collection_name() -> str:
    """
    Obtiene el nombre de la colección desde variables de entorno.
    
    Returns:
        Nombre de la colección
    """
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "metrologia_docs")
    print(f"[QDRANT] Colección: {collection_name}")
    return collection_name
