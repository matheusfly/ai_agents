from typing import Dict, Any, List, Optional
import re
import json
from src.utils.ollama_client import ollama_client
from src.config import settings


class PromptTuner:
    """AI-powered prompt tuning engine."""
    
    def __init__(self):
        self.tuning_history = []
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze a prompt and provide suggestions for improvement."""
        # Analyze prompt structure
        analysis = {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "sentence_count": len(prompt.split('.')),
            "question_count": prompt.count('?'),
            "exclamation_count": prompt.count('!'),
            "complexity_score": self._calculate_complexity(prompt),
            "clarity_score": self._calculate_clarity(prompt),
            "specificity_score": self._calculate_specificity(prompt)
        }
        
        return analysis
    
    def _calculate_complexity(self, prompt: str) -> float:
        """Calculate the complexity score of a prompt."""
        # Simple heuristic: longer prompts with more complex words are more complex
        words = prompt.split()
        if not words:
            return 0.0
            
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Number of clauses (simplified)
        clauses = prompt.count(',') + prompt.count(';') + prompt.count(':')
        
        # Complexity score (0-100)
        complexity = min(100, (avg_word_length * 2) + (clauses * 5))
        return complexity
    
    def _calculate_clarity(self, prompt: str) -> float:
        """Calculate the clarity score of a prompt."""
        # Simple heuristic: clearer prompts use active voice and have fewer ambiguous words
        active_voice_indicators = ['please', 'explain', 'describe', 'list', 'show', 'demonstrate']
        passive_voice_indicators = ['was done', 'has been', 'will be', 'should be']
        
        active_count = sum(1 for word in active_voice_indicators if word in prompt.lower())
        passive_count = sum(1 for word in passive_voice_indicators if word in prompt.lower())
        
        # Clarity score (0-100)
        clarity = 50 + (active_count * 10) - (passive_count * 15)
        return max(0, min(100, clarity))
    
    def _calculate_specificity(self, prompt: str) -> float:
        """Calculate the specificity score of a prompt."""
        # Simple heuristic: more specific prompts contain more concrete details
        vague_words = ['thing', 'stuff', 'good', 'bad', 'nice', 'great', 'important']
        specific_indicators = ['specifically', 'exactly', 'precisely', 'detailed', 'comprehensive']
        
        vague_count = sum(1 for word in vague_words if word in prompt.lower())
        specific_count = sum(1 for word in specific_indicators if word in prompt.lower())
        
        # Specificity score (0-100)
        specificity = 50 - (vague_count * 10) + (specific_count * 15)
        return max(0, min(100, specificity))
    
    def suggest_improvements(self, prompt: str, analysis: Optional[Dict[str, Any]] = None) -> List[str]:
        """Generate AI-powered suggestions for improving a prompt."""
        if analysis is None:
            analysis = self.analyze_prompt(prompt)
        
        suggestions = []
        
        # Length-based suggestions
        if analysis["length"] < 50:
            suggestions.append("Consider making your prompt more detailed. Short prompts may lack sufficient context.")
        elif analysis["length"] > 500:
            suggestions.append("Your prompt is quite long. Consider breaking it into smaller, more focused prompts.")
        
        # Complexity-based suggestions
        if analysis["complexity_score"] > 80:
            suggestions.append("Your prompt is quite complex. Consider simplifying the language for better understanding.")
        elif analysis["complexity_score"] < 30:
            suggestions.append("Your prompt is quite simple. Consider adding more specific details or context.")
        
        # Clarity-based suggestions
        if analysis["clarity_score"] < 50:
            suggestions.append("Improve clarity by using active voice and reducing ambiguous language.")
        
        # Specificity-based suggestions
        if analysis["specificity_score"] < 50:
            suggestions.append("Make your prompt more specific by including concrete examples or detailed requirements.")
        
        # AI-powered suggestions using LLM
        ai_suggestions = self._get_ai_suggestions(prompt)
        suggestions.extend(ai_suggestions)
        
        return suggestions
    
    def _get_ai_suggestions(self, prompt: str) -> List[str]:
        """Get AI-powered suggestions using an LLM."""
        try:
            system_prompt = """You are a prompt engineering expert. Analyze the following prompt and provide 2-3 specific suggestions for improvement. Focus on:
1. Clarity and specificity
2. Proper context and constraints
3. Expected output format
4. Any potential ambiguities

Return your suggestions as a JSON array of strings."""

            user_prompt = f"Analyze this prompt and suggest improvements:\n\n{prompt}"

            response = ollama_client.chat(
                model=settings.GEMMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Try to parse the response as JSON
            try:
                suggestions = json.loads(response['message']['content'])
                if isinstance(suggestions, list):
                    return suggestions
            except json.JSONDecodeError:
                # If JSON parsing fails, extract suggestions from plain text
                content = response['message']['content']
                # Simple extraction of bullet points or numbered lists
                lines = content.split('\n')
                suggestions = []
                for line in lines:
                    if line.strip().startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.')):
                        suggestion = re.sub(r'^[-*•\d.]+\s*', '', line.strip())
                        if suggestion:
                            suggestions.append(suggestion)
                if suggestions:
                    return suggestions[:3]  # Limit to 3 suggestions

            # Fallback to generic suggestions
            return [
                "Consider adding specific examples to clarify your requirements",
                "Define the expected output format more clearly",
                "Include any constraints or limitations that apply"
            ]
        except Exception as e:
            print(f"Error getting AI suggestions: {e}")
            return []  # Return empty list if AI suggestions fail
    
    def compare_prompts(self, prompt1: str, prompt2: str) -> Dict[str, Any]:
        """Compare two prompts and provide analysis."""
        analysis1 = self.analyze_prompt(prompt1)
        analysis2 = self.analyze_prompt(prompt2)
        
        comparison = {
            "prompt1_analysis": analysis1,
            "prompt2_analysis": analysis2,
            "improvements": {}
        }
        
        # Compare scores
        for metric in ["complexity_score", "clarity_score", "specificity_score"]:
            if metric in analysis1 and metric in analysis2:
                diff = analysis2[metric] - analysis1[metric]
                comparison["improvements"][metric] = {
                    "difference": diff,
                    "improved": diff > 0
                }
        
        return comparison
    
    def optimize_prompt(self, prompt: str, iterations: int = 3) -> Dict[str, Any]:
        """Automatically optimize a prompt through multiple iterations."""
        current_prompt = prompt
        history = [{"iteration": 0, "prompt": prompt, "analysis": self.analyze_prompt(prompt)}]
        
        for i in range(iterations):
            # Get suggestions
            suggestions = self.suggest_improvements(current_prompt, history[-1]["analysis"])
            
            # Apply suggestions (simplified - in a real implementation, this would be more sophisticated)
            improved_prompt = self._apply_suggestions(current_prompt, suggestions)
            
            # Analyze improved prompt
            analysis = self.analyze_prompt(improved_prompt)
            
            # Add to history
            history.append({
                "iteration": i + 1,
                "prompt": improved_prompt,
                "analysis": analysis,
                "suggestions": suggestions
            })
            
            current_prompt = improved_prompt
        
        return {
            "original_prompt": prompt,
            "optimized_prompt": current_prompt,
            "history": history,
            "improvement": self.compare_prompts(prompt, current_prompt)
        }
    
    def _apply_suggestions(self, prompt: str, suggestions: List[str]) -> str:
        """Apply suggestions to improve a prompt (simplified implementation)."""
        # In a real implementation, this would be more sophisticated
        # For now, we'll just return the original prompt
        return prompt


# Global instance
prompt_tuner = PromptTuner()