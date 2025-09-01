from langchain_community.llms import Ollama
from src.utils.ollama_callback import OllamaTracingCallback
from src.utils.websocket import websocket_manager
import os

def get_llm(agent_type: str = "unknown"):
    """Get the Ollama LLM with tracing callbacks and agent metadata"""
    return Ollama(
        model=os.getenv("OLLAMA_MODEL", "qwen3:latest"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=0.3,
        callbacks=[OllamaTracingCallback(websocket_manager=websocket_manager)],
        metadata={"agent_type": agent_type}  # Pass agent type for UI filtering
    )
