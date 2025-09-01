import streamlit as st
import requests
import json
import time
import threading
import queue
from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psutil
import subprocess
import re

# Configure the page
st.set_page_config(
    page_title="Multi-Agent Debug Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = "http://localhost:8000"
OLLAMA_BASE_URL = "http://localhost:11434"

# Initialize session state for debugging
if "debug_enabled" not in st.session_state:
    st.session_state.debug_enabled = True
if "live_logs" not in st.session_state:
    st.session_state.live_logs = []
if "ollama_metrics" not in st.session_state:
    st.session_state.ollama_metrics = []
if "api_calls" not in st.session_state:
    st.session_state.api_calls = []
if "workflow_steps" not in st.session_state:
    st.session_state.workflow_steps = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "result" not in st.session_state:
    st.session_state.result = None
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

# Custom CSS for better styling
st.markdown("""
<style>
    .debug-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
    }
    .error-log {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .warning-log {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .info-log {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .success-log {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .workflow-step {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        margin: 5px;
        transition: all 0.3s ease;
    }
    .workflow-step.active {
        border-color: #4CAF50;
        background: #f8fff8;
    }
    .workflow-step.completed {
        border-color: #2196F3;
        background: #f0f8ff;
    }
    .workflow-step.error {
        border-color: #f44336;
        background: #fff5f5;
    }
    .live-log-container {
        max-height: 400px;
        overflow-y: auto;
        background: #1e1e1e;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def get_system_metrics():
    """Get current system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3)
        }
    except Exception as e:
        return {"error": str(e)}

def get_ollama_status():
    """Get Ollama server status and metrics."""
    try:
        # Check if Ollama is running
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            
            # Get process info
            ollama_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                if 'ollama' in proc.info['name'].lower():
                    ollama_processes.append(proc.info)
            
            return {
                "status": "running",
                "models_count": len(models),
                "models": [m["name"] for m in models],
                "processes": ollama_processes,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_api_health():
    """Get API server health status."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "data": response.json(),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def add_live_log(level: str, source: str, message: str, details: Dict = None):
    """Add a log entry to the live logs."""
    log_entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "level": level,
        "source": source,
        "message": message,
        "details": details or {}
    }
    
    st.session_state.live_logs.append(log_entry)
    
    # Keep only last 1000 logs
    if len(st.session_state.live_logs) > 1000:
        st.session_state.live_logs = st.session_state.live_logs[-1000:]

def monitor_workflow_step(step_name: str, status: str, details: Dict = None):
    """Monitor and update workflow step status."""
    step_info = {
        "name": step_name,
        "status": status,  # pending, active, completed, error
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    
    # Update or add step
    step_found = False
    for i, step in enumerate(st.session_state.workflow_steps):
        if step["name"] == step_name:
            st.session_state.workflow_steps[i] = step_info
            step_found = True
            break
    
    if not step_found:
        st.session_state.workflow_steps.append(step_info)
    
    # Add to live logs
    add_live_log("INFO", "WORKFLOW", f"{step_name}: {status}", details)

# Header
st.markdown("""
<div class="debug-header">
    <h1>🔧 Multi-Agent Debug Dashboard</h1>
    <p>Live monitoring of LangGraph workflow, Ollama processes, and API calls</p>
</div>
""", unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.header("🛠️ Debug Controls")
    
    # Auto-refresh toggle
    st.session_state.auto_refresh = st.toggle("🔄 Auto Refresh", value=st.session_state.auto_refresh)
    
    if st.session_state.auto_refresh:
        refresh_interval = st.slider("Refresh Interval (seconds)", 1, 10, 2)
    
    # Debug level filter
    debug_levels = st.multiselect(
        "Log Levels",
        ["ERROR", "WARNING", "INFO", "DEBUG", "SUCCESS"],
        default=["ERROR", "WARNING", "INFO", "SUCCESS"]
    )
    
    # Clear logs button
    if st.button("🗑️ Clear Logs"):
        st.session_state.live_logs = []
        st.session_state.api_calls = []
        st.session_state.workflow_steps = []
        st.rerun()
    
    # Manual refresh button
    if st.button("🔄 Refresh Now"):
        st.rerun()

# Main dashboard
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🖥️ System Status", 
    "🔗 Live Logs", 
    "🧠 LangGraph Flow", 
    "🤖 Ollama Monitor", 
    "📡 API Calls",
    "🧪 Prompt Testing"
])

with tab1:
    st.header("System Status Overview")
    
    # Get current metrics
    system_metrics = get_system_metrics()
    ollama_status = get_ollama_status()
    api_health = get_api_health()
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>💻 System CPU</h4>
            <h2>{:.1f}%</h2>
        </div>
        """.format(system_metrics.get("cpu_percent", 0)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🧠 Memory</h4>
            <h2>{:.1f}%</h2>
            <p>{:.1f} GB available</p>
        </div>
        """.format(
            system_metrics.get("memory_percent", 0),
            system_metrics.get("memory_available_gb", 0)
        ), unsafe_allow_html=True)
    
    with col3:
        status_color = "🟢" if ollama_status.get("status") == "running" else "🔴"
        st.markdown("""
        <div class="metric-card">
            <h4>🤖 Ollama {}</h4>
            <h2>{}</h2>
            <p>{} models loaded</p>
        </div>
        """.format(
            status_color,
            ollama_status.get("status", "unknown").title(),
            ollama_status.get("models_count", 0)
        ), unsafe_allow_html=True)
    
    with col4:
        api_color = "🟢" if api_health.get("status") == "healthy" else "🔴"
        st.markdown("""
        <div class="metric-card">
            <h4>📡 API Server {}</h4>
            <h2>{}</h2>
        </div>
        """.format(
            api_color,
            api_health.get("status", "unknown").title()
        ), unsafe_allow_html=True)
    
    # Detailed system info
    st.subheader("📊 Detailed Metrics")
    
    if system_metrics.get("error"):
        st.error(f"System metrics error: {system_metrics['error']}")
    else:
        # CPU and Memory charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Create CPU gauge
            fig_cpu = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = system_metrics.get("cpu_percent", 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "CPU Usage (%)"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_cpu.update_layout(height=300)
            st.plotly_chart(fig_cpu, use_container_width=True)
        
        with col2:
            # Create Memory gauge
            fig_mem = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = system_metrics.get("memory_percent", 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Memory Usage (%)"},
                delta = {'reference': 50},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_mem.update_layout(height=300)
            st.plotly_chart(fig_mem, use_container_width=True)

with tab2:
    st.header("🔗 Live System Logs")
    
    # Log controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search logs", placeholder="Enter search term...")
    with col2:
        max_logs = st.number_input("Max logs", min_value=10, max_value=1000, value=100)
    with col3:
        log_format = st.selectbox("Format", ["Detailed", "Compact"])
    
    # Add some sample logs for demonstration
    if len(st.session_state.live_logs) < 5:
        sample_logs = [
            ("INFO", "API", "Server started successfully on port 8000"),
            ("SUCCESS", "OLLAMA", "Connected to Ollama server at localhost:11434"),
            ("INFO", "WORKFLOW", "Initialized LangGraph workflow engine"),
            ("DEBUG", "SYSTEM", "Loading agent configurations"),
            ("INFO", "UI", "Streamlit dashboard initialized")
        ]
        
        for level, source, message in sample_logs:
            add_live_log(level, source, message)
    
    # Filter logs
    filtered_logs = st.session_state.live_logs
    if search_term:
        filtered_logs = [log for log in filtered_logs if search_term.lower() in log["message"].lower()]
    
    filtered_logs = [log for log in filtered_logs if log["level"] in debug_levels]
    filtered_logs = filtered_logs[-max_logs:]
    
    # Display logs
    st.markdown('<div class="live-log-container">', unsafe_allow_html=True)
    
    logs_container = st.container()
    with logs_container:
        for log in reversed(filtered_logs):
            level_colors = {
                "ERROR": "🔴",
                "WARNING": "🟡", 
                "INFO": "🔵",
                "DEBUG": "⚪",
                "SUCCESS": "🟢"
            }
            
            level_icon = level_colors.get(log["level"], "⚪")
            
            if log_format == "Detailed":
                st.markdown(f"""
                <div class="{log['level'].lower()}-log">
                    <strong>{level_icon} {log['timestamp']} [{log['source']}]</strong><br>
                    {log['message']}
                    {f"<br><small>{json.dumps(log['details'], indent=2)}</small>" if log['details'] else ""}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                {level_icon} `{log['timestamp']}` **{log['source']}**: {log['message']}
                """)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.header("🧠 LangGraph Workflow Visualization")
    
    # Workflow steps visualization
    if st.session_state.workflow_steps:
        st.subheader("Current Workflow Steps")
        
        # Create workflow diagram
        workflow_cols = st.columns(len(st.session_state.workflow_steps) if st.session_state.workflow_steps else 1)
        
        for i, step in enumerate(st.session_state.workflow_steps):
            with workflow_cols[i % len(workflow_cols)]:
                status_icons = {
                    "pending": "⏳",
                    "active": "🔄",
                    "completed": "✅",
                    "error": "❌"
                }
                
                icon = status_icons.get(step["status"], "❓")
                st.markdown(f"""
                <div class="workflow-step {step['status']}">
                    <h4>{icon} {step['name']}</h4>
                    <p><strong>Status:</strong> {step['status'].title()}</p>
                    <p><small>{step['timestamp']}</small></p>
                </div>
                """, unsafe_allow_html=True)
    else:
        # Add sample workflow steps
        sample_steps = [
            ("Input Analysis", "completed"),
            ("Senior Reasoning", "active"),
            ("Task Delegation", "pending"),
            ("XML Validation", "pending"),
            ("QA Review", "pending")
        ]
        
        for name, status in sample_steps:
            monitor_workflow_step(name, status)
    
    # LangGraph state visualization
    st.subheader("🔄 LangGraph State Machine")
    
    # Create a more detailed workflow diagram
    st.graphviz_chart('''
        digraph {
            rankdir=LR;
            node [shape=box, style=rounded];
            
            "User Input" [color=blue, style=filled, fillcolor=lightblue];
            "Senior Reasoning Agent" [color=green, style=filled, fillcolor=lightgreen];
            "Task Delegation" [color=orange, style=filled, fillcolor=lightyellow];
            "XML Validator" [color=purple, style=filled, fillcolor=lavender];
            "QA Specialist" [color=red, style=filled, fillcolor=lightcoral];
            "Human Review" [color=gray, style=filled, fillcolor=lightgray];
            "Final Output" [color=darkgreen, style=filled, fillcolor=palegreen];
            
            "User Input" -> "Senior Reasoning Agent" [label="analyze"];
            "Senior Reasoning Agent" -> "Task Delegation" [label="delegate"];
            "Task Delegation" -> "XML Validator" [label="validate"];
            "XML Validator" -> "QA Specialist" [label="review"];
            "QA Specialist" -> "Human Review" [label="human_needed"];
            "QA Specialist" -> "Final Output" [label="approved"];
            "Human Review" -> "Senior Reasoning Agent" [label="feedback"];
            "Human Review" -> "Final Output" [label="override"];
        }
    ''')
    
    # Real-time workflow metrics
    st.subheader("📈 Workflow Performance")
    
    col1, col2 = st.columns(2)
    with col1:
        # Step completion times (mock data)
        step_times = pd.DataFrame({
            'Step': ['Analysis', 'Reasoning', 'Delegation', 'Validation', 'QA'],
            'Time (s)': [2.3, 8.7, 3.2, 1.8, 4.5]
        })
        
        fig_times = px.bar(step_times, x='Step', y='Time (s)', 
                          title='Step Execution Times')
        st.plotly_chart(fig_times, use_container_width=True)
    
    with col2:
        # Success rate pie chart (mock data)
        success_data = pd.DataFrame({
            'Status': ['Completed', 'Failed', 'In Progress'],
            'Count': [45, 3, 2]
        })
        
        fig_success = px.pie(success_data, values='Count', names='Status',
                            title='Workflow Success Rate')
        st.plotly_chart(fig_success, use_container_width=True)

with tab4:
    st.header("🤖 Ollama Process Monitor")
    
    # Ollama status
    ollama_status = get_ollama_status()
    
    if ollama_status.get("status") == "running":
        st.success("🟢 Ollama is running")
        
        # Models information
        st.subheader("📚 Loaded Models")
        if ollama_status.get("models"):
            for model in ollama_status["models"]:
                st.info(f"🤖 {model}")
        
        # Process information
        st.subheader("⚙️ Process Information")
        if ollama_status.get("processes"):
            process_data = []
            for proc in ollama_status["processes"]:
                process_data.append({
                    "PID": proc["pid"],
                    "Name": proc["name"],
                    "CPU %": f"{proc['cpu_percent']:.1f}%",
                    "Memory %": f"{proc['memory_percent']:.1f}%"
                })
            
            if process_data:
                df_processes = pd.DataFrame(process_data)
                st.dataframe(df_processes, use_container_width=True)
        
        # Ollama API test
        st.subheader("🧪 Ollama API Test")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            test_prompt = st.text_input("Test prompt", value="Say hello in one word")
        
        with col2:
            if st.button("🚀 Test Ollama"):
                if ollama_status.get("models"):
                    try:
                        test_model = ollama_status["models"][0]
                        add_live_log("INFO", "OLLAMA_TEST", f"Testing {test_model} with prompt: {test_prompt}")
                        
                        # Mock response for now
                        st.success(f"✅ Test successful with model: {test_model}")
                        add_live_log("SUCCESS", "OLLAMA_TEST", f"Model {test_model} responded successfully")
                    except Exception as e:
                        st.error(f"❌ Test failed: {str(e)}")
                        add_live_log("ERROR", "OLLAMA_TEST", f"Test failed: {str(e)}")
                else:
                    st.warning("No models available for testing")
    
    else:
        st.error("🔴 Ollama is not running")
        st.info("💡 Start Ollama by running: `ollama serve`")
        
        if st.button("🔄 Retry Connection"):
            st.rerun()

with tab5:
    st.header("📡 API Call Monitor")
    
    # Add sample API calls for demonstration
    if len(st.session_state.api_calls) < 5:
        sample_calls = [
            ("GET", "/health", 200, "0.05s", "Health check"),
            ("GET", "/models", 200, "0.12s", "List available models"),
            ("POST", "/process-prompt", 200, "8.45s", "Process user prompt"),
            ("GET", "/session/abc123", 200, "0.03s", "Get session status"),
            ("POST", "/submit-feedback", 200, "0.08s", "Submit user feedback")
        ]
        
        for method, endpoint, status, duration, description in sample_calls:
            st.session_state.api_calls.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "duration": duration,
                "description": description
            })
    
    # API calls table
    if st.session_state.api_calls:
        df_calls = pd.DataFrame(st.session_state.api_calls)
        st.dataframe(df_calls, use_container_width=True)
        
        # API performance charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Response time distribution
            durations = [float(call["duration"].replace("s", "")) for call in st.session_state.api_calls]
            fig_duration = px.histogram(x=durations, title="Response Time Distribution")
            fig_duration.update_xaxes(title="Duration (seconds)")
            st.plotly_chart(fig_duration, use_container_width=True)
        
        with col2:
            # Status code distribution
            status_counts = {}
            for call in st.session_state.api_calls:
                status = call["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig_status = px.pie(values=list(status_counts.values()), 
                               names=list(status_counts.keys()),
                               title="Status Code Distribution")
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("No API calls recorded yet")

with tab6:
    st.header("🧪 Live Prompt Testing")
    
    # Prompt testing interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📝 Test Prompt")
        test_prompt = st.text_area(
            "Enter test prompt",
            height=150,
            placeholder="Enter your test prompt here...",
            label_visibility="collapsed"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            selected_model = st.selectbox(
                "Model",
                ollama_status.get("models", ["No models available"])
            )
            
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            max_tokens = st.number_input("Max Tokens", 1, 4000, 1000)
            
            debug_mode = st.checkbox("🔍 Debug Mode", value=True)
    
    with col2:
        st.subheader("🚀 Actions")
        
        if st.button("🧪 Test Prompt", type="primary", use_container_width=True):
            if test_prompt.strip():
                # Add to live logs
                add_live_log("INFO", "PROMPT_TEST", f"Testing prompt with {selected_model}")
                
                # Mock processing
                monitor_workflow_step("Prompt Analysis", "active")
                time.sleep(0.5)
                monitor_workflow_step("Prompt Analysis", "completed")
                monitor_workflow_step("Model Processing", "active")
                
                st.success("✅ Prompt test initiated!")
                add_live_log("SUCCESS", "PROMPT_TEST", "Test completed successfully")
            else:
                st.warning("Please enter a test prompt")
        
        if st.button("🔄 Reset Workflow", use_container_width=True):
            st.session_state.workflow_steps = []
            st.rerun()
        
        if st.button("📊 Export Debug Data", use_container_width=True):
            debug_data = {
                "logs": st.session_state.live_logs,
                "api_calls": st.session_state.api_calls,
                "workflow_steps": st.session_state.workflow_steps,
                "timestamp": datetime.now().isoformat()
            }
            
            st.download_button(
                "💾 Download Debug Data",
                data=json.dumps(debug_data, indent=2),
                file_name=f"debug_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Live results section
    st.subheader("📋 Live Results")
    
    if st.session_state.workflow_steps:
        # Show current workflow state
        current_step = next((step for step in st.session_state.workflow_steps if step["status"] == "active"), None)
        
        if current_step:
            st.info(f"🔄 Currently processing: {current_step['name']}")
        
        # Show completed steps
        completed_steps = [step for step in st.session_state.workflow_steps if step["status"] == "completed"]
        if completed_steps:
            st.success(f"✅ Completed {len(completed_steps)} steps")
    
    # Real-time metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔗 Total Logs", len(st.session_state.live_logs))
    
    with col2:
        st.metric("📡 API Calls", len(st.session_state.api_calls))
    
    with col3:
        st.metric("🔄 Workflow Steps", len(st.session_state.workflow_steps))

# Auto-refresh mechanism
if st.session_state.auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🔧 **Debug Dashboard** - Real-time monitoring of Multi-Agent Prompt Engine")
