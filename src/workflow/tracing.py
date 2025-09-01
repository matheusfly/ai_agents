from typing import Dict, Any, Optional
import os
from datetime import datetime
import json


class LangSmithTracer:
    """LangSmith tracer for workflow monitoring and debugging."""
    
    def __init__(self, project_name: str = "multi-agent-prompt-engine"):
        self.project_name = project_name
        self.enabled = self._check_langsmith_availability()
        self.traces = []
    
    def _check_langsmith_availability(self) -> bool:
        """Check if LangSmith is available and configured."""
        try:
            import langsmith
            # Check if API key is set
            api_key = os.getenv("LANGSMITH_API_KEY")
            return api_key is not None and api_key != ""
        except ImportError:
            return False
    
    def start_trace(self, trace_id: str, trace_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Start a new trace."""
        if not self.enabled:
            return
            
        trace = {
            "id": trace_id,
            "type": trace_type,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "running",
            "spans": []
        }
        self.traces.append(trace)
    
    def end_trace(self, trace_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """End a trace."""
        if not self.enabled:
            return
            
        for trace in self.traces:
            if trace["id"] == trace_id:
                trace["end_time"] = datetime.now().isoformat()
                trace["status"] = "completed"
                trace["result"] = result
                break
    
    def add_span(self, trace_id: str, span_id: str, span_type: str, 
                 input_data: Any, output_data: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a span to a trace."""
        if not self.enabled:
            return
            
        span = {
            "id": span_id,
            "type": span_type,
            "start_time": datetime.now().isoformat(),
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {}
        }
        
        for trace in self.traces:
            if trace["id"] == trace_id:
                trace["spans"].append(span)
                break
    
    def log_error(self, trace_id: str, error_message: str, 
                  error_type: str = "unknown") -> None:
        """Log an error in a trace."""
        if not self.enabled:
            return
            
        for trace in self.traces:
            if trace["id"] == trace_id:
                if "errors" not in trace:
                    trace["errors"] = []
                trace["errors"].append({
                    "message": error_message,
                    "type": error_type,
                    "timestamp": datetime.now().isoformat()
                })
                trace["status"] = "error"
                break
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific trace by ID."""
        for trace in self.traces:
            if trace["id"] == trace_id:
                return trace
        return None
    
    def get_all_traces(self) -> list:
        """Get all traces."""
        return self.traces
    
    def export_traces(self, filepath: str) -> None:
        """Export traces to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.traces, f, indent=2)


class CheckpointStorage:
    """Storage for workflow checkpoints."""
    
    def __init__(self, storage_path: str = "./checkpoints"):
        self.storage_path = storage_path
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
    
    def save_checkpoint(self, session_id: str, checkpoint_data: Dict[str, Any]) -> None:
        """Save a checkpoint."""
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        with open(filepath, 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
    
    def load_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint."""
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None
    
    def list_checkpoints(self) -> list:
        """List all available checkpoints."""
        checkpoints = []
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json extension
                checkpoints.append(session_id)
        return checkpoints
    
    def delete_checkpoint(self, session_id: str) -> bool:
        """Delete a checkpoint."""
        filepath = os.path.join(self.storage_path, f"{session_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False


# Global instances
tracer = LangSmithTracer()
checkpoint_storage = CheckpointStorage()