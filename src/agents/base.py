from abc import ABC, abstractmethod
from typing import Dict, Any
from src.utils.llm import get_llm


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""

    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.llm = get_llm(agent_type=self.name)

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state."""
        pass

    def format_output(self, content: str) -> str:
        """Format the output content."""
        # For now, just return the content as is
        # In the future, we might add formatting or validation
        return content