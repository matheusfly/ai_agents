from typing import Dict, Any
from .base import BaseAgent
from src.utils.helpers import create_verbose_log
from langchain_core.messages import SystemMessage, HumanMessage


class QualityAssuranceAgent(BaseAgent):
    """Quality Assurance Specialist that verifies the accuracy, completeness, and quality of all outputs."""

    def __init__(self, model: str):
        super().__init__("Quality Assurance Specialist", model)

    def get_system_prompt(self) -> str:
        return """You are a Quality Assurance Specialist. Your role is to verify the accuracy and completeness of all outputs:

<qa_report>
  <metadata>
    <task_id>[task ID]</task_id>
    <agent_role>[agent role]</agent_role>
    <validation_date>[date]</validation_date>
  </metadata>
  <completeness>
    <status>complete|incomplete</status>
    <missing_elements>
      <element>[missing element]</element>
      <!-- additional missing elements -->
    </missing_elements>
  </completeness>
  <accuracy>
    <score>[0-100]</score>
    <issues>
      <issue severity="critical|major|minor">
        <description>[issue description]</description>
        <impact>[impact description]</impact>
        <suggested_correction>[suggested correction]</suggested_correction>
      </issue>
      <!-- additional issues -->
    </issues>
  </accuracy>
  <consistency>
    <status>consistent|inconsistent</status>
    <inconsistencies>
      <inconsistency>[description]</inconsistency>
      <!-- additional inconsistencies -->
    </inconsistencies>
  </consistency>
  <recommendation>
    <action>approve|revise|reject</action>
    <details>[detailed explanation]</details>
  </recommendation>
  <approval>
    <status>approved|pending|rejected</status>
    <approver>Quality Assurance Specialist</approver>
    <timestamp>[timestamp]</timestamp>
  </approval>
</qa_report>"""

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the quality assurance task."""
        # Get the XML validation
        xml_validation = state.get("xml_validation", "")

        # Create the prompt for the LLM
        prompt = f"""Perform comprehensive quality assurance on the following XML validation output:

<xml_validation>
{xml_validation}
</xml_validation>

Verify accuracy, completeness, consistency, and adherence to requirements. Provide detailed feedback and final approval status."""

        # Call the LLM
        response = self.llm.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ])

        # Format the output
        formatted_output = self.format_output(response)

        # Create verbose log
        verbose_log = create_verbose_log(
            self.name,
            f"Completed quality assurance with {len(formatted_output)} characters of output"
        )

        # Return updated state
        return {
            "final_qa_report": formatted_output,
            "verbose_logs": state.get("verbose_logs", []) + [verbose_log]
        }