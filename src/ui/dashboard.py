import streamlit as st
import requests
import json
import time
from typing import Dict, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import asyncio
import aiohttp

# Configure the page
st.set_page_config(
    page_title="Multi-Agent Prompt Engine",
    page_icon="🤖",
    layout="wide"
)

# API base URL
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "processing" not in st.session_state:
    st.session_state.processing = False
if "result" not in st.session_state:
    st.session_state.result = None
if "logs" not in st.session_state:
    st.session_state.logs = []
if "sse_active" not in st.session_state:
    st.session_state.sse_active = False

# Custom CSS for styling
st.markdown("""
<style>
    .stApp {
        background-color: #f0f2f6;
    }
    .header {
        background-color: #4A90E2;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .agent-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
    }
    .log-entry {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    .info-log {
        background-color: #e3f2fd;
    }
    .warning-log {
        background-color: #fff3e0;
    }
    .error-log {
        background-color: #ffebee;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("<div class='header'>", unsafe_allow_html=True)
st.title("🤖 Multi-Agent Prompt Engine Dashboard")
st.markdown("</div>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Health Check
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health_data = response.json()
            st.success(f"API Status: {health_data['status']}")
            st.info(f"Ollama Server: {health_data['ollama_server']}")
        else:
            st.error("API Unreachable")
    except:
        st.error("API Unreachable")
    
    # Model Information
    st.subheader("🧠 Models")
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        if response.status_code == 200:
            models_data = response.json()
            for model in models_data["models"]:
                st.write(f"- {model['name']}")
    except:
        st.write("Unable to fetch models")
    
    # Export section
    if st.session_state.session_id and st.session_state.result:
        st.subheader("💾 Export Data")
        export_format = st.selectbox("Export Format", ["JSON", "CSV", "XML"])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export Session"):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/export/session",
                        json={
                            "session_id": st.session_state.session_id,
                            "format": export_format.lower()
                        }
                    )
                    if response.status_code == 200:
                        st.download_button(
                            label="Download Session Data",
                            data=response.content,
                            file_name=f"session_{st.session_state.session_id}.{export_format.lower()}",
                            mime=f"application/{export_format.lower()}"
                        )
                    else:
                        st.error("Export failed")
                except Exception as e:
                    st.error(f"Export error: {str(e)}")
        
        with col2:
            if st.button("Export Logs"):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/export/logs",
                        json={
                            "session_id": st.session_state.session_id,
                            "format": export_format.lower()
                        }
                    )
                    if response.status_code == 200:
                        st.download_button(
                            label="Download Logs",
                            data=response.content,
                            file_name=f"logs_{st.session_state.session_id}.{export_format.lower()}",
                            mime=f"application/{export_format.lower()}"
                        )
                    else:
                        st.error("Export failed")
                except Exception as e:
                    st.error(f"Export error: {str(e)}")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📝 Prompt Input")
    
    # Prompt input
    prompt = st.text_area(
        "Enter your prompt:",
        height=150,
        placeholder="Describe the problem you want the multi-agent system to solve..."
    )
    
    # Process button
    if st.button("🚀 Process Prompt", disabled=st.session_state.processing):
        if prompt.strip():
            st.session_state.processing = True
            st.session_state.result = None
            st.session_state.logs = []
            st.session_state.sse_active = True
            
            try:
                # Send request to API
                response = requests.post(
                    f"{API_BASE_URL}/process-prompt",
                    json={"prompt": prompt}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.session_id = data["session_id"]
                    st.success(f"Processing started! Session ID: {st.session_state.session_id}")
                else:
                    st.error(f"Error: {response.text}")
                    st.session_state.processing = False
                    st.session_state.sse_active = False
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.processing = False
                st.session_state.sse_active = False
        else:
            st.warning("Please enter a prompt")

with col2:
    st.header("📊 System Status")
    
    # Session status
    if st.session_state.session_id:
        try:
            response = requests.get(f"{API_BASE_URL}/session/{st.session_state.session_id}")
            if response.status_code == 200:
                session_data = response.json()
                st.write(f"**Session ID:** {st.session_state.session_id}")
                st.write(f"**Status:** {session_data['status']}")
                
                # If completed, update state
                if session_data["status"] == "completed":
                    st.session_state.processing = False
                    st.session_state.result = session_data["result"]
                    st.session_state.logs = session_data["logs"]
                    st.session_state.sse_active = False
                    st.success("Processing completed!")
                elif session_data["status"] == "error":
                    st.session_state.processing = False
                    st.session_state.sse_active = False
                    st.error("Processing failed!")
        except:
            st.write("Unable to fetch session status")

# Results section
if st.session_state.result:
    st.header("📋 Results")
    
    # Tabs for different outputs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Problem Analysis", 
        "Task Delegation", 
        "XML Validation", 
        "QA Report", 
        "Final Output",
        "Visualizations"
    ])
    
    with tab1:
        st.subheader("Problem Analysis")
        analysis = st.session_state.result.get("problem_analysis", "No analysis available")
        st.text_area("Problem Analysis Content", value=analysis, height=300, key="analysis", label_visibility="collapsed")
    
    with tab2:
        st.subheader("Task Delegation")
        delegation = st.session_state.result.get("task_delegation", "No delegation plan available")
        st.text_area("Task Delegation Content", value=delegation, height=300, key="delegation", label_visibility="collapsed")
    
    with tab3:
        st.subheader("XML Validation")
        validation = st.session_state.result.get("xml_validation", "No validation report available")
        st.text_area("XML Validation Content", value=validation, height=300, key="validation", label_visibility="collapsed")
    
    with tab4:
        st.subheader("QA Report")
        qa_report = st.session_state.result.get("final_qa_report", "No QA report available")
        st.text_area("QA Report Content", value=qa_report, height=300, key="qa_report", label_visibility="collapsed")
    
    with tab5:
        st.subheader("Final Output")
        # Extract final output from QA report
        final_output = "Final output would be extracted from the QA report"
        st.text_area("Final Output Content", value=final_output, height=300, key="final_output", label_visibility="collapsed")
    
    with tab6:
        st.subheader("Workflow Visualization")
        
        # Create a simple workflow DAG visualization
        st.write("### Workflow DAG")
        # Create a simple representation using Streamlit's graphviz
        st.graphviz_chart('''
            digraph {
                "User Input" -> "Senior Reasoning Agent"
                "Senior Reasoning Agent" -> "Task Delegation Specialist"
                "Task Delegation Specialist" -> "XML Formatter & Validator"
                "XML Formatter & Validator" -> "Quality Assurance Specialist"
                "Quality Assurance Specialist" -> "Human Review"
                "Quality Assurance Specialist" -> "Final Output"
                "Human Review" -> "Final Output"
            }
        ''')
        
        # Performance timeline
        if st.session_state.logs:
            st.write("### Performance Timeline")
            # Create a simple timeline using DataFrame
            log_data = []
            for log in st.session_state.logs:
                log_data.append({
                    "Agent": log.get("agent", "Unknown"),
                    "Message": log.get("message", "")[:50] + "..." if len(log.get("message", "")) > 50 else log.get("message", ""),
                    "Timestamp": log.get("timestamp", "")
                })
            
            df = pd.DataFrame(log_data)
            st.dataframe(df)
        
        # Log level distribution
        st.write("### Log Level Distribution")
        if st.session_state.logs:
            level_counts = {}
            for log in st.session_state.logs:
                level = log.get("type", "info")
                level_counts[level] = level_counts.get(level, 0) + 1
            
            if level_counts:
                fig = px.pie(
                    values=list(level_counts.values()),
                    names=list(level_counts.keys()),
                    title="Log Level Distribution"
                )
                st.plotly_chart(fig)

# Logs section
st.header("📝 Agent Logs")
logs_container = st.empty()

# Display logs in reverse chronological order
if st.session_state.logs:
    for log in reversed(st.session_state.logs):
        log_type = log.get("type", "info")
        log_class = f"log-entry {log_type}-log"
        
        logs_container.markdown(
            f"<div class='{log_class}'>"
            f"<strong>{log.get('timestamp', 'N/A')}</strong> - "
            f"<em>{log.get('agent', 'System')}</em>: "
            f"{log.get('message', 'No message')}"
            f"</div>",
            unsafe_allow_html=True
        )

# Human feedback section
if st.session_state.session_id and not st.session_state.processing:
    st.header("👤 Human Review")
    
    feedback = st.text_area(
        "Provide feedback on the results:",
        height=100,
        placeholder="Enter your feedback here..."
    )
    
    if st.button("📤 Submit Feedback"):
        if feedback.strip():
            try:
                response = requests.post(
                    f"{API_BASE_URL}/submit-feedback",
                    json={
                        "session_id": st.session_state.session_id,
                        "feedback": feedback
                    }
                )
                
                if response.status_code == 200:
                    st.success("Feedback submitted successfully!")
                else:
                    st.error(f"Error submitting feedback: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter feedback before submitting")

# SSE connection for real-time updates
if st.session_state.sse_active and st.session_state.session_id:
    # This is a simplified approach using periodic polling
    # In a real implementation, you would use JavaScript to handle SSE
    time.sleep(2)
    try:
        response = requests.get(f"{API_BASE_URL}/session/{st.session_state.session_id}")
        if response.status_code == 200:
            session_data = response.json()
            st.session_state.logs = session_data["logs"]
            
            # Check if processing is complete
            if session_data["status"] in ["completed", "error", "feedback_received"]:
                st.session_state.processing = False
                st.session_state.result = session_data["result"]
                st.session_state.sse_active = False
    except:
        pass
    
    # Rerun to update the UI
    st.rerun()