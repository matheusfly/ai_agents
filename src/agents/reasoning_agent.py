from typing import Dict, Any
from .base import BaseAgent
from src.utils.helpers import create_verbose_log
from langchain_core.messages import SystemMessage, HumanMessage


class SeniorReasoningAgent(BaseAgent):
    """Senior Reasoning Agent that breaks down complex problems into step-by-step reasoning processes."""

    def __init__(self, model: str):
        super().__init__("Senior Reasoning Agent", model)

    def get_system_prompt(self) -> str:
        return """You are a Senior Reasoning Agent. Your role is to break down complex problems into step-by-step reasoning processes. Always use XML tags for structured output:

- For reasoning steps: <reasoning>
  <step id="[number]" type="[analysis|calculation|inference]">
    <description>[step description]</description>
    <input>[input variables]</input>
    <output>[expected output]</output>
  </step>
</reasoning>

- For variables: <variables>
  <var name="[name]" type="[string|number|boolean|object]" required="true|false">
    <description>[variable description]</description>
    <format>[format requirements]</format>
    <example>[example value]</example>
  </var>
</variables>

- For conclusions: <conclusion>
  <summary>[summary of reasoning]</summary>
  <next_steps>[recommended next steps]</next_steps>
</conclusion>

Ensure all XML is properly nested and validated."""

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the problem analysis task."""
        # Get the user input
        user_input = state.get("messages", [""])[-1] if state.get("messages") else ""

        # Create the prompt for the LLM
        prompt = f"""Analyze the following problem in detail and break it down into explicit step-by-step reasoning processes:

{user_input}

Provide a comprehensive reasoning structure with input requirements and expected outputs for each step. Use the XML format specified in your system prompt."""

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
            f"Completed problem analysis with {len(formatted_output)} characters of output"
        )

        # Return updated state
        return {
            "problem_analysis": formatted_output,
            "verbose_logs": state.get("verbose_logs", []) + [verbose_log]
        }