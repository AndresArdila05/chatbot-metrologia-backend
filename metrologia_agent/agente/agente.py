import logging
from typing import Annotated, List, TypedDict, Optional
from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage

from utils.paths import llm_model_gemini
from metrologia_agent.memory.firestoresaver import FirestoreSaver
from metrologia_agent.agente.tools import tools_metrologia
from metrologia_agent.agente.prompts import prompt_agente_metrologia

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

llm_with_tools = llm_model_gemini.bind_tools(tools_metrologia)

class MetrologiaState(TypedDict):
    """Estado del agente de metrología."""
    messages: Annotated[List[BaseMessage], add_messages]

def call_model(state: MetrologiaState) -> dict:
    """
    Nodo que invoca al LLM con las herramientas disponibles.
    
    Args:
        state: Estado actual de la conversación
        
    Returns:
        Estado actualizado con la respuesta del modelo
    """
    logger.info("[AGENTE] Invocando LLM")
    
    system_prompt = SystemMessage(content=prompt_agente_metrologia)
    messages = [system_prompt] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    if hasattr(response, "tool_calls") and response.tool_calls:
        logger.info(f"[AGENTE] LLM solicitó {len(response.tool_calls)} herramienta(s)")
    else:
        logger.info("[AGENTE] LLM generó respuesta final")
    
    return {"messages": [response]}

def should_continue(state: MetrologiaState) -> str:
    """
    Función condicional que determina si continuar con herramientas o finalizar.
    
    Args:
        state: Estado actual de la conversación
        
    Returns:
        Nombre del siguiente nodo o END
    """
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        logger.info("[AGENTE] Ruta: ejecutar herramientas")
        return "tools"
    
    logger.info("[AGENTE] Ruta: finalizar conversación")
    return END

tool_node = ToolNode(tools_metrologia)

builder = StateGraph(MetrologiaState)

builder.add_node("agent", call_model)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

builder.add_edge("tools", "agent")

memory = FirestoreSaver(
    database="pln-proyecto",
    collection_name="metrologia_checkpoints"
)

agente_metrologia = builder.compile(
    checkpointer=memory,
    name="agente_metrologia"
)

logger.info("[AGENTE] Agente de metrología compilado exitosamente")
