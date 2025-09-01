from typing import Dict, Any
from .base import BaseAgent
from src.utils import create_verbose_log, validate_xml_structure
import xml.etree.ElementTree as ET


class XMLFormatterAgent(BaseAgent):
    """XML Formatter & Validator that ensures all inputs and outputs follow strict XML formatting standards."""
    
    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        super().__init__("XML Formatter & Validator", model, base_url)
    
    def get_system_prompt(self) -> str:
        return """You are an XML Formatter & Validator. Your role is to validate and format all inputs and outputs using XML:

<validation>
  <input>[original input]</input>
  <schema_validation>
    <status>valid|invalid</status>
    <issues>
      <issue line="[line number]" severity="error|warning">
        <description>[issue description]</description>
        <suggested_fix>[suggested fix]</suggested_fix>
      </issue>
      <!-- additional issues -->
    </issues>
  </schema_validation>
  <formatting>
    <status>formatted|needs_formatting</status>
    <formatted_output>
      [properly formatted XML output]
    </formatted_output>
  </formatting>
  <compliance>
    <standard>XML 1.0</standard>
    <compliance_level>strict|lenient</compliance_level>
    <issues_resolved>[number]</issues_resolved>
  </compliance>
</validation>

Always provide the corrected XML if issues are found."""
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the XML validation task."""
        # Get the task delegation
        task_delegation = state.get("task_delegation", "")
        
        # Create the prompt for the LLM
        prompt = f"""Validate and format the following task delegation plan according to XML standards:

<task_delegation>
{task_delegation}
</task_delegation>

Check for proper nesting, correct tag usage, attribute completeness, and data type consistency. Provide corrected XML if issues are found."""

        # Call the LLM
        response = self.call_llm(prompt, self.get_system_prompt())
        
        # Format the output
        formatted_output = self.format_output(response)
        
        # Create verbose log
        verbose_log = create_verbose_log(
            self.name, 
            f"Completed XML validation with {len(formatted_output)} characters of output"
        )
        
        # Return updated state
        return {
            "xml_validation": formatted_output,
            "verbose_logs": state.get("verbose_logs", []) + [verbose_log]
        }