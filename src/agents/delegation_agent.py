from typing import Dict, Any
from .base import BaseAgent
from src.utils.helpers import create_verbose_log
from langchain_core.messages import SystemMessage, HumanMessage


class TaskDelegationAgent(BaseAgent):
    """Task Delegation Specialist that creates detailed XML-formatted task delegation plans."""

    def __init__(self, model: str):
        super().__init__("Task Delegation Specialist", model)

    def get_system_prompt(self) -> str:
        return """You are a Task Delegation Specialist. Your role is to create XML-formatted task delegation plans:

<delegation>
  <task id="[id]" priority="[high|medium|low]" dependencies="[comma-separated task IDs]">
    <title>[task title]</title>
    <description>[detailed task description]</description>
    <agent role="[agent role]" model="[model]" capability="[specific capability]" />
    <input_requirements>
      <requirement>[required input]</requirement>
      <!-- additional requirements -->
    </input_requirements>
    <output_specification>
      <format>XML</format>
      <structure>[expected structure]</structure>
      <validation_rules>
        <rule>[validation rule]</rule>
        <!-- additional rules -->
      </validation_rules>
    </output_specification>
    <time_estimation>[estimated time]</time_estimation>
  </task>
</delegation>

Ensure all tasks are properly sequenced and dependencies are correctly identified."""

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the task delegation task."""
        # Get the problem analysis
        problem_analysis = state.get("problem_analysis", "")

        # Create the prompt for the LLM
        prompt = f"""Based on the following problem analysis, create a detailed task delegation plan with XML formatting:

<problem_analysis>
{problem_analysis}
</problem_analysis>

Assign specific subtasks to appropriate agents based on complexity, domain expertise, and model capabilities. Define clear input requirements, output specifications, validation rules, and dependencies for each task."""

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
            f"Completed task delegation with {len(formatted_output)} characters of output"
        )

        # Return updated state
        return {
            "task_delegation": formatted_output,
            "verbose_logs": state.get("verbose_logs", []) + [verbose_log]
        }