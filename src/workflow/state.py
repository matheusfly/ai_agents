from typing import Annotated, Sequence, Dict, Any, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """State object for the LangGraph workflow."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    problem_analysis: str  # XML string
    task_delegation: str   # XML string
    xml_validation: str    # XML string
    final_qa_report: str   # XML string
    human_review_required: bool
    human_feedback: str
    verbose_logs: List[Dict[str, Any]]  # Verbose logs for UI display