import time
import json
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from crew_ai.agents.base_agent import BaseAgent
from crew_ai.utils.database import Neo4jDB
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.utils.messaging import MessageBroker
from crew_ai.config.config import Config, LLMProvider

class LiteRAGAgent(BaseAgent):
    """Agent for answering queries using the knowledge graph."""
    
    def __init__(self, agent_id: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None,
                 neo4j_db: Optional[Neo4jDB] = None):
        """Initialize the LiteRAGAgent."""
        super().__init__(agent_id, llm_client, llm_provider, message_broker)
        
        self.neo4j_db = neo4j_db or Neo4jDB()
        
        # Register message handlers
        self.register_handler("answer_query", self._handle_answer_query)
        self.register_handler("get_subgraph", self._handle_get_subgraph)
    
    def _handle_answer_query(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle answer_query messages."""
        query = message.get("data", {}).get("query")
        context_entities = message.get("data", {}).get("context_entities")
        
        if not query:
            return {"status": "error", "error": "Query is required"}
        
        answer, context, subgraph = self.answer_query(query, context_entities=context_entities)
        
        return {
            "status": "success", 
            "answer": answer,
            "context": context,
            "subgraph": {
                "nodes": len(subgraph["nodes"]),
                "relationships": len(subgraph["relationships"])
            }
        }
    
    def _handle_get_subgraph(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle get_subgraph messages."""
        query = message.get("data", {}).get("query")
        
        if not query:
            return {"status": "error", "error": "Query is required"}
        
        subgraph = self._retrieve_relevant_subgraph(query)
        
        return {
            "status": "success",
            "subgraph": subgraph
        }
    
    def answer_query(self, query: str, context_entities: List[str] = None) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """Answer a query using the knowledge graph."""
        print(f"Answering query: {query}")
        
        # Retrieve relevant subgraph
        subgraph = self._retrieve_relevant_subgraph(query)
        
        if not subgraph["nodes"]:
            return "I don't have enough information to answer this query.", [], subgraph
        
        # Extract context from subgraph
        context = self._extract_context_from_subgraph(subgraph, context_entities)
        
        if not context:
            return "I don't have enough information to answer this query.", [], subgraph
        
        # Generate answer using LLM
        answer = self._generate_answer(query, context)
        
        return answer, context, subgraph
    
    def _retrieve_relevant_subgraph(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant subgraph from Neo4j."""
        # Step 1: Extract key entities and concepts from the query
        query_entities = self._extract_query_entities(query)
        
        # Step 2: Find relevant nodes in the knowledge graph
        relevant_nodes = []
        
        # Find entity nodes that match query entities
        for entity_type, entity_names in query_entities.items():
            for entity_name in entity_names:
                # Search for exact and partial matches
                cypher_query = f"""
                MATCH (n:{entity_type})
                WHERE n.name = $exact_name OR n.name CONTAINS $partial_name
                RETURN n.name AS name, id(n) AS node_id, labels(n) AS node_type
                LIMIT 5
                """
                
                results = self.neo4j_db.query_subgraph(
                    cypher_query, 
                    {"exact_name": entity_name, "partial_name": entity_name}
                )
                
                relevant_nodes.extend(results)
        
        # If no exact matches, try semantic search using query embedding
        if not relevant_nodes:
            query_embedding = self.llm_client.embed(query)
            
            for entity_type in ["Concept", "Topic", "Person", "Organization", "Technology", "Paper"]:
                results = self.neo4j_db.semantic_search(entity_type, query_embedding, limit=3)
                relevant_nodes.extend(results)
        
        # Step 3: Expand from relevant nodes to get a connected subgraph
        subgraph = {"nodes": [], "relationships": []}
        
        if not relevant_nodes:
            return subgraph
        
        # Get unique node IDs
        node_ids = list(set(node["node_id"] for node in relevant_nodes))
        
        # Expand subgraph from these nodes (2-hop neighborhood)
        cypher_query = """
        MATCH path = (n)-[r*0..2]-(m)
        WHERE id(n) IN $node_ids
        WITH nodes(path) AS path_nodes, relationships(path) AS path_rels
        UNWIND path_nodes AS node
        WITH DISTINCT node, path_rels
        RETURN 
            id(node) AS node_id, 
            node.name AS name, 
            labels(node) AS node_type,
            properties(node) AS properties
        LIMIT 100
        """
        
        nodes = self.neo4j_db.query_subgraph(cypher_query, {"node_ids": node_ids})
        
        # Get relationships between these nodes
        if nodes:
            node_ids = [node["node_id"] for node in nodes]
            
            cypher_query = """
            MATCH (n)-[r]->(m)
            WHERE id(n) IN $node_ids AND id(m) IN $node_ids
            RETURN 
                id(r) AS relationship_id,
                id(n) AS source_id,
                id(m) AS target_id,
                type(r) AS relationship_type,
                properties(r) AS properties
            """
            
            relationships = self.neo4j_db.query_subgraph(cypher_query, {"node_ids": node_ids})
            
            subgraph["nodes"] = nodes
            subgraph["relationships"] = relationships
        
        return subgraph
    
    def _extract_query_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from the query using LLM."""
        prompt = f"""
        Extract key entities from the following query. Categorize them into the following types:
        - Person (individual people)
        - Organization (companies, institutions)
        - Location (places, geographical areas)
        - Concept (abstract ideas, theories, frameworks)
        - Technology (tools, programming languages, technical concepts)
        - Paper (research papers, articles, publications)
        
        Return a JSON object with these categories as keys and arrays of entity names as values.
        Only include entities that are explicitly mentioned in the query.
        
        Query: {query}
        """
        
        system_prompt = """
        You are an entity extraction system. Your task is to identify key entities in a query.
        Return ONLY a JSON object with entity types as keys and arrays of entity names as values.
        Example response: {"Person": ["John Smith"], "Concept": ["machine learning"]}
        """
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=200
            )
            
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse JSON object
            entities = json.loads(response)
            
            # Validate the structure
            if isinstance(entities, dict):
                return {k: v for k, v in entities.items() if isinstance(v, list)}
            else:
                return {}
        
        except Exception as e:
            print(f"Error extracting entities from query: {e}")
            return {}
    
    def _extract_context_from_subgraph(self, subgraph: Dict[str, Any], context_entities: List[str] = None) -> List[Dict[str, Any]]:
        """Extract context from the subgraph."""
        context = []
        
        # Get Content nodes from the subgraph
        content_nodes = [
            node for node in subgraph["nodes"] 
            if "Content" in node["node_type"]
        ]
        
        # If we have Content nodes, extract their information
        if content_nodes:
            for node in content_nodes:
                context.append({
                    "type": "content",
                    "title": node["properties"].get("title", ""),
                    "url": node["properties"].get("url", ""),
                    "text_snippet": node["properties"].get("text_snippet", ""),
                    "source_type": node["properties"].get("source_type", "")
                })
        
        # Get other entity nodes
        entity_nodes = [
            node for node in subgraph["nodes"] 
            if "Content" not in node["node_type"]
        ]
        
        # Extract entity information
        for node in entity_nodes:
            entity_type = node["node_type"][0] if node["node_type"] else "Unknown"
            
            if context_entities and node["name"] not in context_entities:
                continue
            
            context.append({
                "type": "entity",
                "entity_type": entity_type,
                "name": node["name"],
                "properties": node["properties"]
            })
        
        # Get relationships
        for rel in subgraph["relationships"]:
            # Find source and target nodes
            source_node = next((node for node in subgraph["nodes"] if node["node_id"] == rel["source_id"]), None)
            target_node = next((node for node in subgraph["nodes"] if node["node_id"] == rel["target_id"]), None)
            
            if source_node and target_node:
                context.append({
                    "type": "relationship",
                    "relationship_type": rel["relationship_type"],
                    "source": {
                        "type": source_node["node_type"][0] if source_node["node_type"] else "Unknown",
                        "name": source_node["name"]
                    },
                    "target": {
                        "type": target_node["node_type"][0] if target_node["node_type"] else "Unknown",
                        "name": target_node["name"]
                    },
                    "properties": rel["properties"]
                })
        
        return context
    
    def _generate_answer(self, query: str, context: List[Dict[str, Any]]) -> str:
        """Generate an answer using LLM based on the query and context."""
        # Format context for LLM
        formatted_context = self._format_context_for_llm(context)
        
        prompt = f"""
        Answer the following query based on the provided context. If the context doesn't contain
        enough information to answer the query, state that you don't have enough information.
        
        Query: {query}
        
        Context:
        {formatted_context}
        """
        
        system_prompt = """
        You are a research assistant with access to a knowledge graph. Your task is to answer
        queries based on the context provided from the knowledge graph. Be concise, accurate,
        and only use information from the provided context. If the context doesn't contain
        enough information to answer the query, state that you don't have enough information.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        return response
    
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
    
    def run(self, query: str, context_entities: List[str] = None):
        """Run the query answering process."""
        print(f"Processing query: {query}")
        answer, context, subgraph = self.answer_query(query, context_entities=context_entities)
        
        print("Query processing completed:")
        print(f"- Subgraph size: {len(subgraph['nodes'])} nodes, {len(subgraph['relationships'])} relationships")
        print(f"- Context items: {len(context)}")
        print(f"- Answer: {answer[:100]}..." if len(answer) > 100 else f"- Answer: {answer}")
        
        return {
            "answer": answer,
            "context": context,
            "subgraph": subgraph
        }
