from typing import Dict, Any, List, Optional
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
import pandas as pd
from src.utils.visualization import workflow_visualizer, data_visualizer


class DataExporter:
    """Export functionality for reports and data."""
    
    def __init__(self):
        pass
    
    def export_session_data(self, session_data: Dict[str, Any], format: str = "json") -> bytes:
        """Export session data in the specified format."""
        if format.lower() == "json":
            return self._export_json(session_data)
        elif format.lower() == "csv":
            return self._export_csv(session_data)
        elif format.lower() == "xml":
            return self._export_xml(session_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, data: Dict[str, Any]) -> bytes:
        """Export data as JSON."""
        json_str = json.dumps(data, indent=2, default=str)
        return json_str.encode('utf-8')
    
    def _export_csv(self, data: Dict[str, Any]) -> bytes:
        """Export data as CSV."""
        # Flatten the data structure for CSV export
        flattened_data = self._flatten_data(data)
        
        # Convert to DataFrame
        df = pd.DataFrame([flattened_data])
        
        # Convert to CSV
        csv_str = df.to_csv(index=False)
        return csv_str.encode('utf-8')
    
    def _export_xml(self, data: Dict[str, Any]) -> bytes:
        """Export data as XML."""
        root = ET.Element("session_data")
        self._dict_to_xml(data, root)
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str.encode('utf-8')
    
    def _dict_to_xml(self, data: Dict[str, Any], parent: ET.Element) -> None:
        """Convert dictionary to XML elements."""
        for key, value in data.items():
            # Sanitize key name for XML
            safe_key = "".join(c if c.isalnum() else "_" for c in key)
            
            if isinstance(value, dict):
                child = ET.SubElement(parent, safe_key)
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                child = ET.SubElement(parent, safe_key)
                for item in value:
                    if isinstance(item, dict):
                        item_element = ET.SubElement(child, "item")
                        self._dict_to_xml(item, item_element)
                    else:
                        item_element = ET.SubElement(child, "item")
                        item_element.text = str(item)
            else:
                child = ET.SubElement(parent, safe_key)
                child.text = str(value)
    
    def _flatten_data(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary structure."""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_data(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def export_logs(self, logs: List[Dict[str, Any]], format: str = "csv") -> bytes:
        """Export logs in the specified format."""
        if format.lower() == "json":
            return self._export_logs_json(logs)
        elif format.lower() == "csv":
            return self._export_logs_csv(logs)
        elif format.lower() == "xml":
            return self._export_logs_xml(logs)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_logs_json(self, logs: List[Dict[str, Any]]) -> bytes:
        """Export logs as JSON."""
        json_str = json.dumps(logs, indent=2, default=str)
        return json_str.encode('utf-8')
    
    def _export_logs_csv(self, logs: List[Dict[str, Any]]) -> bytes:
        """Export logs as CSV."""
        # Convert to DataFrame
        df = pd.DataFrame(logs)
        
        # Convert to CSV
        csv_str = df.to_csv(index=False)
        return csv_str.encode('utf-8')
    
    def _export_logs_xml(self, logs: List[Dict[str, Any]]) -> bytes:
        """Export logs as XML."""
        root = ET.Element("logs")
        for i, log in enumerate(logs):
            log_element = ET.SubElement(root, "log", id=str(i))
            self._dict_to_xml(log, log_element)
        xml_str = ET.tostring(root, encoding='unicode')
        return xml_str.encode('utf-8')
    
    def export_performance_report(self, report: Dict[str, Any], format: str = "json") -> bytes:
        """Export performance report in the specified format."""
        if format.lower() == "json":
            return self._export_json(report)
        elif format.lower() == "csv":
            return self._export_performance_csv(report)
        elif format.lower() == "xml":
            return self._export_xml(report)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_performance_csv(self, report: Dict[str, Any]) -> bytes:
        """Export performance report as CSV."""
        # Extract key metrics for CSV export
        summary = report.get("summary", {})
        csv_data = []
        
        # Add summary metrics
        csv_data.append({"metric": "Total Executions", "value": summary.get("total_executions", 0)})
        csv_data.append({"metric": "Average Execution Time", "value": summary.get("avg_execution_time", 0)})
        csv_data.append({"metric": "Total Input Processed", "value": summary.get("total_input_processed", 0)})
        csv_data.append({"metric": "Total Output Generated", "value": summary.get("total_output_generated", 0)})
        csv_data.append({"metric": "Peak CPU Usage", "value": summary.get("peak_cpu_usage", 0)})
        csv_data.append({"metric": "Peak Memory Usage", "value": summary.get("peak_memory_usage", 0)})
        
        # Add agent performance metrics
        for agent_name, perf_data in summary.get("agent_performance", {}).items():
            csv_data.append({"metric": f"{agent_name} Executions", "value": perf_data.get("executions", 0)})
            csv_data.append({"metric": f"{agent_name} Avg Time", "value": perf_data.get("avg_execution_time", 0)})
            csv_data.append({"metric": f"{agent_name} Avg Throughput", "value": perf_data.get("avg_throughput", 0)})
        
        # Convert to DataFrame and then to CSV
        df = pd.DataFrame(csv_data)
        csv_str = df.to_csv(index=False)
        return csv_str.encode('utf-8')
    
    def export_visualization_data(self, data: Dict[str, Any], format: str = "json") -> bytes:
        """Export visualization data."""
        # For now, we'll just export as JSON
        # In a real implementation, you might export plot images or other formats
        return self._export_json(data)
    
    def generate_export_filename(self, data_type: str, format: str) -> str:
        """Generate a filename for exported data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{data_type}_{timestamp}.{format.lower()}"


class ReportGenerator:
    """Generate comprehensive reports from system data."""
    
    def __init__(self, data_exporter: DataExporter):
        self.data_exporter = data_exporter
    
    def generate_session_report(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive report for a session."""
        report = {
            "report_type": "session_report",
            "generated_at": datetime.now().isoformat(),
            "session_id": session_data.get("session_id", "unknown"),
            "status": session_data.get("status", "unknown"),
            "summary": {
                "total_logs": len(session_data.get("logs", [])),
                "result_size": len(str(session_data.get("result", {}))),
                "duration": self._calculate_session_duration(session_data)
            },
            "data": session_data
        }
        
        return report
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> float:
        """Calculate the duration of a session."""
        # This is a simplified implementation
        # In a real system, you would track start and end times
        return 0.0
    
    def generate_performance_report(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a performance report."""
        report = {
            "report_type": "performance_report",
            "generated_at": datetime.now().isoformat(),
            "data": performance_data
        }
        
        return report
    
    def generate_audit_report(self, audit_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate an audit report."""
        report = {
            "report_type": "audit_report",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_events": len(audit_logs),
                "event_types": self._count_event_types(audit_logs)
            },
            "data": audit_logs
        }
        
        return report
    
    def _count_event_types(self, audit_logs: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of each event type."""
        event_counts = {}
        for log in audit_logs:
            event_type = log.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        return event_counts


# Global instances
data_exporter = DataExporter()
report_generator = ReportGenerator(data_exporter)