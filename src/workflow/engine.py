from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import uuid
import time

from src.workflow.state import AgentState
from src.workflow.human_review import HumanReviewInterface, HumanReviewNode
from src.workflow.tracing import tracer, checkpoint_storage
from src.agents import (
    SeniorReasoningAgent, 
    TaskDelegationAgent, 
    XMLFormatterAgent, 
    QualityAssuranceAgent
)
from src.config import settings


class WorkflowEngine:
    """LangGraph workflow engine with DAG subgraphs."""
    
    def __init__(self):
        # Initialize agents
        self.reasoning_agent = SeniorReasoningAgent(
            model=settings.QWEN_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        self.delegation_agent = TaskDelegationAgent(
            model=settings.GEMMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        self.xml_agent = XMLFormatterAgent(
            model=settings.GEMMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        self.qa_agent = QualityAssuranceAgent(
            model=settings.QWEN_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )
        
        # Initialize human review system
        self.human_review_interface = HumanReviewInterface()
        self.human_review_node = HumanReviewNode(self.human_review_interface)
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
        
        # Set up memory
        self.memory = MemorySaver()
        
        # Compile the workflow
        self.app = self.workflow.compile(checkpointer=self.memory)
        
        # Trace ID for this engine instance
        self.trace_id = str(uuid.uuid4())
        tracer.start_trace(self.trace_id, "workflow_engine", {
            "qwen_model": settings.QWEN_MODEL,
            "gemma_model": settings.GEMMA_MODEL
        })
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("delegation", self._delegation_node)
        workflow.add_node("xml_validation", self._xml_validation_node)
        workflow.add_node("qa", self._qa_node)
        workflow.add_node("human_review", self._human_review_node)
        
        # Add edges between nodes
        workflow.add_edge("reasoning", "delegation")
        workflow.add_edge("delegation", "xml_validation")
        workflow.add_edge("xml_validation", "qa")
        
        # Add conditional edge for human review
        workflow.add_conditional_edges(
            "qa",
            self._should_human_review,
            {
                "human_review": "human_review",
                "end": END
            }
        )
        
        # Add edge from human review to end
        workflow.add_edge("human_review", END)
        
        # Set the entry point
        workflow.set_entry_point("reasoning")
        
        return workflow
    
    def _reasoning_node(self, state: AgentState) -> Dict[str, Any]:
        """Process the reasoning node."""
        span_id = str(uuid.uuid4())
        tracer.add_span(
            self.trace_id, 
            span_id, 
            "reasoning", 
            {"input": state.get("messages", [])}, 
            {}
        )
        
        try:
            result = self.reasoning_agent.process(state)
            tracer.add_span(
                self.trace_id, 
                f"{span_id}_result", 
                "reasoning_result", 
                {}, 
                result
            )
            return result
        except Exception as e:
            tracer.log_error(self.trace_id, str(e), "reasoning_error")
            raise
    
    def _delegation_node(self, state: AgentState) -> Dict[str, Any]:
        """Process the delegation node."""
        span_id = str(uuid.uuid4())
        tracer.add_span(
            self.trace_id, 
            span_id, 
            "delegation", 
            {"problem_analysis": state.get("problem_analysis", "")}, 
            {}
        )
        
        try:
            result = self.delegation_agent.process(state)
            tracer.add_span(
                self.trace_id, 
                f"{span_id}_result", 
                "delegation_result", 
                {}, 
                result
            )
            return result
        except Exception as e:
            tracer.log_error(self.trace_id, str(e), "delegation_error")
            raise
    
    def _xml_validation_node(self, state: AgentState) -> Dict[str, Any]:
        """Process the XML validation node."""
        span_id = str(uuid.uuid4())
        tracer.add_span(
            self.trace_id, 
            span_id, 
            "xml_validation", 
            {"task_delegation": state.get("task_delegation", "")}, 
            {}
        )
        
        try:
            result = self.xml_agent.process(state)
            tracer.add_span(
                self.trace_id, 
                f"{span_id}_result", 
                "xml_validation_result", 
                {}, 
                result
            )
            return result
        except Exception as e:
            tracer.log_error(self.trace_id, str(e), "xml_validation_error")
            raise
    
    def _qa_node(self, state: AgentState) -> Dict[str, Any]:
        """Process the QA node."""
        span_id = str(uuid.uuid4())
        tracer.add_span(
            self.trace_id, 
            span_id, 
            "qa", 
            {"xml_validation": state.get("xml_validation", "")}, 
            {}
        )
        
        try:
            result = self.qa_agent.process(state)
            tracer.add_span(
                self.trace_id, 
                f"{span_id}_result", 
                "qa_result", 
                {}, 
                result
            )
            return result
        except Exception as e:
            tracer.log_error(self.trace_id, str(e), "qa_error")
            raise
    
    def _human_review_node(self, state: AgentState) -> Dict[str, Any]:
        """Process the human review node."""
        # Process human review with session ID
        session_id = "default_session"  # In a real app, this would come from the config
        return self.human_review_node.process(state, session_id)
    
    def _should_human_review(self, state: AgentState) -> str:
        """Determine if human review is required."""
        # Check if human review is needed based on QA report
        return "human_review" if self.human_review_interface.should_request_review(state) else "end"
    
    def run(self, input_message: str) -> Dict[str, Any]:
        """Run the workflow with the given input."""
        initial_state = {
            "messages": [{"role": "user", "content": input_message}],
            "problem_analysis": "",
            "task_delegation": "",
            "xml_validation": "",
            "final_qa_report": "",
            "human_review_required": False,
            "human_feedback": "",
            "verbose_logs": []
        }
        
        # Save initial checkpoint
        session_id = str(uuid.uuid4())
        checkpoint_storage.save_checkpoint(session_id, {
            "state": initial_state,
            "timestamp": time.time(),
            "status": "started"
        })
        
        config = {"configurable": {"thread_id": session_id}}
        result = self.app.invoke(initial_state, config)
        
        # Save final checkpoint
        checkpoint_storage.save_checkpoint(session_id, {
            "state": result,
            "timestamp": time.time(),
            "status": "completed"
        })
        
        # End trace
        tracer.end_trace(self.trace_id, result)
        
        return result
    
    def submit_human_feedback(self, session_id: str, feedback: str) -> bool:
        """Submit human feedback for a review."""
        return self.human_review_interface.submit_feedback(session_id, feedback)
    
    def get_trace(self) -> Dict[str, Any]:
        """Get the trace for this workflow engine."""
        return tracer.get_trace(self.trace_id) or {}