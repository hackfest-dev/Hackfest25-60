import time
import datetime
import json
import re
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
import spacy
from tqdm import tqdm
import networkx as nx
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

from crew_ai.agents.base_agent import BaseAgent
from crew_ai.utils.database import SQLiteDB, Neo4jDB
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.utils.messaging import MessageBroker
from crew_ai.config.config import Config, LLMProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('KnowledgeGraphAgent')

class KnowledgeGraphAgent(BaseAgent):
    """Agent for creating and managing knowledge graphs.
    
    This agent is responsible for:
    1. Extracting entities from content stored in SQLite
    2. Creating a knowledge graph in Neo4j
    3. Establishing relationships between entities
    4. Providing graph-based analytics and search capabilities
    """
    
    def __init__(self, agent_id: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None,
                 sqlite_db: Optional[SQLiteDB] = None,
                 neo4j_db: Optional[Neo4jDB] = None):
        """Initialize the KnowledgeGraphAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_client: LLM client for entity extraction and analysis
            llm_provider: LLM provider configuration
            message_broker: Message broker for agent communication
            sqlite_db: SQLite database instance
            neo4j_db: Neo4j database instance
        """
        super().__init__(agent_id or "knowledge_graph_agent", 
                         llm_client, 
                         llm_provider, 
                         message_broker)
        
        self.sqlite_db = sqlite_db or SQLiteDB()
        self.neo4j_db = neo4j_db or Neo4jDB()
        
        # Load NLP model for fallback entity extraction
        try:
            self.nlp = spacy.load("en_core_web_sm")
            self.has_spacy = True
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {e}. Fallback entity extraction will be limited.")
            self.has_spacy = False
        
        # Register message handlers
        self.register_handler("create_knowledge_graph", self._handle_create_knowledge_graph)
        self.register_handler("extract_entities", self._handle_extract_entities)
        self.register_handler("get_graph_stats", self._handle_get_graph_stats)
        self.register_handler("semantic_search", self._handle_semantic_search)
        self.register_handler("get_entity_context", self._handle_get_entity_context)
    
    def _handle_create_knowledge_graph(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle create_knowledge_graph messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with the results of the knowledge graph creation
        """
        try:
            max_content_items = message.get("data", {}).get("max_content_items")
            source_filter = message.get("data", {}).get("source_filter")
            
            results = self.create_knowledge_graph(max_content_items, source_filter)
            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Error creating knowledge graph: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _handle_extract_entities(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle extract_entities messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with the extracted entities
        """
        try:
            content_id = message.get("data", {}).get("content_id")
            
            if not content_id:
                return {"status": "error", "error": "Content ID is required"}
            
            with self.sqlite_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM content WHERE id = ?", (content_id,))
                row = cursor.fetchone()
                
                if not row:
                    return {"status": "error", "error": f"Content with ID {content_id} not found"}
                
                content_text = row[0]
                entities = self._extract_entities_from_text(content_text)
                
                # Store entities in SQLite
                for entity_type, entity_dict in entities.items():
                    for entity_name, entity_data in entity_dict.items():
                        # Store entity
                        entity_id = str(uuid.uuid4())
                        metadata = {
                            "count": entity_data["count"],
                            "importance": entity_data["importance"]
                        }
                        
                        with conn:
                            cursor.execute(
                                "INSERT INTO entities (id, name, entity_type, metadata) VALUES (?, ?, ?, ?)",
                                (entity_id, entity_name, entity_type, json.dumps(metadata))
                            )
                            
                            # Link entity to content
                            mention_id = str(uuid.uuid4())
                            cursor.execute(
                                "INSERT INTO entity_mentions (id, entity_id, content_id) VALUES (?, ?, ?)",
                                (mention_id, entity_id, content_id)
                            )
                
                return {"status": "success", "entities": entities}
        except Exception as e:
            logger.error(f"Error extracting entities: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _handle_get_graph_stats(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle get_graph_stats messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with graph statistics
        """
        try:
            # Query Neo4j for graph statistics
            node_stats = self.neo4j_db.run_query("""
                MATCH (n)
                RETURN labels(n) AS node_type, count(*) AS count
                ORDER BY count DESC
            """)
            
            relationship_stats = self.neo4j_db.run_query("""
                MATCH ()-[r]->()
                RETURN type(r) AS relationship_type, count(*) AS count
                ORDER BY count DESC
            """)
            
            if not node_stats or not relationship_stats:
                # Fallback to SQLite stats if Neo4j query fails
                with self.sqlite_db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get entity type counts
                    cursor.execute("""
                        SELECT entity_type, COUNT(*) as count
                        FROM entities
                        GROUP BY entity_type
                        ORDER BY count DESC
                    """)
                    node_stats = [{"node_type": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    # Get mention counts as a proxy for relationships
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM entity_mentions
                    """)
                    mention_count = cursor.fetchone()[0]
                    relationship_stats = [{"relationship_type": "MENTIONS", "count": mention_count}]
            
            return {
                "status": "success",
                "node_stats": node_stats,
                "relationship_stats": relationship_stats,
                "total_nodes": sum(stat["count"] for stat in node_stats) if node_stats else 0,
                "total_relationships": sum(stat["count"] for stat in relationship_stats) if relationship_stats else 0
            }
        except Exception as e:
            logger.error(f"Error getting graph stats: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _handle_semantic_search(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle semantic_search messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with search results
        """
        try:
            query = message.get("data", {}).get("query")
            entity_type = message.get("data", {}).get("entity_type")
            limit = message.get("data", {}).get("limit", 10)
            
            if not query:
                return {"status": "error", "error": "Query is required"}
            
            # Generate query embedding using LLM
            try:
                # This would normally use an embedding model
                # For now, we'll use a simple fallback
                query_embedding = [0.5] * 10  # Placeholder embedding
                
                results = self.neo4j_db.semantic_search(entity_type, query_embedding, limit)
                
                if not results:
                    # Fallback to SQLite text search
                    with self.sqlite_db.get_connection() as conn:
                        cursor = conn.cursor()
                        search_term = f"%{query}%"
                        
                        if entity_type:
                            cursor.execute("""
                                SELECT e.id, e.name, e.entity_type, e.metadata
                                FROM entities e
                                WHERE e.entity_type = ? AND e.name LIKE ?
                                LIMIT ?
                            """, (entity_type, search_term, limit))
                        else:
                            cursor.execute("""
                                SELECT e.id, e.name, e.entity_type, e.metadata
                                FROM entities e
                                WHERE e.name LIKE ?
                                LIMIT ?
                            """, (search_term, limit))
                        
                        results = []
                        for row in cursor.fetchall():
                            metadata = json.loads(row[3]) if row[3] else {}
                            results.append({
                                "id": row[0],
                                "name": row[1],
                                "entity_type": row[2],
                                "score": 0.5,  # Placeholder score
                                "metadata": metadata
                            })
                
                return {"status": "success", "results": results}
            except Exception as e:
                logger.error(f"Error in semantic search: {e}", exc_info=True)
                return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error handling semantic search: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _handle_get_entity_context(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle get_entity_context messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with entity context
        """
        try:
            entity_name = message.get("data", {}).get("entity_name")
            entity_id = message.get("data", {}).get("entity_id")
            limit = message.get("data", {}).get("limit", 5)
            
            if not entity_name and not entity_id:
                return {"status": "error", "error": "Either entity_name or entity_id is required"}
            
            try:
                if entity_id:
                    # Get entity context from SQLite
                    with self.sqlite_db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT e.name, e.entity_type
                            FROM entities e
                            WHERE e.id = ?
                        """, (entity_id,))
                        
                        entity_row = cursor.fetchone()
                        if not entity_row:
                            return {"status": "error", "error": f"Entity with ID {entity_id} not found"}
                        
                        entity_name = entity_row[0]
                        entity_type = entity_row[1]
                        
                        # Get content related to this entity
                        cursor.execute("""
                            SELECT c.id, c.title, c.summary, c.url
                            FROM content c
                            JOIN entity_mentions em ON c.id = em.content_id
                            JOIN entities e ON em.entity_id = e.id
                            WHERE e.id = ?
                            LIMIT ?
                        """, (entity_id, limit))
                        
                        content_items = []
                        for row in cursor.fetchall():
                            content_items.append({
                                "id": row[0],
                                "title": row[1],
                                "summary": row[2],
                                "url": row[3]
                            })
                        
                        return {
                            "status": "success",
                            "entity": {
                                "id": entity_id,
                                "name": entity_name,
                                "type": entity_type
                            },
                            "content_items": content_items
                        }
                else:
                    # Try to get context from Neo4j first
                    context = self.neo4j_db.get_entity_context(entity_name, limit)
                    
                    if not context:
                        # Fallback to SQLite
                        with self.sqlite_db.get_connection() as conn:
                            cursor = conn.cursor()
                            
                            # Find entity by name
                            cursor.execute("""
                                SELECT e.id, e.entity_type
                                FROM entities e
                                WHERE e.name = ?
                            """, (entity_name,))
                            
                            entity_row = cursor.fetchone()
                            if not entity_row:
                                return {"status": "error", "error": f"Entity with name '{entity_name}' not found"}
                            
                            entity_id = entity_row[0]
                            entity_type = entity_row[1]
                            
                            # Get content related to this entity
                            cursor.execute("""
                                SELECT c.id, c.title, c.summary, c.url
                                FROM content c
                                JOIN entity_mentions em ON c.id = em.content_id
                                JOIN entities e ON em.entity_id = e.id
                                WHERE e.id = ?
                                LIMIT ?
                            """, (entity_id, limit))
                            
                            content_items = []
                            for row in cursor.fetchall():
                                content_items.append({
                                    "id": row[0],
                                    "title": row[1],
                                    "summary": row[2],
                                    "url": row[3]
                                })
                            
                            context = content_items
                    
                    return {
                        "status": "success",
                        "entity": {
                            "name": entity_name,
                            "type": entity_type if 'entity_type' in locals() else "Unknown"
                        },
                        "content_items": context
                    }
            except Exception as e:
                logger.error(f"Error getting entity context: {e}", exc_info=True)
                return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"Error handling get entity context: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def _extract_entities_from_text(self, text: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Extract entities from text using LLM with robust fallback mechanisms.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            Dictionary of entity types to entity names to entity data
        """
        entities = {
            "Person": {},
            "Organization": {},
            "Location": {},
            "Concept": {},
            "Technology": {},
            "Paper": {}
        }
        
        # Truncate text if it's too long
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        prompt = f"""
        Extract named entities from the following text. Categorize them into these types:
        - Person: individual people
        - Organization: companies, institutions, groups
        - Location: places, geographical areas
        - Concept: abstract ideas, theories, frameworks
        - Technology: tools, programming languages, technical concepts
        - Paper: research papers, articles, publications
        
        For each entity, include a count (how many times it appears) and an importance score (0.0-1.0).
        
        Return the results as a JSON object with this structure:
        {{
            "Person": {{
                "person_name": {{"count": 1, "importance": 0.7}}
            }},
            "Organization": {{
                "org_name": {{"count": 2, "importance": 0.8}}
            }},
            ...
        }}
        
        Text: {text}
        """
        
        system_prompt = """
        You are an entity extraction system. Extract named entities from text and categorize them.
        Return ONLY a JSON object with the specified structure, no explanation or other text.
        """
        
        try:
            if not self.llm_client:
                # If no LLM client is available, use fallback method
                logger.warning("No LLM client available, using fallback entity extraction")
                return self._fallback_entity_extraction(text)
                
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=1000
            )
            
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse JSON object
            extracted_entities = json.loads(response)
            
            # Validate and merge with our entity structure
            for entity_type, entity_dict in extracted_entities.items():
                if entity_type in entities and isinstance(entity_dict, dict):
                    for entity_name, entity_data in entity_dict.items():
                        if isinstance(entity_data, dict) and "count" in entity_data and "importance" in entity_data:
                            entities[entity_type][entity_name] = {
                                "count": entity_data["count"],
                                "importance": entity_data["importance"]
                            }
            
            return entities
        
        except Exception as e:
            logger.error(f"Error extracting entities with LLM: {e}", exc_info=True)
            
            # Fallback to simple entity extraction
            return self._fallback_entity_extraction(text)
    
    def _fallback_entity_extraction(self, text: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Fallback entity extraction when LLM extraction fails.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            Dictionary of entity types to entity names to entity data
        """
        entities = {
            "Person": {},
            "Organization": {},
            "Location": {},
            "Concept": {},
            "Technology": {},
            "Paper": {}
        }
        
        try:
            if self.has_spacy:
                # Use spaCy for entity extraction
                doc = self.nlp(text[:10000])  # Limit text length for performance
                
                # Map spaCy entity types to our types
                entity_type_map = {
                    "PERSON": "Person",
                    "ORG": "Organization",
                    "GPE": "Location",
                    "LOC": "Location",
                    "PRODUCT": "Technology",
                    "WORK_OF_ART": "Paper"
                }
                
                # Extract entities
                for ent in doc.ents:
                    mapped_type = entity_type_map.get(ent.label_, "Concept")
                    
                    if ent.text in entities[mapped_type]:
                        entities[mapped_type][ent.text]["count"] += 1
                    else:
                        entities[mapped_type][ent.text] = {
                            "count": 1,
                            "importance": 0.5  # Default importance
                        }
                
                # Extract noun chunks as concepts
                for chunk in doc.noun_chunks:
                    if len(chunk.text) > 3 and chunk.text[0].isupper():
                        if chunk.text in entities["Concept"]:
                            entities["Concept"][chunk.text]["count"] += 1
                        else:
                            entities["Concept"][chunk.text] = {
                                "count": 1,
                                "importance": 0.4  # Lower importance for noun chunks
                            }
            else:
                # Simple regex-based extraction
                # Extract potential entities based on capitalization
                words = text.split()
                capitalized_words = [word for word in words if word and word[0].isupper()]
                
                # Count occurrences
                word_counts = {}
                for word in capitalized_words:
                    # Clean the word
                    clean_word = re.sub(r'[^\w\s]', '', word)
                    if len(clean_word) < 3:
                        continue
                        
                    if clean_word in word_counts:
                        word_counts[clean_word] += 1
                    else:
                        word_counts[clean_word] = 1
                
                # Add to entities (default to Concept)
                for word, count in word_counts.items():
                    importance = min(1.0, 0.3 + (count / 10.0))
                    entities["Concept"][word] = {
                        "count": count,
                        "importance": importance
                    }
            
            return entities
            
        except Exception as e:
            logger.error(f"Error in fallback entity extraction: {e}", exc_info=True)
            
            # Return minimal entity set to avoid further errors
            entities["Concept"]["general topic"] = {"count": 1, "importance": 0.5}
            return entities
    
    def create_knowledge_graph(self, max_content_items: Optional[int] = None, source_filter: Optional[str] = None) -> Dict[str, Any]:
        """Create a knowledge graph from the data in SQLite.
        
        Args:
            max_content_items: Maximum number of content items to process
            source_filter: Filter content by source
            
        Returns:
            Results of the knowledge graph creation process
        """
        logger.info("Starting knowledge graph creation...")
        start_time = time.time()
        
        try:
            # Get content from SQLite
            with self.sqlite_db.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT c.id, c.title, c.summary, c.content, c.authors, c.published_date, c.url, c.metadata,
                       s.id as source_id, s.name as source_name, s.url as source_url
                FROM content c
                JOIN sources s ON c.source_id = s.id
                """
                
                params = []
                if source_filter:
                    query += " WHERE s.name = ?"
                    params.append(source_filter)
                
                if max_content_items:
                    query += f" LIMIT {max_content_items}"
                
                cursor.execute(query, params)
                
                all_content = []
                for row in cursor.fetchall():
                    metadata = json.loads(row[7]) if row[7] else {}
                    content_item = {
                        "id": row[0],
                        "title": row[1],
                        "summary": row[2],
                        "content": row[3],
                        "authors": row[4],
                        "published_date": row[5],
                        "url": row[6],
                        "metadata": metadata,
                        "source": {
                            "id": row[8],
                            "name": row[9],
                            "url": row[10]
                        }
                    }
                    all_content.append(content_item)
            
            logger.info(f"Processing {len(all_content)} content items...")
            
            # Process each content item
            entity_nodes = {}  # Map of entity name to Neo4j node ID
            content_nodes = {}  # Map of content ID to Neo4j node ID
            entity_types = set()
            
            # Create a temporary graph in memory for similarity analysis
            temp_graph = nx.Graph()
            
            # Extract text for TF-IDF
            content_texts = []
            content_ids = []
            for item in all_content:
                content_text = ""
                if item["title"]:
                    content_text += item["title"] + " "
                if item["summary"]:
                    content_text += item["summary"] + " "
                if item["content"]:
                    content_text += item["content"]
                
                content_texts.append(content_text)
                content_ids.append(item["id"])
            
            # Calculate TF-IDF vectors for content similarity
            try:
                vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
                tfidf_matrix = vectorizer.fit_transform(content_texts)
                
                # Calculate pairwise similarity
                cosine_sim = cosine_similarity(tfidf_matrix)
            except Exception as e:
                logger.error(f"Error calculating content similarity: {e}", exc_info=True)
                cosine_sim = None
            
            # Process content items
            for i, content_item in enumerate(tqdm(all_content, desc="Processing content")):
                content_id = content_item["id"]
                content_text = content_item.get("content", "")
                if not content_text and content_item.get("summary"):
                    content_text = content_item["summary"]
                
                source_url = content_item.get("url", "")
                source_title = content_item.get("title", "")
                source_name = content_item["source"]["name"] if "source" in content_item else "unknown"
                
                # Create content node in Neo4j
                try:
                    content_node_id = self.neo4j_db.create_entity_node(
                        entity_type="Content",
                        name=f"Content_{content_id}",
                        properties={
                            "content_id": content_id,
                            "title": source_title,
                            "url": source_url,
                            "source": source_name,
                            "text_snippet": content_text[:200] + "..." if len(content_text) > 200 else content_text
                        }
                    )
                    content_nodes[content_id] = content_node_id
                except Exception as e:
                    logger.error(f"Error creating content node: {e}", exc_info=True)
                    continue
                
                # Extract entities from content
                entities = self._extract_entities_from_text(content_text)
                
                # Create entity nodes and relationships
                for entity_type, entity_list in entities.items():
                    for entity_name, entity_data in entity_list.items():
                        # Skip if entity name is too short or just numbers
                        if len(entity_name) < 3 or entity_name.isdigit():
                            continue
                        
                        entity_types.add(entity_type)
                        
                        # Create or get entity node
                        try:
                            if entity_name not in entity_nodes:
                                entity_node_id = self.neo4j_db.create_entity_node(
                                    entity_type=entity_type,
                                    name=entity_name,
                                    properties={
                                        "frequency": entity_data["count"],
                                        "importance": entity_data["importance"]
                                    }
                                )
                                entity_nodes[entity_name] = entity_node_id
                            else:
                                entity_node_id = entity_nodes[entity_name]
                            
                            # Create relationship between content and entity
                            self.neo4j_db.create_relationship(
                                from_id=content_node_id,
                                to_id=entity_node_id,
                                rel_type="MENTIONS",
                                properties={
                                    "count": entity_data["count"],
                                    "importance": entity_data["importance"]
                                }
                            )
                            
                            # Add to temporary graph for analysis
                            if entity_name not in temp_graph:
                                temp_graph.add_node(entity_name, type=entity_type)
                            
                            # Add edges between entities that co-occur
                            for other_entity_type, other_entity_list in entities.items():
                                for other_entity_name in other_entity_list:
                                    if entity_name != other_entity_name:
                                        if other_entity_name not in temp_graph:
                                            temp_graph.add_node(other_entity_name, type=other_entity_type)
                                        
                                        if temp_graph.has_edge(entity_name, other_entity_name):
                                            temp_graph[entity_name][other_entity_name]['weight'] += 1
                                        else:
                                            temp_graph.add_edge(entity_name, other_entity_name, weight=1)
                        except Exception as e:
                            logger.error(f"Error processing entity {entity_name}: {e}", exc_info=True)
                            continue
            
            # Create similarity relationships between content
            if cosine_sim is not None:
                logger.info("Creating similarity relationships between content...")
                similarity_threshold = 0.3
                
                for i in tqdm(range(len(all_content)), desc="Creating content similarity relationships"):
                    for j in range(i+1, len(all_content)):
                        if cosine_sim[i, j] > similarity_threshold:
                            try:
                                self.neo4j_db.create_relationship(
                                    from_id=content_nodes[content_ids[i]],
                                    to_id=content_nodes[content_ids[j]],
                                    rel_type="SIMILAR_TO",
                                    properties={
                                        "similarity_score": float(cosine_sim[i, j])
                                    }
                                )
                            except Exception as e:
                                logger.error(f"Error creating similarity relationship: {e}", exc_info=True)
                                continue
            
            # Create relationships between entities based on co-occurrence
            logger.info("Creating relationships between entities...")
            for edge in tqdm(temp_graph.edges(data=True), desc="Creating entity relationships"):
                entity1, entity2, data = edge
                
                if entity1 in entity_nodes and entity2 in entity_nodes:
                    weight = data['weight']
                    
                    if weight > 1:  # Only create relationships for entities that co-occur multiple times
                        try:
                            self.neo4j_db.create_relationship(
                                from_id=entity_nodes[entity1],
                                to_id=entity_nodes[entity2],
                                rel_type="RELATED_TO",
                                properties={
                                    "weight": weight,
                                    "strength": min(1.0, weight / 10.0)  # Normalize strength
                                }
                            )
                        except Exception as e:
                            logger.error(f"Error creating entity relationship: {e}", exc_info=True)
                            continue
            
            # Try to create topic clusters
            try:
                logger.info("Creating topic clusters...")
                self._create_topic_clusters(entity_nodes)
            except Exception as e:
                logger.error(f"Error creating topic clusters: {e}", exc_info=True)
            
            end_time = time.time()
            
            return {
                "status": "success",
                "execution_time": end_time - start_time,
                "content_nodes": len(content_nodes),
                "entity_nodes": len(entity_nodes),
                "entity_types": list(entity_types)
            }
        except Exception as e:
            logger.error(f"Error creating knowledge graph: {e}", exc_info=True)
            end_time = time.time()
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": end_time - start_time
            }
    
    def _create_topic_clusters(self, entity_nodes: Dict[str, str]):
        """Create topic clusters using LLM.
        
        Args:
            entity_nodes: Map of entity name to Neo4j node ID
        """
        # Get all concept entities
        try:
            concept_entities = self.neo4j_db.run_query("""
                MATCH (c:Concept)
                RETURN c.name AS name, id(c) AS node_id
            """)
            
            if not concept_entities:
                logger.warning("No concept entities found for topic clustering")
                return
            
            # Group concepts into topics using LLM
            concept_names = [entity["name"] for entity in concept_entities]
            topics = self._cluster_concepts_with_llm(concept_names)
            
            # Create topic nodes and relationships
            for topic_name, topic_concepts in topics.items():
                # Create topic node
                try:
                    topic_node_id = self.neo4j_db.create_entity_node(
                        entity_type="Topic",
                        name=topic_name,
                        properties={
                            "concept_count": len(topic_concepts)
                        }
                    )
                    
                    # Create relationships between topic and concepts
                    for concept in topic_concepts:
                        # Find the concept node
                        for entity in concept_entities:
                            if entity["name"] == concept:
                                self.neo4j_db.create_relationship(
                                    from_id=topic_node_id,
                                    to_id=entity["node_id"],
                                    rel_type="CONTAINS",
                                    properties={}
                                )
                                break
                except Exception as e:
                    logger.error(f"Error creating topic node {topic_name}: {e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error in topic clustering: {e}", exc_info=True)
    
    def _cluster_concepts_with_llm(self, concepts: List[str]) -> Dict[str, List[str]]:
        """Cluster concepts into topics using LLM.
        
        Args:
            concepts: List of concept names to cluster
            
        Returns:
            Dictionary of topic names to lists of concepts
        """
        if not concepts:
            return {}
        
        if not self.llm_client:
            logger.warning("No LLM client available for concept clustering")
            return {}
        
        # Limit number of concepts to process
        if len(concepts) > 100:
            concepts = concepts[:100]
        
        concepts_str = json.dumps(concepts)
        
        prompt = f"""
        Group the following concepts into 5-10 coherent topics. Each concept should be assigned to exactly one topic.
        Return a JSON object where keys are topic names and values are arrays of concepts belonging to that topic.
        
        Concepts: {concepts_str}
        """
        
        system_prompt = """
        You are a concept clustering system. Your task is to group concepts into coherent topics.
        Return ONLY a JSON object where keys are topic names and values are arrays of concepts.
        Example response: {{"Machine Learning": ["neural networks", "deep learning"], "NLP": ["text mining", "sentiment analysis"]}}
        """
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse JSON object
            topics = json.loads(response)
            
            # Validate the structure
            if isinstance(topics, dict):
                return {k: v for k, v in topics.items() if isinstance(v, list)}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Error clustering concepts with LLM: {e}", exc_info=True)
            return {}
    
    def run(self, max_content_items: Optional[int] = None, source_filter: Optional[str] = None):
        """Run the knowledge graph creation process.
        
        Args:
            max_content_items: Maximum number of content items to process
            source_filter: Filter content by source
            
        Returns:
            Results of the knowledge graph creation process
        """
        logger.info("Starting knowledge graph creation...")
        results = self.create_knowledge_graph(max_content_items, source_filter)
        
        if results["status"] == "success":
            logger.info("Knowledge graph creation completed:")
            logger.info(f"- Execution time: {results['execution_time']:.2f} seconds")
            logger.info(f"- Content nodes: {results['content_nodes']}")
            logger.info(f"- Entity nodes: {results['entity_nodes']}")
            logger.info(f"- Entity types: {', '.join(results['entity_types'])}")
        else:
            logger.error(f"Knowledge graph creation failed: {results.get('error', 'Unknown error')}")
        
        return results
