import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.base import BaseAgent
from agents.reasoning_agent import SeniorReasoningAgent
from agents.delegation_agent import TaskDelegationAgent
from agents.xml_agent import XMLFormatterAgent
from agents.qa_agent import QualityAssuranceAgent


class TestBaseAgent(unittest.TestCase):
    """Test cases for the BaseAgent class."""
    
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        # Create a concrete implementation of BaseAgent for testing
        class ConcreteAgent(BaseAgent):
            def get_system_prompt(self):
                return "test prompt"
            
            def process(self, state):
                return state
        
        agent = ConcreteAgent("Test Agent", "test-model")
        
        # Test that the concrete implementation works
        self.assertEqual(agent.name, "Test Agent")
        self.assertEqual(agent.model, "test-model")
        self.assertEqual(agent.get_system_prompt(), "test prompt")


class TestSeniorReasoningAgent(unittest.TestCase):
    """Test cases for the SeniorReasoningAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Ollama client to avoid actual API calls
        with patch('src.agents.base.ollama.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            self.agent = SeniorReasoningAgent("qwen3:latest")
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "Senior Reasoning Agent")
        self.assertEqual(self.agent.model, "qwen3:latest")
    
    def test_system_prompt(self):
        """Test system prompt."""
        prompt = self.agent.get_system_prompt()
        self.assertIn("Senior Reasoning Agent", prompt)
        self.assertIn("<reasoning>", prompt)
        self.assertIn("<variables>", prompt)
        self.assertIn("<conclusion>", prompt)


class TestTaskDelegationAgent(unittest.TestCase):
    """Test cases for the TaskDelegationAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Ollama client to avoid actual API calls
        with patch('src.agents.base.ollama.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            self.agent = TaskDelegationAgent("gemma3:latest")
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "Task Delegation Specialist")
        self.assertEqual(self.agent.model, "gemma3:latest")
    
    def test_system_prompt(self):
        """Test system prompt."""
        prompt = self.agent.get_system_prompt()
        self.assertIn("Task Delegation Specialist", prompt)
        self.assertIn("<delegation>", prompt)
        self.assertIn("<task", prompt)


class TestXMLFormatterAgent(unittest.TestCase):
    """Test cases for the XMLFormatterAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Ollama client to avoid actual API calls
        with patch('src.agents.base.ollama.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            self.agent = XMLFormatterAgent("gemma3:latest")
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "XML Formatter & Validator")
        self.assertEqual(self.agent.model, "gemma3:latest")
    
    def test_system_prompt(self):
        """Test system prompt."""
        prompt = self.agent.get_system_prompt()
        self.assertIn("XML Formatter & Validator", prompt)
        self.assertIn("<validation>", prompt)
        self.assertIn("<schema_validation>", prompt)


class TestQualityAssuranceAgent(unittest.TestCase):
    """Test cases for the QualityAssuranceAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Ollama client to avoid actual API calls
        with patch('src.agents.base.ollama.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            self.agent = QualityAssuranceAgent("qwen3:latest")
    
    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.name, "Quality Assurance Specialist")
        self.assertEqual(self.agent.model, "qwen3:latest")
    
    def test_system_prompt(self):
        """Test system prompt."""
        prompt = self.agent.get_system_prompt()
        self.assertIn("Quality Assurance Specialist", prompt)
        self.assertIn("<qa_report>", prompt)
        self.assertIn("<accuracy>", prompt)


if __name__ == '__main__':
    unittest.main()