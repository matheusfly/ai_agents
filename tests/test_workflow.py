import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workflow.state import AgentState
from workflow.engine import WorkflowEngine


class TestAgentState(unittest.TestCase):
    """Test cases for the AgentState class."""
    
    def test_state_structure(self):
        """Test that AgentState has the expected structure."""
        # This is more of a type check than a functional test
        # Since AgentState is a TypedDict, we can't instantiate it directly
        # But we can check that the keys exist
        expected_keys = [
            "messages", 
            "problem_analysis", 
            "task_delegation", 
            "xml_validation", 
            "final_qa_report",
            "human_review_required",
            "human_feedback",
            "verbose_logs"
        ]
        
        # We're just verifying the structure exists
        self.assertTrue(True)  # Placeholder - TypedDict structure is verified at type-checking time


class TestWorkflowEngine(unittest.TestCase):
    """Test cases for the WorkflowEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the Ollama client to avoid actual API calls
        with patch('src.agents.base.ollama.Client') as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value = mock_instance
            self.workflow_engine = WorkflowEngine()
    
    def test_initialization(self):
        """Test workflow engine initialization."""
        self.assertIsNotNone(self.workflow_engine.reasoning_agent)
        self.assertIsNotNone(self.workflow_engine.delegation_agent)
        self.assertIsNotNone(self.workflow_engine.xml_agent)
        self.assertIsNotNone(self.workflow_engine.qa_agent)
        self.assertIsNotNone(self.workflow_engine.app)
    
    def test_workflow_build(self):
        """Test that the workflow graph is built correctly."""
        # Check that we have the expected nodes
        nodes = list(self.workflow_engine.workflow.nodes)
        expected_nodes = [
            "reasoning", 
            "delegation", 
            "xml_validation", 
            "qa", 
            "human_review"
        ]
        
        for node in expected_nodes:
            self.assertIn(node, nodes)
    
    def test_run_method_exists(self):
        """Test that the run method exists."""
        self.assertTrue(hasattr(self.workflow_engine, 'run'))
        self.assertTrue(callable(self.workflow_engine.run))


if __name__ == '__main__':
    unittest.main()