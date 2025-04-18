import time
import threading
from typing import Dict, Any, List, Optional, Tuple
import queue

from crew_ai.agents.data_miner_agent import DataMinerAgent
from crew_ai.agents.knowledge_graph_agent import KnowledgeGraphAgent
from crew_ai.agents.lite_rag_agent import LiteRAGAgent
from crew_ai.agents.validator_agent import ValidatorAgent
from crew_ai.agents.writer_agent import WriterAgent
from crew_ai.utils.messaging import MessageBroker
from crew_ai.models.llm_client import get_llm_client
from crew_ai.config.config import Config, LLMProvider

class Orchestrator:
    """Orchestrator for the Crew AI framework."""
    
    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        """Initialize the orchestrator."""
        self.llm_provider = llm_provider or Config.LLM_PROVIDER
        self.message_broker = MessageBroker()
        self.llm_client = get_llm_client(self.llm_provider)
        
        # Initialize agents
        self.data_miner_agent = DataMinerAgent(
            agent_id="data_miner",
            llm_client=self.llm_client,
            message_broker=self.message_broker
        )
        
        self.knowledge_graph_agent = KnowledgeGraphAgent(
            agent_id="knowledge_graph",
            llm_client=self.llm_client,
            message_broker=self.message_broker
        )
        
        self.lite_rag_agent = LiteRAGAgent(
            agent_id="lite_rag",
            llm_client=self.llm_client,
            message_broker=self.message_broker
        )
        
        self.validator_agent = ValidatorAgent(
            agent_id="validator",
            llm_client=self.llm_client,
            message_broker=self.message_broker
        )
        
        self.writer_agent = WriterAgent(
            agent_id="writer",
            llm_client=self.llm_client,
            message_broker=self.message_broker
        )
        
        # Create a queue for storing results
        self.result_queue = queue.Queue()
    
    def mine_data(self, query: str, sources: List[str] = None, max_results: int = None) -> Dict[str, Any]:
        """Mine data using the DataMinerAgent."""
        print(f"Starting data mining for query: {query}")
        
        result = self.data_miner_agent.send_message(
            target_agent_id="data_miner",
            message_type="mine_data",
            data={
                "query": query,
                "sources": sources,
                "max_results": max_results
            },
            wait_for_response=True,
            timeout=3600  # 1 hour timeout for data mining
        )
        
        return result
    
    def create_knowledge_graph(self, max_content_items: Optional[int] = None) -> Dict[str, Any]:
        """Create a knowledge graph using the KnowledgeGraphAgent."""
        print("Starting knowledge graph creation...")
        
        result = self.knowledge_graph_agent.send_message(
            target_agent_id="knowledge_graph",
            message_type="create_knowledge_graph",
            data={
                "max_content_items": max_content_items
            },
            wait_for_response=True,
            timeout=3600  # 1 hour timeout for knowledge graph creation
        )
        
        return result
    
    def answer_query(self, query: str) -> Dict[str, Any]:
        """Answer a query using the LiteRAGAgent and ValidatorAgent."""
        print(f"Processing query: {query}")
        
        # Get answer from LiteRAGAgent
        rag_result = self.lite_rag_agent.send_message(
            target_agent_id="lite_rag",
            message_type="answer_query",
            data={
                "query": query
            },
            wait_for_response=True,
            timeout=300  # 5 minutes timeout for query answering
        )
        
        if rag_result.get("status") != "success":
            return {"status": "error", "error": "Failed to get answer from LiteRAGAgent"}
        
        answer = rag_result.get("answer", "")
        context = rag_result.get("context", [])
        
        # Validate answer using ValidatorAgent
        validation_result = self.validator_agent.send_message(
            target_agent_id="validator",
            message_type="validate_answer",
            data={
                "query": query,
                "answer": answer,
                "context": context
            },
            wait_for_response=True,
            timeout=300  # 5 minutes timeout for validation
        )
        
        if validation_result.get("status") != "success":
            return {"status": "error", "error": "Failed to validate answer"}
        
        # Use corrected answer if available
        corrected_answer = validation_result.get("validation_result", {}).get("corrected_answer", answer)
        
        return {
            "status": "success",
            "query": query,
            "answer": corrected_answer,
            "validation": validation_result.get("validation_result", {})
        }
    
    def generate_report(self, title: str, queries: List[str], answers: List[str], 
                       output_path: str = "report.pdf") -> Dict[str, Any]:
        """Generate a report using the WriterAgent."""
        print(f"Generating report: {title}")
        
        result = self.writer_agent.send_message(
            target_agent_id="writer",
            message_type="generate_report",
            data={
                "title": title,
                "queries": queries,
                "answers": answers,
                "output_path": output_path
            },
            wait_for_response=True,
            timeout=1800  # 30 minutes timeout for report generation
        )
        
        return result
    
    def run_research_pipeline(self, research_query: str, 
                             sources: List[str] = None, 
                             max_results: int = None,
                             output_path: str = "report.pdf") -> Dict[str, Any]:
        """Run the complete research pipeline."""
        print(f"Starting research pipeline for query: {research_query}")
        start_time = time.time()
        
        # Step 1: Mine data
        print("Step 1: Mining data...")
        mining_result = self.mine_data(research_query, sources, max_results)
        
        if mining_result.get("status") != "success":
            return {"status": "error", "error": "Data mining failed", "details": mining_result}
        
        # Step 2: Create knowledge graph
        print("Step 2: Creating knowledge graph...")
        graph_result = self.create_knowledge_graph()
        
        if graph_result.get("status") != "success":
            return {"status": "error", "error": "Knowledge graph creation failed", "details": graph_result}
        
        # Step 3: Generate sub-queries
        print("Step 3: Generating sub-queries...")
        sub_queries = self._generate_sub_queries(research_query)
        
        # Step 4: Answer sub-queries
        print("Step 4: Answering sub-queries...")
        answers = []
        
        for query in sub_queries:
            answer_result = self.answer_query(query)
            
            if answer_result.get("status") == "success":
                answers.append(answer_result.get("answer", ""))
            else:
                print(f"Failed to answer query: {query}")
                answers.append("No answer available.")
        
        # Step 5: Generate report
        print("Step 5: Generating report...")
        report_result = self.generate_report(
            title=f"Research Report: {research_query}",
            queries=sub_queries,
            answers=answers,
            output_path=output_path
        )
        
        if report_result.get("status") != "success":
            return {"status": "error", "error": "Report generation failed", "details": report_result}
        
        end_time = time.time()
        
        return {
            "status": "success",
            "execution_time": end_time - start_time,
            "research_query": research_query,
            "sub_queries": sub_queries,
            "answers": answers,
            "report_path": report_result.get("report_path", "")
        }
    
    def _generate_sub_queries(self, main_query: str) -> List[str]:
        """Generate sub-queries from the main research query."""
        prompt = f"""
        Break down the following research query into 3-5 specific sub-queries that would help answer the main question.
        Each sub-query should focus on a different aspect of the main query and be specific enough to get a detailed answer.
        
        Main Query: {main_query}
        
        Return only a JSON array of strings with the sub-queries, with no explanation.
        """
        
        system_prompt = """
        You are a research query generator. Your task is to break down a main research query into specific sub-queries.
        Return ONLY a JSON array of strings with the sub-queries, with no explanation or other text.
        Example response: ["What are the key factors affecting X?", "How does Y impact Z?", "What are the current trends in W?"]
        """
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract JSON array from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse JSON array
            import json
            import re
            
            # Try to find JSON array in the response
            match = re.search(r'\[.*\]', response, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    sub_queries = json.loads(json_str)
                    
                    # Ensure we have a list of strings
                    if isinstance(sub_queries, list):
                        return [q for q in sub_queries if isinstance(q, str)]
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {json_str}")
            
            # Fallback: extract questions using regex
            questions = re.findall(r'"([^"]+\?)"', response)
            if questions:
                return questions
                
            # If all else fails, return the main query
            return [main_query]
            
        except Exception as e:
            print(f"Error generating sub-queries: {e}")
            return [main_query]
    
    def stop(self):
        """Stop all agents."""
        print("Stopping all agents...")
        
        agents = [
            self.data_miner_agent,
            self.knowledge_graph_agent,
            self.lite_rag_agent,
            self.validator_agent,
            self.writer_agent
        ]
        
        for agent in agents:
            agent.stop()
        
        self.message_broker.close()
