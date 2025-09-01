from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
import time
import json
from typing import Dict, Any, List, Optional
import uuid

from src.utils.websocket import websocket_manager

class OllamaTracingCallback(BaseCallbackHandler):
    """Enhanced callback handler for tracing Ollama LLM calls with UI-specific formatting"""

    def __init__(self, websocket_manager=None):
        self.websocket_manager = websocket_manager
        self.current_run_id = None
        self.start_time = None
        self.token_count = 0
        self.model = "qwen3:latest"
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.agent_type = "unknown"

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: Optional[uuid.UUID] = None,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Run when LLM starts."""
        self.start_time = time.time()
        self.token_count = 0
        self.model = serialized.get("model", "qwen3:latest")

        # Extract agent type from metadata if available
        if metadata and "agent_type" in metadata:
            self.agent_type = metadata["agent_type"]

        # Generate a unique run ID
        self.current_run_id = f"ollama-{int(time.time())}-{id(self)}"

        # Use parent_run_id as the session_id if it exists
        session_id = str(parent_run_id) if parent_run_id else self.current_run_id

        # Calculate prompt tokens (simplified)
        self.prompt_tokens = sum(len(prompt.split()) for prompt in prompts)

        # Send start event with detailed metadata
        if self.websocket_manager:
            self.websocket_manager.broadcast({
                "type": "llm_start",
                "run_id": self.current_run_id,
                "session_id": session_id,
                "model": self.model,
                "prompts": prompts,
                "prompt_tokens": self.prompt_tokens,
                "timestamp": time.time(),
                "agent_type": self.agent_type
            })

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Optional[Any] = None,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any
    ) -> None:
        """Run when LLM generates a new token."""
        self.token_count += 1
        self.completion_tokens += 1
        self.total_tokens = self.prompt_tokens + self.completion_tokens

        # Broadcast token to UI with streaming capability
        if self.websocket_manager:
            self.websocket_manager.broadcast({
                "type": "llm_token",
                "run_id": self.current_run_id,
                "token": token,
                "token_count": self.token_count,
                "timestamp": time.time(),
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens
            })

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: Optional[uuid.UUID] = None,
        parent_run_id: Optional[uuid.UUID] = None,
        tags: Optional[List[str]] = None,
        **kwargs: Any
    ) -> None:
        """Run when LLM ends."""
        duration = time.time() - self.start_time

        # Calculate completion tokens
        self.completion_tokens = sum(len(gen.text.split()) for generations in response.generations for gen in generations)
        self.total_tokens = self.prompt_tokens + self.completion_tokens

        # Send completion event with performance metrics
        if self.websocket_manager:
            self.websocket_manager.broadcast({
                "type": "llm_end",
                "run_id": self.current_run_id,
                "duration": duration,
                "token_count": self.token_count,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "tokens_per_second": self.completion_tokens / max(duration, 0.1),
                "generations": [[{
                    "text": gen.text,
                    "generation_info": gen.generation_info
                } for gen in generations] for generations in response.generations],
                "timestamp": time.time()
            })

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
.
        if self.websocket_manager:
            self.websocket_manager.broadcast({
                "type": "llm_error",
                "run_id": self.current_run_id,
                "error": str(error),
                "error_type": type(error).__name__,
                "timestamp": time.time()
            })
