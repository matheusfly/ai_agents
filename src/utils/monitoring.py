from typing import Dict, Any, List, Optional
import time
import psutil
import json
import os
from datetime import datetime
from src.utils.ollama_client import ollama_monitor


class PerformanceMonitor:
    """Performance monitoring and analytics for the multi-agent system."""
    
    def __init__(self, log_path: str = "./performance_logs"):
        self.log_path = log_path
        os.makedirs(log_path, exist_ok=True)
        self.metrics_history = []
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level performance metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available = memory.available
        memory_total = memory.total
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "percent": memory_percent,
                "available": memory_available,
                "total": memory_total
            },
            "disk": {
                "percent": disk_percent,
                "used": disk.used,
                "total": disk.total
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }
        }
    
    def collect_ollama_metrics(self) -> Dict[str, Any]:
        """Collect Ollama-specific metrics."""
        try:
            # Get model info
            models = ollama_monitor.client.list_models()
            
            # Get resource usage
            resource_usage = ollama_monitor.monitor_resource_usage()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "active_models": len(models),
                "models": [model["name"] for model in models],
                "resource_usage": resource_usage
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def collect_agent_metrics(self, agent_name: str, execution_time: float, 
                            input_size: int, output_size: int) -> Dict[str, Any]:
        """Collect metrics for a specific agent execution."""
        return {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "execution_time": execution_time,
            "input_size": input_size,
            "output_size": output_size,
            "throughput": output_size / execution_time if execution_time > 0 else 0
        }
    
    def log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics to file."""
        self.metrics_history.append(metrics)
        
        # Write to log file
        log_file = os.path.join(self.log_path, f"metrics_{datetime.now().strftime('%Y-%m-%d')}.json")
        
        # Read existing entries
        entries = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    entries = json.load(f)
            except:
                entries = []
        
        # Add new entry
        entries.append(metrics)
        
        # Write back to file
        with open(log_file, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def get_metrics_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get metrics history for the specified number of days."""
        history = []
        
        # Get files for the last N days
        for i in range(days):
            date = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.log_path, f"metrics_{date}.json")
            
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        entries = json.load(f)
                        history.extend(entries)
                except:
                    pass
            
            # Move to previous day
            datetime.now().replace(day=datetime.now().day - 1)
        
        return history
    
    def calculate_performance_summary(self, metrics_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance summary from metrics history."""
        if not metrics_history:
            return {}
        
        # Initialize summary data
        summary = {
            "total_executions": len(metrics_history),
            "avg_execution_time": 0,
            "total_input_processed": 0,
            "total_output_generated": 0,
            "peak_cpu_usage": 0,
            "peak_memory_usage": 0,
            "agent_performance": {}
        }
        
        total_execution_time = 0
        total_input_size = 0
        total_output_size = 0
        peak_cpu = 0
        peak_memory = 0
        
        # Process metrics
        for metric in metrics_history:
            if "agent_name" in metric:
                # Agent-specific metrics
                agent_name = metric["agent_name"]
                if agent_name not in summary["agent_performance"]:
                    summary["agent_performance"][agent_name] = {
                        "executions": 0,
                        "total_time": 0,
                        "total_input": 0,
                        "total_output": 0
                    }
                
                summary["agent_performance"][agent_name]["executions"] += 1
                summary["agent_performance"][agent_name]["total_time"] += metric.get("execution_time", 0)
                summary["agent_performance"][agent_name]["total_input"] += metric.get("input_size", 0)
                summary["agent_performance"][agent_name]["total_output"] += metric.get("output_size", 0)
                
                total_execution_time += metric.get("execution_time", 0)
                total_input_size += metric.get("input_size", 0)
                total_output_size += metric.get("output_size", 0)
            
            elif "cpu" in metric:
                # System metrics
                cpu_percent = metric["cpu"].get("percent", 0)
                memory_percent = metric["memory"].get("percent", 0)
                
                peak_cpu = max(peak_cpu, cpu_percent)
                peak_memory = max(peak_memory, memory_percent)
        
        # Calculate averages
        if len(metrics_history) > 0:
            summary["avg_execution_time"] = total_execution_time / len(metrics_history)
            summary["total_input_processed"] = total_input_size
            summary["total_output_generated"] = total_output_size
            summary["peak_cpu_usage"] = peak_cpu
            summary["peak_memory_usage"] = peak_memory
        
        # Calculate agent averages
        for agent_name, perf_data in summary["agent_performance"].items():
            if perf_data["executions"] > 0:
                perf_data["avg_execution_time"] = perf_data["total_time"] / perf_data["executions"]
                perf_data["avg_throughput"] = perf_data["total_output"] / perf_data["total_time"] if perf_data["total_time"] > 0 else 0
        
        return summary


class AnalyticsEngine:
    """Analytics engine for generating insights from performance data."""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
    
    def identify_bottlenecks(self, metrics_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Calculate average execution times by agent
        agent_times = {}
        for metric in metrics_history:
            if "agent_name" in metric:
                agent_name = metric["agent_name"]
                execution_time = metric.get("execution_time", 0)
                
                if agent_name not in agent_times:
                    agent_times[agent_name] = []
                agent_times[agent_name].append(execution_time)
        
        # Identify slow agents
        for agent_name, times in agent_times.items():
            if times:
                avg_time = sum(times) / len(times)
                # If average time is more than 2 standard deviations above the mean, flag as bottleneck
                if len(times) > 1:
                    import statistics
                    std_dev = statistics.stdev(times)
                    if avg_time > (sum(times) / len(times)) + (2 * std_dev):
                        bottlenecks.append({
                            "type": "slow_agent",
                            "agent": agent_name,
                            "avg_time": avg_time,
                            "std_dev": std_dev,
                            "recommendation": f"Consider optimizing {agent_name} or using a more powerful model"
                        })
        
        return bottlenecks
    
    def generate_recommendations(self, performance_summary: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on performance data."""
        recommendations = []
        
        # CPU usage recommendations
        if performance_summary.get("peak_cpu_usage", 0) > 80:
            recommendations.append("High CPU usage detected. Consider adding more CPU cores or optimizing agent implementations.")
        
        # Memory usage recommendations
        if performance_summary.get("peak_memory_usage", 0) > 80:
            recommendations.append("High memory usage detected. Consider optimizing memory usage or adding more RAM.")
        
        # Agent performance recommendations
        for agent_name, perf_data in performance_summary.get("agent_performance", {}).items():
            if perf_data.get("avg_execution_time", 0) > 10:  # More than 10 seconds
                recommendations.append(f"{agent_name} has slow execution times. Consider using a more powerful model or optimizing the prompt.")
            
            if perf_data.get("avg_throughput", 0) < 100:  # Less than 100 chars/second
                recommendations.append(f"{agent_name} has low throughput. Consider optimizing the agent implementation.")
        
        # General recommendations
        if performance_summary.get("total_executions", 0) > 1000:
            recommendations.append("High volume of executions detected. Consider implementing caching for common requests.")
        
        return recommendations
    
    def create_performance_report(self) -> Dict[str, Any]:
        """Create a comprehensive performance report."""
        # Get metrics history
        metrics_history = self.performance_monitor.get_metrics_history()
        
        # Calculate summary
        performance_summary = self.performance_monitor.calculate_performance_summary(metrics_history)
        
        # Identify bottlenecks
        bottlenecks = self.identify_bottlenecks(metrics_history)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(performance_summary)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": performance_summary,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "total_metrics": len(metrics_history)
        }


# Global instances
performance_monitor = PerformanceMonitor()
analytics_engine = AnalyticsEngine(performance_monitor)