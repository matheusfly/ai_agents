from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from xml.dom import minidom


def format_xml(xml_string: str) -> str:
    """Format XML string with proper indentation."""
    try:
        root = ET.fromstring(xml_string)
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    except ET.ParseError:
        return xml_string


def validate_xml_structure(xml_string: str, required_elements: List[str]) -> Dict[str, Any]:
    """Validate XML structure contains required elements."""
    result = {
        "valid": True,
        "missing_elements": [],
        "errors": []
    }
    
    try:
        root = ET.fromstring(xml_string)
        
        for element in required_elements:
            if root.find(element) is None:
                result["missing_elements"].append(element)
                result["valid"] = False
                
    except ET.ParseError as e:
        result["valid"] = False
        result["errors"].append(f"XML Parse Error: {str(e)}")
    
    return result


def create_verbose_log(agent_name: str, message: str, log_type: str = "info") -> Dict[str, Any]:
    """Create a structured log entry for verbose logging."""
    import datetime
    
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "agent": agent_name,
        "message": message,
        "type": log_type
    }