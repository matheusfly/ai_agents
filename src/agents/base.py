from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain_core.messages import BaseMessage
import ollama


class BaseAgent(ABC):
    """Base class for all agents in the multi-agent system."""
    
    def __init__(self, name: str, model: str, base_url: str = "http://localhost:11434"):
        self.name = name
        self.model = model
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the current state and return updated state."""
        pass
    
    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call the LLM with the given prompt."""
        messages = []
        
        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })
            
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        response = self.client.chat(
            model=self.model,
            messages=messages
        )
        
        return response['message']['content']
    
    def format_output(self, content: str) -> str:
        """Format the output content."""
        # For now, just return the content as is
        # In the future, we might add formatting or validation
        return content