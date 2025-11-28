from typing import Any, AsyncIterator, Dict, Iterator, Optional, Sequence, Tuple
from google.cloud import firestore
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.base import Checkpoint, CheckpointMetadata, CheckpointTuple, ChannelVersions
import pickle
from datetime import datetime
import pytz

class JsonPlusSerializerCompat(JsonPlusSerializer):
    """Clase para serializar-deserializar el checkpointer."""
    
    def loads(self, data: bytes) -> Any:
        if data.startswith(b"\x80") and data.endswith(b"."):
            return pickle.loads(data)
        return super().loads(data)
    
class FirestoreSaver(BaseCheckpointSaver):
    """
    Implementación de memoria de LangGraph en Firestore.
    
    Args:
        database: Nombre de la base de datos de Firestore
        collection_name: Nombre de la colección de checkpoints
        pw_collection_name: Nombre de la colección de escrituras intermedias
    """
    serde = JsonPlusSerializerCompat()

    def __init__(
        self, 
        database: str = "pln-proyecto", 
        collection_name: str = "metrologia_checkpoints", 
        pw_collection_name: str = "metrologia_checkpoint_writes", 
        serde: Optional[Any] = None
    ) -> None:
        super().__init__(serde=serde)
        self.db: firestore.Client = firestore.Client(database=database)
        self.async_db: firestore.AsyncClient = firestore.AsyncClient(database=database)
        self.collection_name: str = collection_name
        self.pw_collection_name: str = pw_collection_name

    def get_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Obtiene el checkpoint asociado a un thread_id."""
        thread_id: str = config["configurable"]["thread_id"]
        
        doc_ref: firestore.DocumentReference = self.db.collection(self.collection_name).document(thread_id)
        doc: firestore.DocumentSnapshot = doc_ref.get()

        if not doc.exists:
            return None

        data: Dict[str, Any] = doc.to_dict()
        return self._process_checkpoint_data_common(data)

    async def aget_tuple(self, config: RunnableConfig) -> Optional[CheckpointTuple]:
        """Obtiene el checkpoint de forma asíncrona."""
        thread_id: str = config["configurable"]["thread_id"]
        
        doc_ref: firestore.AsyncDocumentReference = self.async_db.collection(self.collection_name).document(thread_id)
        doc: firestore.DocumentSnapshot = await doc_ref.get()
        
        if not doc.exists:
            return None
        
        data: Dict[str, Any] = doc.to_dict()
        return self._process_checkpoint_data_common(data)

    def list(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """Lista checkpoints basados en criterios."""
        thread_id: Optional[str] = config["configurable"]["thread_id"] if config else None
        if filter:
            raise NotImplementedError("Filtrado no implementado")
        
        col_ref: firestore.CollectionReference = self.db.collection(self.collection_name)
        
        if thread_id:
            col_ref = col_ref.where("thread_id", "==", thread_id)
        
        docs: firestore.QuerySnapshot = col_ref.order_by(
            "timestamp", 
            direction=firestore.Query.DESCENDING
        ).limit(limit or 100).get()
        
        for doc in docs:
            yield self._process_checkpoint_data_common(doc.to_dict())

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Lista checkpoints de forma asíncrona."""
        thread_id: Optional[str] = config["configurable"]["thread_id"] if config else None
        if filter:
            raise NotImplementedError("Filtrado no implementado")
        
        col_ref: firestore.AsyncCollectionReference = self.async_db.collection(self.collection_name)
        
        if thread_id:
            col_ref = col_ref.where("thread_id", "==", thread_id)
        
        docs: firestore.QuerySnapshot = await col_ref.order_by(
            "timestamp", 
            direction=firestore.Query.DESCENDING
        ).limit(limit or 100).get()
        
        async for doc in docs:
            yield self._process_checkpoint_data_common(doc.to_dict())

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Guarda un checkpoint en Firestore."""
        thread_id: str = config["configurable"]["thread_id"]
        user_email: str = config["configurable"].get("user_email", "")
        timestamp: str = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')
        ts: str = checkpoint["id"]
        
        doc_ref: firestore.DocumentReference = self.db.collection(self.collection_name).document(thread_id)
        doc_data = {
            "checkpoint": self.serde.dumps(checkpoint),
            "metadata": self.serde.dumps(metadata),
            "thread_id": thread_id,
            "timestamp": timestamp
        }
        
        if user_email:
            doc_data["user_email"] = user_email
        
        doc_ref.set(doc_data)

        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
            },
        }

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Guarda un checkpoint de forma asíncrona."""
        thread_id: str = config["configurable"]["thread_id"]
        user_email: str = config["configurable"].get("user_email", "")
        timestamp: str = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S')
        ts: str = checkpoint["id"]
        
        doc_ref: firestore.AsyncDocumentReference = self.async_db.collection(
            self.collection_name
        ).document(thread_id)
        
        doc_data = {
            "checkpoint": self.serde.dumps(checkpoint),
            "metadata": self.serde.dumps(metadata),
            "thread_id": thread_id,
            "timestamp": timestamp
        }
        
        if user_email:
            doc_data["user_email"] = user_email
        
        await doc_ref.set(doc_data)

        return {
            "configurable": {
                "thread_id": thread_id,
                "thread_ts": ts,
            },
        }
    
    def put_writes(
        self,
        config: dict,
        writes: Sequence[Tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Guarda escrituras intermedias vinculadas a un checkpoint."""
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"]["checkpoint_ns"]
        checkpoint_id = config["configurable"]["checkpoint_id"]
        
        for idx, (channel, value) in enumerate(writes):
            doc_id = f"{thread_id}"
            type_, serialized_value = self.serde.dumps_typed(value)

            write_data = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "channel": channel,
                "type": type_,
                "value": serialized_value,
            }

            self.db.collection(self.pw_collection_name).document(doc_id).set(write_data, merge=True)

    def _process_checkpoint_data_common(self, data: Dict[str, Any]) -> CheckpointTuple:
        """Procesa los datos del checkpoint."""
        checkpoint: Checkpoint = self.serde.loads(data["checkpoint"])
        metadata: CheckpointMetadata = self.serde.loads(data["metadata"])
        thread_id: str = data["thread_id"]
        thread_ts: str = data["timestamp"]

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id, 
                "thread_ts": thread_ts
            }
        }
        return CheckpointTuple(
            config=config, 
            checkpoint=checkpoint, 
            metadata=metadata, 
            parent_config=None
        )
