from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import json


class WorkflowVisualizer:
    """Advanced visualization for workflow monitoring and analysis."""
    
    def __init__(self):
        self.visualization_data = []
    
    def create_workflow_dag(self, workflow_data: Dict[str, Any]) -> go.Figure:
        """Create an interactive DAG visualization of the workflow."""
        # Create nodes for each agent
        nodes = [
            "User Input",
            "Senior Reasoning Agent",
            "Task Delegation Specialist",
            "XML Formatter & Validator",
            "Quality Assurance Specialist",
            "Human Review",
            "Final Output"
        ]
        
        # Create edges
        edges = [
            ("User Input", "Senior Reasoning Agent"),
            ("Senior Reasoning Agent", "Task Delegation Specialist"),
            ("Task Delegation Specialist", "XML Formatter & Validator"),
            ("XML Formatter & Validator", "Quality Assurance Specialist"),
            ("Quality Assurance Specialist", "Human Review"),
            ("Quality Assurance Specialist", "Final Output"),
            ("Human Review", "Final Output")
        ]
        
        # Create node positions
        positions = {
            "User Input": (0, 0),
            "Senior Reasoning Agent": (1, 1),
            "Task Delegation Specialist": (2, 1),
            "XML Formatter & Validator": (3, 1),
            "Quality Assurance Specialist": (4, 1),
            "Human Review": (5, 0),
            "Final Output": (6, 1)
        }
        
        # Create figure
        fig = go.Figure()
        
        # Add edges
        for edge in edges:
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            fig.add_trace(go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(width=2, color='blue'),
                showlegend=False
            ))
        
        # Add nodes
        node_x = [positions[node][0] for node in nodes]
        node_y = [positions[node][1] for node in nodes]
        
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(size=20, color='lightblue', line=dict(width=2, color='darkblue')),
            text=nodes,
            textposition="middle center",
            showlegend=False
        ))
        
        fig.update_layout(
            title="Multi-Agent Workflow DAG",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400
        )
        
        return fig
    
    def create_performance_timeline(self, logs: List[Dict[str, Any]]) -> go.Figure:
        """Create a timeline visualization of agent performance."""
        # Extract timing data from logs
        timeline_data = []
        for log in logs:
            if "timestamp" in log and "agent" in log:
                timeline_data.append({
                    "timestamp": log["timestamp"],
                    "agent": log["agent"],
                    "message": log["message"][:50] + "..." if len(log["message"]) > 50 else log["message"]
                })
        
        if not timeline_data:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="Performance Timeline")
            return fig
        
        # Create DataFrame
        df = pd.DataFrame(timeline_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")
        
        # Create figure
        fig = px.timeline(
            df, 
            x_start="timestamp", 
            x_end="timestamp", 
            y="agent", 
            color="agent",
            title="Agent Performance Timeline"
        )
        
        fig.update_layout(height=400)
        return fig
    
    def create_agent_activity_heatmap(self, logs: List[Dict[str, Any]]) -> go.Figure:
        """Create a heatmap of agent activity."""
        # Group logs by agent and time
        activity_data = {}
        for log in logs:
            if "agent" in log and "timestamp" in log:
                agent = log["agent"]
                timestamp = pd.to_datetime(log["timestamp"])
                hour = timestamp.hour
                
                if agent not in activity_data:
                    activity_data[agent] = [0] * 24
                
                activity_data[agent][hour] += 1
        
        if not activity_data:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="Agent Activity Heatmap")
            return fig
        
        # Create DataFrame
        df = pd.DataFrame(activity_data)
        df.index = [f"{i:02d}:00" for i in range(24)]
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=df.values.T,
            x=df.index,
            y=df.columns,
            colorscale='Blues'
        ))
        
        fig.update_layout(
            title="Agent Activity Heatmap",
            xaxis_title="Hour of Day",
            yaxis_title="Agent",
            height=400
        )
        
        return fig
    
    def create_resource_usage_chart(self, monitoring_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a chart showing resource usage over time."""
        if not monitoring_data:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="Resource Usage")
            return fig
        
        # Create DataFrame
        df = pd.DataFrame(monitoring_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Create figure with multiple traces
        fig = go.Figure()
        
        # Add CPU usage trace
        if "cpu_percent" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["cpu_percent"],
                mode='lines',
                name='CPU %'
            ))
        
        # Add memory usage trace
        if "memory_percent" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["timestamp"],
                y=df["memory_percent"],
                mode='lines',
                name='Memory %'
            ))
        
        fig.update_layout(
            title="Resource Usage Over Time",
            xaxis_title="Time",
            yaxis_title="Usage %",
            height=400
        )
        
        return fig
    
    def create_log_level_distribution(self, logs: List[Dict[str, Any]]) -> go.Figure:
        """Create a pie chart showing log level distribution."""
        # Count log levels
        level_counts = {}
        for log in logs:
            level = log.get("type", "info")
            level_counts[level] = level_counts.get(level, 0) + 1
        
        if not level_counts:
            # Return empty figure if no data
            fig = go.Figure()
            fig.update_layout(title="Log Level Distribution")
            return fig
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(level_counts.keys()),
            values=list(level_counts.values())
        )])
        
        fig.update_layout(title="Log Level Distribution")
        return fig


class DataVisualizer:
    """Visualization for data analysis and reporting."""
    
    def __init__(self):
        pass
    
    def create_prompt_analysis_chart(self, prompt_analysis: Dict[str, Any]) -> go.Figure:
        """Create a chart analyzing prompt quality."""
        # Extract metrics
        metrics = ["complexity_score", "clarity_score", "specificity_score"]
        values = [
            prompt_analysis.get("complexity_score", 0),
            prompt_analysis.get("clarity_score", 0),
            prompt_analysis.get("specificity_score", 0)
        ]
        
        # Create radar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name='Prompt Analysis'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Prompt Quality Analysis",
            height=400
        )
        
        return fig
    
    def create_performance_comparison_chart(self, comparison_data: List[Dict[str, Any]]) -> go.Figure:
        """Create a chart comparing performance metrics."""
        # Extract data
        models = [item["model"] for item in comparison_data]
        response_times = [item["avg_response_time"] for item in comparison_data]
        accuracy_scores = [item["accuracy_score"] for item in comparison_data]
        
        # Create figure with subplots
        fig = go.Figure()
        
        # Add response time bars
        fig.add_trace(go.Bar(
            x=models,
            y=response_times,
            name='Avg Response Time (ms)',
            yaxis='y',
            offsetgroup=1
        ))
        
        # Add accuracy scores
        fig.add_trace(go.Scatter(
            x=models,
            y=accuracy_scores,
            mode='lines+markers',
            name='Accuracy Score',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="Model Performance Comparison",
            yaxis=dict(title="Response Time (ms)"),
            yaxis2=dict(title="Accuracy Score", overlaying='y', side='right'),
            height=400
        )
        
        return fig


# Global instances
workflow_visualizer = WorkflowVisualizer()
data_visualizer = DataVisualizer()