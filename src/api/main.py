from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
import uuid
import json
import time

from src.workflow import WorkflowEngine
from src.utils import (
    ollama_monitor, 
    security_manager, 
    access_control,
    performance_monitor,
    analytics_engine,
    data_exporter,
    report_generator
)
from src.utils.debug_logger import debug_logger, log_debug, log_workflow_step, Timer
from src.config import settings

app = FastAPI(title="Multi-Agent Prompt Engine API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global workflow engine instance
workflow_engine = WorkflowEngine()

# Store for active sessions
active_sessions = {}

# Store for SSE connections
sse_connections = {}


class PromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    session_id: str
    feedback: str


class SessionStatus(BaseModel):
    session_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    logs: List[Dict[str, Any]] = []


class AuthRequest(BaseModel):
    user_id: str
    password: str


class AuthResponse(BaseModel):
    session_id: str
    permissions: List[str]


class ExportRequest(BaseModel):
    session_id: str
    format: str = "json"


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Multi-Agent Prompt Engine API"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    server_status = ollama_monitor.check_server_status()
    system_metrics = performance_monitor.collect_system_metrics()
    ollama_metrics = performance_monitor.collect_ollama_metrics()
    
    return {
        "status": "healthy" if server_status else "unhealthy",
        "ollama_server": "running" if server_status else "not running",
        "models": ollama_monitor.client.list_models(),
        "system_metrics": system_metrics,
        "ollama_metrics": ollama_metrics
    }


@app.post("/auth", response_model=AuthResponse)
async def authenticate(request: AuthRequest):
    """Authenticate a user and create a session."""
    # In a real implementation, you would verify credentials against a database
    # For now, we'll create a session with basic permissions
    permissions = ["read_prompts", "write_prompts", "execute_workflows", "view_logs", "export_data"]
    session_id = security_manager.create_session(request.user_id, permissions)
    
    # Log the authentication event
    security_manager.log_audit_event(
        "authentication", 
        request.user_id, 
        {"action": "login", "ip_address": "unknown"}
    )
    
    return AuthResponse(session_id=session_id, permissions=permissions)


@app.post("/process-prompt", response_model=SessionStatus)
async def process_prompt(
    request: PromptRequest, 
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """Process a prompt through the multi-agent workflow."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "execute_workflows"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Store session
    active_sessions[session_id] = {
        "status": "processing",
        "result": None,
        "logs": [],
        "last_updated": time.time()
    }
    
    # Initialize SSE connections for this session
    sse_connections[session_id] = []
    
    # Log the prompt processing event
    user_id = "anonymous"
    if authorization:
        session = security_manager.validate_session(authorization)
        if session:
            user_id = session["user_id"]
    
    security_manager.log_audit_event(
        "prompt_processing", 
        user_id, 
        {"session_id": session_id, "prompt_length": len(request.prompt)}
    )
    
    # Run workflow in background
    background_tasks.add_task(run_workflow, session_id, request.prompt, user_id)
    
    return SessionStatus(
        session_id=session_id,
        status="processing"
    )


@app.get("/session/{session_id}", response_model=SessionStatus)
async def get_session_status(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    """Get the status of a session."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "view_logs"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    return SessionStatus(
        session_id=session_id,
        status=session["status"],
        result=session["result"],
        logs=session["logs"]
    )


@app.post("/submit-feedback")
async def submit_feedback(
    request: FeedbackRequest,
    authorization: Optional[str] = Header(None)
):
    """Submit human feedback for a session."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
    
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    success = workflow_engine.submit_human_feedback(request.session_id, request.feedback)
    
    if success:
        # Update session status
        active_sessions[request.session_id]["status"] = "feedback_received"
        
        # Log the feedback submission
        user_id = "anonymous"
        if authorization:
            session = security_manager.validate_session(authorization)
            if session:
                user_id = session["user_id"]
        
        security_manager.log_audit_event(
            "feedback_submission", 
            user_id, 
            {"session_id": request.session_id, "feedback_length": len(request.feedback)}
        )
        
        return {"message": "Feedback submitted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to submit feedback")


@app.get("/models")
async def list_models():
    """List available models."""
    models = ollama_monitor.client.list_models()
    return {"models": models}


@app.get("/stream-workflow/{session_id}")
async def stream_workflow(
    session_id: str,
    authorization: Optional[str] = Header(None)
):
    """Stream workflow updates using Server-Sent Events."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "view_logs"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # Keep track of last sent log index
        last_log_index = 0
        
        while True:
            # Check if session still exists
            if session_id not in active_sessions:
                break
                
            session = active_sessions[session_id]
            
            # Send new logs
            logs = session.get("logs", [])
            if len(logs) > last_log_index:
                for i in range(last_log_index, len(logs)):
                    log_entry = logs[i]
                    data = {
                        "status": session["status"],
                        "log": log_entry
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                last_log_index = len(logs)
            
            # If workflow is completed, send final update and break
            if session["status"] in ["completed", "error", "feedback_received"]:
                final_data = {
                    "status": session["status"],
                    "result": session.get("result"),
                    "final": True
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                break
            
            # Wait before checking again
            await asyncio.sleep(1)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/performance/metrics")
async def get_performance_metrics():
    """Get current performance metrics."""
    system_metrics = performance_monitor.collect_system_metrics()
    ollama_metrics = performance_monitor.collect_ollama_metrics()
    
    return {
        "system": system_metrics,
        "ollama": ollama_metrics
    }


@app.get("/performance/history")
async def get_performance_history(days: int = 7):
    """Get performance metrics history."""
    history = performance_monitor.get_metrics_history(days)
    return {"metrics": history}


@app.get("/analytics/report")
async def get_analytics_report():
    """Get analytics report with insights and recommendations."""
    report = analytics_engine.create_performance_report()
    return report


@app.post("/export/session")
async def export_session_data(
    request: ExportRequest,
    authorization: Optional[str] = Header(None)
):
    """Export session data in the specified format."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "export_data"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = active_sessions[request.session_id]
    
    try:
        exported_data = data_exporter.export_session_data(session_data, request.format)
        filename = data_exporter.generate_export_filename(f"session_{request.session_id}", request.format)
        
        # Determine content type
        content_type = "application/json"
        if request.format.lower() == "csv":
            content_type = "text/csv"
        elif request.format.lower() == "xml":
            content_type = "application/xml"
        
        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/export/logs")
async def export_session_logs(
    request: ExportRequest,
    authorization: Optional[str] = Header(None)
):
    """Export session logs in the specified format."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "export_data"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if request.session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    logs = active_sessions[request.session_id].get("logs", [])
    
    try:
        exported_data = data_exporter.export_logs(logs, request.format)
        filename = data_exporter.generate_export_filename(f"logs_{request.session_id}", request.format)
        
        # Determine content type
        content_type = "application/json"
        if request.format.lower() == "csv":
            content_type = "text/csv"
        elif request.format.lower() == "xml":
            content_type = "application/xml"
        
        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/export/report/performance")
async def export_performance_report(
    format: str = "json",
    authorization: Optional[str] = Header(None)
):
    """Export performance report in the specified format."""
    # Check authentication if provided
    if authorization:
        session = security_manager.validate_session(authorization)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")
        # Check permission
        if not access_control.check_permission(authorization, "export_data"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Generate performance report
    report = analytics_engine.create_performance_report()
    
    try:
        exported_data = data_exporter.export_performance_report(report, format)
        filename = data_exporter.generate_export_filename("performance_report", format)
        
        # Determine content type
        content_type = "application/json"
        if format.lower() == "csv":
            content_type = "text/csv"
        elif format.lower() == "xml":
            content_type = "application/xml"
        
        return Response(
            content=exported_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Debug endpoints
@app.get("/debug/logs")
async def get_debug_logs(max_logs: int = 100):
    """Get debug logs for the dashboard."""
    logs = debug_logger.get_logs(max_logs)
    return {"logs": logs}


@app.get("/debug/workflow")
async def get_workflow_state():
    """Get current workflow state."""
    state = debug_logger.get_workflow_state()
    return {"workflow_state": state}


@app.get("/debug/api-calls")
async def get_api_calls(max_calls: int = 100):
    """Get recent API calls."""
    calls = debug_logger.get_api_calls(max_calls)
    return {"api_calls": calls}


@app.get("/debug/ollama-metrics")
async def get_ollama_metrics(max_metrics: int = 100):
    """Get Ollama interaction metrics."""
    metrics = debug_logger.get_ollama_metrics(max_metrics)
    return {"ollama_metrics": metrics}


@app.post("/debug/clear")
async def clear_debug_data():
    """Clear all debug data."""
    debug_logger.clear_logs()
    return {"message": "Debug data cleared"}


@app.get("/debug/system-info")
async def get_system_info():
    """Get comprehensive system information."""
    import psutil
    import platform
    
    system_info = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        },
        "cpu": {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        "memory": psutil.virtual_memory()._asdict(),
        "disk": psutil.disk_usage('/')._asdict(),
        "network": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
        "timestamp": time.time()
    }
    
    return system_info


async def run_workflow(session_id: str, prompt: str, user_id: str):
    """Run the workflow in the background with enhanced debug logging."""
    start_time = time.time()
    
    # Log workflow start
    log_debug("INFO", "WORKFLOW", f"Starting workflow for session {session_id}", 
             {"user_id": user_id, "prompt_length": len(prompt)})
    log_workflow_step("Workflow Initialization", "active", "System")
    
    try:
        with Timer("Complete Workflow Execution", "WORKFLOW"):
            # Log workflow steps
            log_workflow_step("Prompt Analysis", "active", "Senior Reasoning Agent")
            
            # Run the workflow
            result = workflow_engine.run(prompt)
            
            log_workflow_step("Prompt Analysis", "completed", "Senior Reasoning Agent")
            log_workflow_step("Task Delegation", "completed", "Delegation Specialist")
            log_workflow_step("XML Validation", "completed", "XML Validator")
            log_workflow_step("Quality Assurance", "completed", "QA Specialist")
            
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update session
        active_sessions[session_id]["status"] = "completed"
        active_sessions[session_id]["result"] = result
        active_sessions[session_id]["logs"] = result.get("verbose_logs", [])
        active_sessions[session_id]["last_updated"] = time.time()
        
        # Enhanced debug logging
        log_debug("SUCCESS", "WORKFLOW", 
                 f"Workflow completed for session {session_id} in {execution_time:.3f}s",
                 {"result_size": len(str(result)), "steps_completed": 4})
        
        log_workflow_step("Workflow Completion", "completed", "System", 
                         {"execution_time": execution_time, "result_size": len(str(result))})
        
        # Log completion
        security_manager.log_audit_event(
            "workflow_completed", 
            user_id, 
            {"session_id": session_id, "result_length": len(str(result))}
        )
        
        # Collect and log performance metrics
        agent_metrics = performance_monitor.collect_agent_metrics(
            "workflow_engine",
            execution_time,
            len(prompt),
            len(str(result))
        )
        performance_monitor.log_metrics(agent_metrics)
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Log error with debug system
        log_debug("ERROR", "WORKFLOW", 
                 f"Workflow failed for session {session_id}: {str(e)}",
                 {"execution_time": execution_time, "error_type": type(e).__name__})
        
        log_workflow_step("Workflow Execution", "error", "System", 
                         {"error": str(e), "execution_time": execution_time})
        
        # Update session with error
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["result"] = {"error": str(e)}
        active_sessions[session_id]["logs"] = [
            {"timestamp": time.time(), "agent": "system", "message": f"Error: {str(e)}", "type": "error"}
        ]
        active_sessions[session_id]["last_updated"] = time.time()
        
        # Log error
        security_manager.log_audit_event(
            "workflow_error", 
            user_id, 
            {"session_id": session_id, "error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )