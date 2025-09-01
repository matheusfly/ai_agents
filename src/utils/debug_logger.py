"""
Enhanced debug logger for Multi-Agent system monitoring.
"""
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import threading
import queue
import logging
from functools import wraps

# Global debug state
DEBUG_ENABLED = True
LOG_QUEUE = queue.Queue()
WORKFLOW_STATE = {}
API_CALLS = []
OLLAMA_METRICS = []

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DebugLogger:
    """Enhanced debug logger for the Multi-Agent system."""
    
    def __init__(self):
        self.log_queue = LOG_QUEUE
        self.workflow_state = WORKFLOW_STATE
        self.api_calls = API_CALLS
        self.ollama_metrics = OLLAMA_METRICS
    
    def log(self, level: str, source: str, message: str, details: Dict = None, **kwargs):
        """Add a log entry to the debug system."""
        if not DEBUG_ENABLED:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "source": source.upper(),
            "message": message,
            "details": details or {},
            **kwargs
        }
        
        # Add to queue for real-time display
        try:
            self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # Remove oldest entry if queue is full
            try:
                self.log_queue.get_nowait()
                self.log_queue.put_nowait(log_entry)
            except queue.Empty:
                pass
        
        # Also log to standard logger
        getattr(logger, level.lower(), logger.info)(f"[{source}] {message}")
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                     duration: float, details: Dict = None):
        """Log an API call."""
        call_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method.upper(),
            "endpoint": endpoint,
            "status_code": status_code,
            "duration": f"{duration:.3f}s",
            "details": details or {}
        }
        
        self.api_calls.append(call_entry)
        
        # Keep only last 1000 API calls
        if len(self.api_calls) > 1000:
            self.api_calls = self.api_calls[-1000:]
        
        # Log the API call
        status_level = "ERROR" if status_code >= 400 else "INFO"
        self.log(status_level, "API", 
                f"{method} {endpoint} - {status_code} ({duration:.3f}s)",
                details)
    
    def log_workflow_step(self, step_name: str, status: str, 
                         agent: str = None, details: Dict = None):
        """Log a workflow step update."""
        step_info = {
            "name": step_name,
            "status": status,  # pending, active, completed, error
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        # Update workflow state
        self.workflow_state[step_name] = step_info
        
        # Log the step
        self.log("INFO", "WORKFLOW", 
                f"Step '{step_name}': {status}" + (f" ({agent})" if agent else ""),
                details)
    
    def log_ollama_interaction(self, model: str, action: str, 
                              duration: float = None, details: Dict = None):
        """Log Ollama model interaction."""
        metric_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "action": action,
            "duration": f"{duration:.3f}s" if duration else None,
            "details": details or {}
        }
        
        self.ollama_metrics.append(metric_entry)
        
        # Keep only last 500 metrics
        if len(self.ollama_metrics) > 500:
            self.ollama_metrics = self.ollama_metrics[-500:]
        
        # Log the interaction
        duration_str = f" ({duration:.3f}s)" if duration else ""
        self.log("INFO", "OLLAMA", 
                f"Model {model}: {action}{duration_str}",
                details)
    
    def log_langgraph_state(self, state_name: str, state_data: Dict, 
                           transition: str = None):
        """Log LangGraph state changes."""
        state_info = {
            "state": state_name,
            "data": state_data,
            "transition": transition,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log("DEBUG", "LANGGRAPH", 
                f"State: {state_name}" + (f" -> {transition}" if transition else ""),
                state_info)
    
    def get_logs(self, max_logs: int = 100) -> List[Dict]:
        """Get recent logs from the queue."""
        logs = []
        try:
            while len(logs) < max_logs and not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        
        return logs
    
    def get_workflow_state(self) -> Dict:
        """Get current workflow state."""
        return dict(self.workflow_state)
    
    def get_api_calls(self, max_calls: int = 100) -> List[Dict]:
        """Get recent API calls."""
        return self.api_calls[-max_calls:]
    
    def get_ollama_metrics(self, max_metrics: int = 100) -> List[Dict]:
        """Get recent Ollama metrics."""
        return self.ollama_metrics[-max_metrics:]
    
    def clear_logs(self):
        """Clear all logs and metrics."""
        # Clear queue
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break
        
        # Clear other data
        self.workflow_state.clear()
        self.api_calls.clear()
        self.ollama_metrics.clear()
        
        self.log("INFO", "DEBUG", "All logs and metrics cleared")


# Global debug logger instance
debug_logger = DebugLogger()


def log_api_call(func):
    """Decorator to log API calls."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        method = getattr(kwargs.get('request'), 'method', 'UNKNOWN')
        url = str(getattr(kwargs.get('request'), 'url', 'UNKNOWN'))
        
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Determine status code
            status_code = getattr(result, 'status_code', 200)
            
            debug_logger.log_api_call(method, url, status_code, duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            debug_logger.log_api_call(method, url, 500, duration, 
                                    {"error": str(e)})
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        method = getattr(kwargs.get('request'), 'method', 'UNKNOWN')
        url = str(getattr(kwargs.get('request'), 'url', 'UNKNOWN'))
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Determine status code
            status_code = getattr(result, 'status_code', 200)
            
            debug_logger.log_api_call(method, url, status_code, duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            debug_logger.log_api_call(method, url, 500, duration, 
                                    {"error": str(e)})
            raise
    
    # Return appropriate wrapper based on function type
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_workflow_step(step_name: str, status: str, agent: str = None, details: Dict = None):
    """Convenience function to log workflow steps."""
    debug_logger.log_workflow_step(step_name, status, agent, details)


def log_ollama_call(model: str, action: str, duration: float = None, details: Dict = None):
    """Convenience function to log Ollama interactions."""
    debug_logger.log_ollama_interaction(model, action, duration, details)


def log_debug(level: str, source: str, message: str, details: Dict = None):
    """Convenience function for general debug logging."""
    debug_logger.log(level, source, message, details)


# Context manager for timing operations
class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str, source: str = "SYSTEM"):
        self.operation_name = operation_name
        self.source = source
        self.start_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.time()
        debug_logger.log("DEBUG", self.source, f"Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        
        if exc_type is not None:
            debug_logger.log("ERROR", self.source, 
                           f"Failed: {self.operation_name} ({self.duration:.3f}s)",
                           {"error": str(exc_val)})
        else:
            debug_logger.log("SUCCESS", self.source, 
                           f"Completed: {self.operation_name} ({self.duration:.3f}s)")


# Function to enable/disable debugging
def set_debug_enabled(enabled: bool):
    """Enable or disable debug logging."""
    global DEBUG_ENABLED
    DEBUG_ENABLED = enabled
    debug_logger.log("INFO", "DEBUG", f"Debug logging {'enabled' if enabled else 'disabled'}")


# Initialize debug logging
debug_logger.log("INFO", "DEBUG", "Debug logging system initialized")
