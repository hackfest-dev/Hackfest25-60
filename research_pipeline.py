"""Research Pipeline for AgentSus2.

This script integrates all components of the research pipeline:
1. Data mining from various sources
2. Storing data in a temporary SQLite database
3. Creating a knowledge graph with proper relationships
4. Using LiteRAG to generate structured research content
5. Creating a LaTeX research paper
"""

import os
import argparse
import logging
from typing import List, Dict, Any, Optional
import time
import uuid

from crew_ai.agents.data_miner_agent import DataMinerAgent
from crew_ai.agents.knowledge_graph_agent import KnowledgeGraphAgent
from crew_ai.agents.lite_rag_agent import LiteRAGAgent
from crew_ai.agents.writer_agent import WriterAgent
from crew_ai.models.llm_client import get_llm_client
from crew_ai.utils.temp_sqlite import TempSQLiteDB
from crew_ai.utils.database import SQLiteDB
from crew_ai.config.config import Config, LLMProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("research_pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ResearchPipeline')

class ResearchPipeline:
    """Research pipeline for AgentSus2."""
    
    def __init__(self, 
                 db_path: str = "research_data.db",
                 output_dir: str = "output",
                 llm_provider: Optional[LLMProvider] = None):
        """Initialize the research pipeline.
        
        Args:
            db_path: Path to the SQLite database
            output_dir: Directory to store output files
            llm_provider: LLM provider configuration
        """
        self.db_path = db_path
        self.output_dir = output_dir
        self.llm_provider = llm_provider or LLMProvider.OPENAI
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize LLM client
        self.llm_client = get_llm_client(self.llm_provider)
        
        # Initialize shared database
        self.db = TempSQLiteDB(db_path)
        
        # Initialize agents
        self.data_miner = DataMinerAgent(
            agent_id="data_miner",
            llm_client=self.llm_client,
            llm_provider=self.llm_provider,
            db=self.db  # DataMinerAgent uses 'db' parameter, not 'sqlite_db'
        )
        
        self.knowledge_graph = KnowledgeGraphAgent(
            agent_id="knowledge_graph",
            llm_client=self.llm_client,
            llm_provider=self.llm_provider,
            sqlite_db=self.db,  # Use the shared database
            temp_db_path=db_path  # Use the same database for temp storage
        )
        
        self.lite_rag = LiteRAGAgent(
            agent_id="lite_rag",
            llm_client=self.llm_client,
            llm_provider=self.llm_provider
            # LiteRAGAgent doesn't accept a sqlite_db parameter
        )
        
        self.writer = WriterAgent(
            agent_id="writer",
            llm_client=self.llm_client,
            llm_provider=self.llm_provider,
            latex_temp_dir=os.path.join(output_dir, "latex_temp")
        )
        
        logger.info(f"Research pipeline initialized with database at {db_path}")
    
    def run(self, 
            query: str, 
            sources: List[str] = None,
            max_results: int = 50,
            paper_title: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete research pipeline.
        
        Args:
            query: Research query
            sources: List of sources to mine data from
            max_results: Maximum number of results to mine
            paper_title: Title of the research paper (if None, will be generated)
            
        Returns:
            Results of the pipeline execution
        """
        start_time = time.time()
        logger.info(f"Starting research pipeline for query: {query}")
        
        # Step 1: Mine data
        logger.info("Step 1: Mining data...")
        mining_results = self.data_miner.mine_data(query, sources, max_results)
        logger.info(f"Data mining completed: {mining_results['successful_sources']} successful sources")
        
        # Step 2: Create knowledge graph directly (no need to transfer data)
        logger.info("Step 2: Creating knowledge graph...")
        graph_results = self.knowledge_graph.create_knowledge_graph(use_temp_db=True)
        logger.info(f"Knowledge graph creation completed: {graph_results.get('content_nodes', 0)} content nodes, {graph_results.get('entity_nodes', 0)} entity nodes")
        
        # Step 3: Generate research questions
        logger.info("Step 3: Generating research questions...")
        research_questions = self._generate_research_questions(query)
        logger.info(f"Generated {len(research_questions)} research questions")
        
        # Step 4: Answer research questions using LiteRAG
        logger.info("Step 4: Answering research questions...")
        answers = []
        for question in research_questions:
            logger.info(f"Answering question: {question}")
            # Use the knowledge graph agent's entity extraction to enhance the query
            extracted_entities = self.knowledge_graph._extract_entities_from_text(question)
            entity_names = []
            for entity_type, entities in extracted_entities.items():
                entity_names.extend(list(entities.keys()))
            
            logger.info(f"Extracted entities: {entity_names}")
            
            # Use LiteRAG to answer the question
            answer_result = self.lite_rag.answer_query(question, context_entities=entity_names)
            answers.append(answer_result[0])  # Extract answer text
            logger.info(f"Answer generated: {answer_result[0][:100]}...")
        
        # Step 5: Generate paper title if not provided
        if not paper_title:
            logger.info("Step 5: Generating paper title...")
            paper_title = self._generate_paper_title(query, research_questions, answers)
            logger.info(f"Paper title generated: {paper_title}")
        
        # Step 6: Generate research paper
        logger.info("Step 6: Generating research paper...")
        output_base = os.path.join(self.output_dir, f"research_paper_{uuid.uuid4().hex[:8]}")
        output_path = f"{output_base}.pdf"
        
        # Format questions and answers for the writer agent
        formatted_qa_pairs = []
        for i, (question, answer) in enumerate(zip(research_questions, answers)):
            formatted_qa_pairs.append({
                "query": question,
                "answer": answer
            })
        
        # Generate the report
        paper_result = self.writer.generate_report(
            title=paper_title,
            queries=research_questions,
            answers=formatted_qa_pairs,  # Pass the formatted QA pairs instead of raw answers
            output_path=output_path
        )
        
        # Check for alternative formats
        output_formats = {
            "pdf": paper_result if paper_result.endswith(".pdf") else None,
            "html": output_base + ".html" if os.path.exists(output_base + ".html") else None,
            "markdown": output_base + ".md" if os.path.exists(output_base + ".md") else None,
            "latex": output_base + ".tex" if os.path.exists(output_base + ".tex") else None
        }
        
        logger.info(f"Research paper generated with formats: {[fmt for fmt, path in output_formats.items() if path]}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            "status": "success",
            "query": query,
            "paper_title": paper_title,
            "output_formats": output_formats,
            "execution_time": execution_time,
            "research_questions": research_questions,
            "answers": answers,
            "mining_results": mining_results,
            "graph_results": graph_results
        }
    
    def _generate_research_questions(self, query: str, num_questions: int = 5) -> List[str]:
        """Generate research questions based on the query.
        
        Args:
            query: Research query
            num_questions: Number of questions to generate
            
        Returns:
            List of research questions
        """
        prompt = f"""
        Generate {num_questions} specific research questions based on the following query:
        
        Query: {query}
        
        The questions should:
        1. Be specific and focused
        2. Cover different aspects of the topic
        3. Be answerable using the knowledge graph
        4. Be suitable for a research paper
        
        Return ONLY the questions, one per line, without numbering.
        """
        
        system_prompt = """
        You are a research question generator. Your task is to generate specific, focused research questions
        based on a given query. The questions should cover different aspects of the topic and be suitable
        for a research paper. Return ONLY the questions, one per line, without numbering or explanations.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse questions
        questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
        
        # Limit to requested number
        return questions[:num_questions]
    
    def _generate_paper_title(self, query: str, questions: List[str], answers: List[str]) -> str:
        """Generate a paper title based on the query, questions, and answers.
        
        Args:
            query: Research query
            questions: Research questions
            answers: Answers to research questions
            
        Returns:
            Paper title
        """
        # Combine questions and answers
        qa_text = ""
        for i, (question, answer) in enumerate(zip(questions, answers)):
            qa_text += f"Question {i+1}: {question}\n"
            qa_text += f"Answer {i+1}: {answer[:200]}...\n\n"
        
        prompt = f"""
        Generate a concise, academic title for a research paper based on the following:
        
        Research Query: {query}
        
        Questions and Answers:
        {qa_text}
        
        The title should:
        1. Be concise (10-15 words)
        2. Be specific to the research topic
        3. Use academic language
        4. Avoid clickbait or sensationalism
        5. Not use colons or subtitles
        
        Return ONLY the title, without quotes or explanations.
        """
        
        system_prompt = """
        You are a research paper title generator. Your task is to generate a concise, academic title
        for a research paper based on a query and research questions/answers. Return ONLY the title,
        without quotes, numbering, or explanations.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=50
        )
        
        # Clean up title
        title = response.strip().replace('"', '').replace("'", "")
        
        return title

def main():
    """Main function to run the research pipeline from command line."""
    parser = argparse.ArgumentParser(description="Run the AgentSus2 Research Pipeline")
    parser.add_argument("query", help="Research query")
    parser.add_argument("--sources", nargs="+", default=["arxiv", "reddit", "medium"], 
                        help="Sources to mine data from")
    parser.add_argument("--max-results", type=int, default=50,
                        help="Maximum number of results to mine")
    parser.add_argument("--paper-title", default=None,
                        help="Title of the research paper (if not provided, will be generated)")
    parser.add_argument("--db-path", default="research_data.db",
                        help="Path to the SQLite database")
    parser.add_argument("--output-dir", default="output",
                        help="Directory to store output files")
    
    args = parser.parse_args()
    
    # Initialize and run pipeline
    pipeline = ResearchPipeline(
        db_path=args.db_path,
        output_dir=args.output_dir
    )
    
    results = pipeline.run(
        query=args.query,
        sources=args.sources,
        max_results=args.max_results,
        paper_title=args.paper_title
    )
    
    print(f"\nResearch pipeline completed in {results['execution_time']:.2f} seconds")
    print(f"Paper title: {results['paper_title']}")
    print(f"Output formats: {results['output_formats']}")

if __name__ == "__main__":
    main()
