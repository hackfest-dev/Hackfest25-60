import json
from typing import Dict, Any, List, Optional, Tuple

from crew_ai.agents.base_agent import BaseAgent
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.utils.messaging import MessageBroker
from crew_ai.config.config import Config, LLMProvider

class ValidatorAgent(BaseAgent):
    """Agent for validating LLM-generated outputs."""
    
    def __init__(self, agent_id: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None):
        """Initialize the ValidatorAgent."""
        super().__init__(agent_id, llm_client, llm_provider, message_broker)
        
        # Register message handlers
        self.register_handler("validate_answer", self._handle_validate_answer)
        self.register_handler("validate_report", self._handle_validate_report)
    
    def _handle_validate_answer(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle validate_answer messages."""
        query = message.get("data", {}).get("query")
        answer = message.get("data", {}).get("answer")
        context = message.get("data", {}).get("context", [])
        
        if not query or not answer:
            return {"status": "error", "error": "Query and answer are required"}
        
        validation_result = self.validate_answer(query, answer, context)
        
        return {
            "status": "success",
            "validation_result": validation_result
        }
    
    def _handle_validate_report(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle validate_report messages."""
        report_sections = message.get("data", {}).get("report_sections", {})
        
        if not report_sections:
            return {"status": "error", "error": "Report sections are required"}
        
        validation_result = self.validate_report(report_sections)
        
        return {
            "status": "success",
            "validation_result": validation_result
        }
    
    def validate_answer(self, query: str, answer: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate an answer based on the query and context."""
        print(f"Validating answer for query: {query}")
        
        # Format context for LLM
        formatted_context = self._format_context_for_llm(context)
        
        prompt = f"""
        Validate the following answer to a query based on the provided context. 
        Assess the answer for:
        1. Factual accuracy: Does the answer align with the facts in the context?
        2. Relevance: Does the answer address the query?
        3. Completeness: Does the answer cover all relevant aspects of the query?
        4. Clarity: Is the answer clear and well-structured?
        
        If there are issues with the answer, provide a corrected version.
        
        Query: {query}
        
        Answer: {answer}
        
        Context:
        {formatted_context}
        
        Return your assessment as a JSON object with the following structure:
        {{
            "is_valid": true/false,
            "scores": {{
                "factual_accuracy": 0-10,
                "relevance": 0-10,
                "completeness": 0-10,
                "clarity": 0-10
            }},
            "issues": ["issue1", "issue2", ...],
            "corrected_answer": "corrected answer if needed"
        }}
        """
        
        system_prompt = """
        You are a validation system for LLM-generated answers. Your task is to assess answers
        for factual accuracy, relevance, completeness, and clarity based on the provided context.
        Return your assessment as a JSON object with the specified structure.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        try:
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            validation_result = json.loads(response)
            
            # Ensure the result has the expected structure
            if not isinstance(validation_result, dict):
                validation_result = {
                    "is_valid": False,
                    "scores": {
                        "factual_accuracy": 0,
                        "relevance": 0,
                        "completeness": 0,
                        "clarity": 0
                    },
                    "issues": ["Failed to parse validation result"],
                    "corrected_answer": answer
                }
            
            # Ensure all required fields are present
            if "is_valid" not in validation_result:
                validation_result["is_valid"] = False
            
            if "scores" not in validation_result:
                validation_result["scores"] = {
                    "factual_accuracy": 0,
                    "relevance": 0,
                    "completeness": 0,
                    "clarity": 0
                }
            
            if "issues" not in validation_result:
                validation_result["issues"] = []
            
            if "corrected_answer" not in validation_result:
                validation_result["corrected_answer"] = answer
            
            return validation_result
        
        except Exception as e:
            print(f"Error parsing validation result: {e}")
            return {
                "is_valid": False,
                "scores": {
                    "factual_accuracy": 0,
                    "relevance": 0,
                    "completeness": 0,
                    "clarity": 0
                },
                "issues": [f"Error parsing validation result: {str(e)}"],
                "corrected_answer": answer
            }
    
    def validate_report(self, report_sections: Dict[str, str]) -> Dict[str, Any]:
        """Validate a report based on its sections."""
        print("Validating report...")
        
        validation_results = {}
        
        # Validate each section
        for section_name, section_content in report_sections.items():
            validation_results[section_name] = self._validate_report_section(section_name, section_content)
        
        # Calculate overall validation result
        is_valid = all(result["is_valid"] for result in validation_results.values())
        
        # Calculate average scores
        avg_scores = {
            "factual_accuracy": 0,
            "relevance": 0,
            "completeness": 0,
            "clarity": 0,
            "consistency": 0
        }
        
        for result in validation_results.values():
            for score_name, score_value in result["scores"].items():
                avg_scores[score_name] += score_value
        
        for score_name in avg_scores:
            avg_scores[score_name] /= len(validation_results)
        
        # Collect all issues
        all_issues = []
        for section_name, result in validation_results.items():
            for issue in result["issues"]:
                all_issues.append(f"{section_name}: {issue}")
        
        return {
            "is_valid": is_valid,
            "scores": avg_scores,
            "issues": all_issues,
            "section_results": validation_results
        }
    
    def _validate_report_section(self, section_name: str, section_content: str) -> Dict[str, Any]:
        """Validate a single report section."""
        prompt = f"""
        Validate the following {section_name} section of a research report. 
        Assess the section for:
        1. Factual accuracy: Does the content appear factually sound?
        2. Relevance: Is the content relevant to a {section_name} section?
        3. Completeness: Does the section cover all expected aspects?
        4. Clarity: Is the content clear and well-structured?
        5. Consistency: Is the content consistent with what would be expected in a {section_name} section?
        
        If there are issues with the section, provide suggestions for improvement.
        
        Section content:
        {section_content}
        
        Return your assessment as a JSON object with the following structure:
        {{
            "is_valid": true/false,
            "scores": {{
                "factual_accuracy": 0-10,
                "relevance": 0-10,
                "completeness": 0-10,
                "clarity": 0-10,
                "consistency": 0-10
            }},
            "issues": ["issue1", "issue2", ...],
            "suggestions": ["suggestion1", "suggestion2", ...]
        }}
        """
        
        system_prompt = """
        You are a validation system for research report sections. Your task is to assess sections
        for factual accuracy, relevance, completeness, clarity, and consistency.
        Return your assessment as a JSON object with the specified structure.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        try:
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            validation_result = json.loads(response)
            
            # Ensure the result has the expected structure
            if not isinstance(validation_result, dict):
                validation_result = {
                    "is_valid": False,
                    "scores": {
                        "factual_accuracy": 0,
                        "relevance": 0,
                        "completeness": 0,
                        "clarity": 0,
                        "consistency": 0
                    },
                    "issues": ["Failed to parse validation result"],
                    "suggestions": ["Review and rewrite the section"]
                }
            
            # Ensure all required fields are present
            if "is_valid" not in validation_result:
                validation_result["is_valid"] = False
            
            if "scores" not in validation_result:
                validation_result["scores"] = {
                    "factual_accuracy": 0,
                    "relevance": 0,
                    "completeness": 0,
                    "clarity": 0,
                    "consistency": 0
                }
            
            if "issues" not in validation_result:
                validation_result["issues"] = []
            
            if "suggestions" not in validation_result:
                validation_result["suggestions"] = []
            
            return validation_result
        
        except Exception as e:
            print(f"Error parsing validation result: {e}")
            return {
                "is_valid": False,
                "scores": {
                    "factual_accuracy": 0,
                    "relevance": 0,
                    "completeness": 0,
                    "clarity": 0,
                    "consistency": 0
                },
                "issues": [f"Error parsing validation result: {str(e)}"],
                "suggestions": ["Review and rewrite the section"]
            }
    
    def _format_context_for_llm(self, context: List[Dict[str, Any]]) -> str:
        """Format context for LLM consumption."""
        formatted_context = []
        
        # Process content items first
        content_items = [item for item in context if item["type"] == "content"]
        if content_items:
            formatted_context.append("# Content Items")
            for item in content_items:
                formatted_context.append(f"- Title: {item['title']}")
                formatted_context.append(f"  Source: {item['source_type']}")
                formatted_context.append(f"  URL: {item['url']}")
                formatted_context.append(f"  Text: {item['text_snippet']}")
                formatted_context.append("")
        
        # Process entity items
        entity_items = [item for item in context if item["type"] == "entity"]
        if entity_items:
            entity_by_type = {}
            for item in entity_items:
                entity_type = item["entity_type"]
                if entity_type not in entity_by_type:
                    entity_by_type[entity_type] = []
                entity_by_type[entity_type].append(item)
            
            formatted_context.append("# Entities")
            for entity_type, entities in entity_by_type.items():
                formatted_context.append(f"## {entity_type}s")
                for entity in entities:
                    properties_str = ", ".join(
                        f"{k}: {v}" for k, v in entity["properties"].items()
                        if k not in ["name", "entity_type"]
                    )
                    formatted_context.append(f"- {entity['name']} ({properties_str})")
                formatted_context.append("")
        
        # Process relationship items
        relationship_items = [item for item in context if item["type"] == "relationship"]
        if relationship_items:
            formatted_context.append("# Relationships")
            for item in relationship_items:
                source_name = item["source"]["name"]
                target_name = item["target"]["name"]
                rel_type = item["relationship_type"]
                
                properties_str = ", ".join(
                    f"{k}: {v}" for k, v in item["properties"].items()
                )
                
                formatted_context.append(
                    f"- {source_name} {rel_type} {target_name} ({properties_str})"
                )
        
        return "\n".join(formatted_context)
    
    def run(self, query: str, answer: str, context: List[Dict[str, Any]]):
        """Run the validation process for an answer."""
        print(f"Validating answer for query: {query}")
        validation_result = self.validate_answer(query, answer, context)
        
        print("Validation completed:")
        print(f"- Valid: {validation_result['is_valid']}")
        print(f"- Factual accuracy: {validation_result['scores']['factual_accuracy']}/10")
        print(f"- Relevance: {validation_result['scores']['relevance']}/10")
        print(f"- Completeness: {validation_result['scores']['completeness']}/10")
        print(f"- Clarity: {validation_result['scores']['clarity']}/10")
        
        if validation_result["issues"]:
            print("- Issues:")
            for issue in validation_result["issues"]:
                print(f"  - {issue}")
        
        return validation_result
