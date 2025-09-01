from typing import Dict, Any, Optional
from src.workflow.state import AgentState


class HumanReviewInterface:
    """Interface for human-in-the-loop review system."""
    
    def __init__(self):
        self.pending_reviews = {}
    
    def request_review(self, session_id: str, state: AgentState) -> None:
        """Request a human review for the given state."""
        self.pending_reviews[session_id] = {
            "state": state,
            "status": "pending",
            "feedback": None
        }
    
    def submit_feedback(self, session_id: str, feedback: str) -> bool:
        """Submit human feedback for a review request."""
        if session_id in self.pending_reviews:
            self.pending_reviews[session_id]["status"] = "completed"
            self.pending_reviews[session_id]["feedback"] = feedback
            return True
        return False
    
    def get_pending_review(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a pending review for a session."""
        if session_id in self.pending_reviews:
            review = self.pending_reviews[session_id]
            if review["status"] == "pending":
                return review
        return None
    
    def get_completed_review(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a completed review for a session."""
        if session_id in self.pending_reviews:
            review = self.pending_reviews[session_id]
            if review["status"] == "completed":
                return review
        return None
    
    def should_request_review(self, state: AgentState) -> bool:
        """Determine if a human review should be requested based on the QA report."""
        qa_report = state.get("final_qa_report", "")
        
        # Simple heuristic: if the QA report contains "critical" or "major" issues,
        # request human review
        if "critical" in qa_report.lower() or "major" in qa_report.lower():
            return True
        
        # Another heuristic: if the QA score is below 80, request human review
        try:
            if "<score>" in qa_report:
                # Extract score from XML
                start = qa_report.find("<score>") + len("<score>")
                end = qa_report.find("</score>")
                if start > len("<score>") - 1 and end > start:
                    score = int(qa_report[start:end])
                    return score < 80
        except ValueError:
            # If we can't parse the score, default to not requesting review
            pass
        
        return False


class HumanReviewNode:
    """Node for handling human review in the workflow."""
    
    def __init__(self, review_interface: HumanReviewInterface):
        self.review_interface = review_interface
    
    def process(self, state: AgentState, session_id: str) -> Dict[str, Any]:
        """Process human review for the given state."""
        # Check if we already have feedback
        completed_review = self.review_interface.get_completed_review(session_id)
        if completed_review:
            return {
                "human_review_required": True,
                "human_feedback": completed_review["feedback"],
                "messages": state.get("messages", []) + [{
                    "role": "system",
                    "content": f"Human feedback received: {completed_review['feedback']}"
                }]
            }
        
        # Check if we need to request review
        pending_review = self.review_interface.get_pending_review(session_id)
        if not pending_review:
            # Request a new review
            self.review_interface.request_review(session_id, state)
            # In a real implementation, this would pause the workflow
            # For now, we'll simulate immediate feedback
            simulated_feedback = "Human review: The output looks good, approved for final delivery."
            self.review_interface.submit_feedback(session_id, simulated_feedback)
            
            return {
                "human_review_required": True,
                "human_feedback": simulated_feedback,
                "messages": state.get("messages", []) + [{
                    "role": "system",
                    "content": f"Human feedback received: {simulated_feedback}"
                }]
            }
        
        # If we're still waiting for review, return the state as is
        # In a real implementation, this would pause the workflow
        return {}