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
from crew_ai.utils.temp_sqlite import TempSQLiteDB
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
                 neo4j_db: Optional[Neo4jDB] = None,
                 temp_db_path: Optional[str] = None):
        """Initialize the KnowledgeGraphAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            llm_client: LLM client for entity extraction and analysis
            llm_provider: LLM provider configuration
            message_broker: Message broker for agent communication
            sqlite_db: SQLite database instance
            neo4j_db: Neo4j database instance
            temp_db_path: Path to the temporary SQLite database
        """
        super().__init__(agent_id or "knowledge_graph_agent", 
                         llm_client, 
                         llm_provider, 
                         message_broker)
        
        # If sqlite_db is provided and it's a TempSQLiteDB, use it for both
        if sqlite_db and isinstance(sqlite_db, TempSQLiteDB):
            self.sqlite_db = sqlite_db
            self.temp_db = sqlite_db
            logger.info(f"Using shared database for both SQLite and temp operations")
        else:
            # Otherwise, initialize separate databases
            self.sqlite_db = sqlite_db or SQLiteDB()
            self.temp_db = TempSQLiteDB(temp_db_path) if temp_db_path else None
            logger.info(f"Using separate databases for SQLite and temp operations")
        
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
        self.register_handler("transfer_data_to_temp_db", self._handle_transfer_data_to_temp_db)
        
        # Only register these handlers if we're using the message broker (legacy orchestrator)
        if message_broker:
            self.register_handler("semantic_search", self._handle_semantic_search)
            self.register_handler("get_entity_context", self._handle_get_entity_context)
    
    def _handle_transfer_data_to_temp_db(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle transfer_data_to_temp_db messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with the results of the data transfer
        """
        try:
            max_content_items = message.get("data", {}).get("max_content_items")
            source_filter = message.get("data", {}).get("source_filter")
            
            results = self.transfer_data_to_temp_db(max_content_items, source_filter)
            return {"status": "success", "results": results}
        except Exception as e:
            logger.error(f"Error transferring data to temp DB: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def transfer_data_to_temp_db(self, max_content_items: Optional[int] = None, source_filter: Optional[str] = None) -> Dict[str, Any]:
        """Transfer data from SQLite to the temporary database.
        
        Args:
            max_content_items: Maximum number of content items to transfer
            source_filter: Filter content by source
            
        Returns:
            Results of the data transfer
        """
        logger.info("Starting data transfer to temporary database...")
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
                
                content_items = []
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
                    content_items.append(content_item)
            
            logger.info(f"Found {len(content_items)} content items to transfer")
            
            # Transfer content to temp DB
            content_count = 0
            entity_count = 0
            relationship_count = 0
            
            for content_item in tqdm(content_items, desc="Transferring content"):
                # Store source
                source_id = self.temp_db.store_source(
                    content_item["source"]["name"],
                    content_item["source"]["url"]
                )
                
                # Store content
                content_id = self.temp_db.store_content(content_item, source_id)
                content_count += 1
                
                # Extract entities
                content_text = content_item.get("content", "")
                if not content_text:
                    content_text = content_item.get("summary", "")
                
                entities = self._extract_entities_from_text(content_text)
                
                # Store entities and create relationships
                entity_ids = {}
                
                for entity_type, entity_dict in entities.items():
                    for entity_name, entity_data in entity_dict.items():
                        # Skip if entity name is too short or just numbers
                        if len(entity_name) < 3 or entity_name.isdigit():
                            continue
                        
                        # Store entity
                        entity_id = self.temp_db.store_entity(
                            entity_name,
                            entity_type,
                            {
                                "count": entity_data["count"],
                                "importance": entity_data["importance"]
                            }
                        )
                        
                        # Link entity to content
                        self.temp_db.link_entity_to_content(entity_id, content_id)
                        
                        entity_ids[entity_name] = entity_id
                        entity_count += 1
                
                # Create relationships between co-occurring entities
                for entity1_name, entity1_id in entity_ids.items():
                    for entity2_name, entity2_id in entity_ids.items():
                        if entity1_name != entity2_name:
                            self.temp_db.create_relationship(
                                entity1_id,
                                entity2_id,
                                "CO_OCCURS_WITH",
                                1.0,
                                {
                                    "content_id": content_id
                                }
                            )
                            relationship_count += 1
            
            end_time = time.time()
            
            return {
                "status": "success",
                "execution_time": end_time - start_time,
                "content_count": content_count,
                "entity_count": entity_count,
                "relationship_count": relationship_count
            }
        except Exception as e:
            logger.error(f"Error transferring data to temp DB: {e}", exc_info=True)
            end_time = time.time()
            
            return {
                "status": "error",
                "error": str(e),
                "execution_time": end_time - start_time
            }
    
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
            use_temp_db = message.get("data", {}).get("use_temp_db", True)
            
            results = self.create_knowledge_graph(max_content_items, source_filter, use_temp_db)
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
            use_temp_db = message.get("data", {}).get("use_temp_db", False)
            
            if not content_id:
                return {"status": "error", "error": "Content ID is required"}
            
            db = self.temp_db if use_temp_db else self.sqlite_db
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT content FROM content WHERE id = ?", (content_id,))
                row = cursor.fetchone()
                
                if not row:
                    return {"status": "error", "error": f"Content with ID {content_id} not found"}
                
                content_text = row[0]
                entities = self._extract_entities_from_text(content_text)
                
                # Store entities in the database
                for entity_type, entity_dict in entities.items():
                    for entity_name, entity_data in entity_dict.items():
                        # Skip if entity name is too short or just numbers
                        if len(entity_name) < 3 or entity_name.isdigit():
                            continue
                            
                        # Store entity
                        entity_id = db.store_entity(
                            entity_name,
                            entity_type,
                            {
                                "count": entity_data["count"],
                                "importance": entity_data["importance"]
                            }
                        )
                        
                        # Link entity to content
                        db.link_entity_to_content(entity_id, content_id)
                
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
            use_temp_db = message.get("data", {}).get("use_temp_db", False)
            
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
                # Fallback to database stats
                db = self.temp_db if use_temp_db else self.sqlite_db
                
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get entity type counts
                    cursor.execute("""
                        SELECT entity_type, COUNT(*) as count
                        FROM entities
                        GROUP BY entity_type
                        ORDER BY count DESC
                    """)
                    node_stats = [{"node_type": row[0], "count": row[1]} for row in cursor.fetchall()]
                    
                    # Get relationship type counts
                    if isinstance(db, TempSQLiteDB):
                        cursor.execute("""
                            SELECT relationship_type, COUNT(*) as count
                            FROM relationships
                            GROUP BY relationship_type
                            ORDER BY count DESC
                        """)
                        relationship_stats = [{"relationship_type": row[0], "count": row[1]} for row in cursor.fetchall()]
                    else:
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
            query = message.get("data", {}).get("query", "")
            limit = message.get("data", {}).get("limit", 10)
            
            if not query:
                return {"status": "error", "error": "No query provided"}
            
            # Extract entities from the query
            query_entities = self._extract_entities_from_text(query)
            
            # Flatten entity dictionary
            entity_names = []
            for entity_type, entities in query_entities.items():
                entity_names.extend(list(entities.keys()))
            
            results = []
            
            # If we have entities, search for them in Neo4j
            if entity_names:
                try:
                    with self.neo4j_db.get_session() as session:
                        # Search for content related to the entities
                        cypher_query = """
                        MATCH (c:Content)-[:MENTIONS]->(e:Entity)
                        WHERE e.name IN $entity_names
                        WITH c, count(DISTINCT e) AS entity_count
                        ORDER BY entity_count DESC
                        LIMIT $limit
                        RETURN c.id AS id, c.title AS title, c.summary AS summary, c.url AS url, entity_count
                        """
                        
                        result = session.run(
                            cypher_query,
                            {"entity_names": entity_names, "limit": limit}
                        )
                        
                        for record in result:
                            results.append({
                                "id": record["id"],
                                "title": record["title"],
                                "summary": record["summary"],
                                "url": record["url"],
                                "relevance_score": record["entity_count"]
                            })
                except Exception as e:
                    logger.error(f"Neo4j search error: {e}", exc_info=True)
            
            # If Neo4j search failed or returned no results, fall back to SQLite
            if not results:
                logger.info("Falling back to SQLite search")
                
                # Search in SQLite using full-text search if available
                try:
                    with self.sqlite_db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Use full-text search if available
                        try:
                            cursor.execute(
                                """
                                SELECT id, title, summary, url
                                FROM content
                                WHERE content MATCH ?
                                LIMIT ?
                                """,
                                (query, limit)
                            )
                        except Exception:
                            # Fall back to basic LIKE search
                            search_term = f"%{query}%"
                            cursor.execute(
                                """
                                SELECT id, title, summary, url
                                FROM content
                                WHERE title LIKE ? OR summary LIKE ? OR content LIKE ?
                                LIMIT ?
                                """,
                                (search_term, search_term, search_term, limit)
                            )
                        
                        for row in cursor.fetchall():
                            results.append({
                                "id": row[0],
                                "title": row[1],
                                "summary": row[2],
                                "url": row[3],
                                "relevance_score": 1  # Default score for SQLite results
                            })
                except Exception as e:
                    logger.error(f"SQLite search error: {e}", exc_info=True)
            
            return {
                "status": "success", 
                "results": results,
                "query_entities": entity_names
            }
        except Exception as e:
            logger.error(f"Error in semantic search: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _handle_get_entity_context(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle get_entity_context messages.
        
        Args:
            message: The message containing the request
            correlation_id: Correlation ID for tracking the request
            
        Returns:
            Response with entity context information
        """
        try:
            entity_name = message.get("data", {}).get("entity_name", "")
            limit = message.get("data", {}).get("limit", 10)
            
            if not entity_name:
                return {"status": "error", "error": "No entity name provided"}
            
            context = []
            
            # Try to get context from Neo4j
            try:
                with self.neo4j_db.get_session() as session:
                    # Get content that mentions the entity
                    cypher_query = """
                    MATCH (c:Content)-[:MENTIONS]->(e:Entity {name: $entity_name})
                    RETURN c.id AS id, c.title AS title, c.summary AS summary, c.url AS url
                    LIMIT $limit
                    """
                    
                    result = session.run(
                        cypher_query,
                        {"entity_name": entity_name, "limit": limit}
                    )
                    
                    for record in result:
                        context.append({
                            "id": record["id"],
                            "title": record["title"],
                            "summary": record["summary"],
                            "url": record["url"]
                        })
                    
                    # Get related entities
                    cypher_query = """
                    MATCH (e1:Entity {name: $entity_name})<-[:MENTIONS]-(c:Content)-[:MENTIONS]->(e2:Entity)
                    WHERE e1 <> e2
                    WITH e2, count(c) AS common_content
                    ORDER BY common_content DESC
                    LIMIT $limit
                    RETURN e2.name AS name, e2.type AS type, common_content
                    """
                    
                    result = session.run(
                        cypher_query,
                        {"entity_name": entity_name, "limit": limit}
                    )
                    
                    related_entities = []
                    for record in result:
                        related_entities.append({
                            "name": record["name"],
                            "type": record["type"],
                            "common_content": record["common_content"]
                        })
            except Exception as e:
                logger.error(f"Neo4j entity context error: {e}", exc_info=True)
                related_entities = []
            
            # If Neo4j failed or returned no results, fall back to SQLite
            if not context:
                logger.info("Falling back to SQLite for entity context")
                
                try:
                    with self.sqlite_db.get_connection() as conn:
                        cursor = conn.cursor()
                        
                        # Get content that mentions the entity
                        cursor.execute(
                            """
                            SELECT c.id, c.title, c.summary, c.url
                            FROM content c
                            JOIN entity_mentions em ON c.id = em.content_id
                            JOIN entities e ON em.entity_id = e.id
                            WHERE e.name = ?
                            LIMIT ?
                            """,
                            (entity_name, limit)
                        )
                        
                        for row in cursor.fetchall():
                            context.append({
                                "id": row[0],
                                "title": row[1],
                                "summary": row[2],
                                "url": row[3]
                            })
                except Exception as e:
                    logger.error(f"SQLite entity context error: {e}", exc_info=True)
            
            return {
                "status": "success",
                "entity_name": entity_name,
                "context": context,
                "related_entities": related_entities if 'related_entities' in locals() else []
            }
        except Exception as e:
            logger.error(f"Error getting entity context: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def create_knowledge_graph(self, max_content_items: Optional[int] = None, 
                              source_filter: Optional[str] = None,
                              use_temp_db: bool = True) -> Dict[str, Any]:
        """Create a knowledge graph from the data in the database.
        
        Args:
            max_content_items: Maximum number of content items to process
            source_filter: Filter content by source
            use_temp_db: Whether to use the temporary database
            
        Returns:
            Results of the knowledge graph creation
        """
        start_time = time.time()
        
        try:
            # Determine which database to use
            db = self.temp_db if use_temp_db and self.temp_db else self.sqlite_db
            logger.info(f"Using {'temporary' if use_temp_db and self.temp_db else 'main'} database for knowledge graph creation")
            
            # If we're using the temp DB but haven't transferred data yet, do it now
            if use_temp_db and self.temp_db and self.temp_db != self.sqlite_db:
                transfer_results = self.transfer_data_to_temp_db(max_content_items, source_filter)
                logger.info(f"Transferred {transfer_results.get('content_count', 0)} content items and {transfer_results.get('entity_count', 0)} entities to temp DB")
            
            # Get content from the database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get content to process
                query = "SELECT id, title, summary, content FROM content"
                params = []
                
                if source_filter:
                    query += " WHERE source_id LIKE ?"
                    params.append(f"%{source_filter}%")
                
                if max_content_items:
                    query += f" LIMIT ?"
                    params.append(max_content_items)
                
                cursor.execute(query, params)
                content_items = cursor.fetchall()
                
                logger.info(f"Processing {len(content_items)} content items")
                
                # Process each content item
                content_nodes = []
                entity_nodes = {}  # Map of entity name to node ID
                entity_types = set()
                
                for content_item in tqdm(content_items, desc="Processing content"):
                    content_id, title, summary, content_text = content_item
                    
                    # Create content node in Neo4j
                    try:
                        content_node_id = self.neo4j_db.create_node(
                            label="Content",
                            properties={
                                "id": content_id,
                                "title": title or "",
                                "summary": summary or "",
                                "content": (content_text or "")[:1000]  # Limit content length
                            }
                        )
                        content_nodes.append(content_node_id)
                    except Exception as e:
                        logger.error(f"Error creating content node for {content_id}: {e}", exc_info=True)
                        continue
                    
                    # Get entities for this content
                    cursor.execute(
                        """
                        SELECT e.id, e.name, e.entity_type
                        FROM entities e
                        JOIN entity_mentions em ON e.id = em.entity_id
                        WHERE em.content_id = ?
                        """,
                        (content_id,)
                    )
                    
                    entities = cursor.fetchall()
                    
                    # If no entities found, try to extract them
                    if not entities:
                        logger.info(f"No entities found for content {content_id}, extracting now...")
                        
                        # Combine title and summary for better extraction
                        text_for_extraction = f"{title or ''}\n{summary or ''}\n{content_text or ''}"
                        
                        # Extract entities
                        extracted_entities = self._extract_entities_from_text(text_for_extraction)
                        
                        # Store extracted entities
                        for entity_type, entities_dict in extracted_entities.items():
                            entity_types.add(entity_type)
                            
                            for entity_name, entity_data in entities_dict.items():
                                # Skip empty entity names
                                if not entity_name.strip():
                                    continue
                                    
                                # Create entity in database
                                entity_id = str(uuid.uuid4())
                                
                                try:
                                    cursor.execute(
                                        """
                                        INSERT OR IGNORE INTO entities (id, name, entity_type, metadata)
                                        VALUES (?, ?, ?, ?)
                                        """,
                                        (
                                            entity_id,
                                            entity_name,
                                            entity_type,
                                            json.dumps(entity_data)
                                        )
                                    )
                                    
                                    # Create entity mention
                                    cursor.execute(
                                        """
                                        INSERT OR IGNORE INTO entity_mentions (id, entity_id, content_id, frequency)
                                        VALUES (?, ?, ?, ?)
                                        """,
                                        (
                                            str(uuid.uuid4()),
                                            entity_id,
                                            content_id,
                                            entity_data.get("frequency", 1)
                                        )
                                    )
                                    
                                    # Add to entities list
                                    entities.append((entity_id, entity_name, entity_type))
                                except Exception as e:
                                    logger.error(f"Error storing entity {entity_name}: {e}", exc_info=True)
                    
                    # Process entities
                    content_entity_nodes = []
                    
                    for entity_id, entity_name, entity_type in entities:
                        entity_types.add(entity_type)
                        
                        # Create entity node in Neo4j if it doesn't exist
                        if entity_name not in entity_nodes:
                            try:
                                entity_node_id = self.neo4j_db.create_node(
                                    label="Entity",
                                    properties={
                                        "id": entity_id,
                                        "name": entity_name,
                                        "type": entity_type
                                    }
                                )
                                entity_nodes[entity_name] = entity_node_id
                            except Exception as e:
                                logger.error(f"Error creating entity node for {entity_name}: {e}", exc_info=True)
                                continue
                        
                        # Create relationship between content and entity
                        try:
                            self.neo4j_db.create_relationship(
                                from_id=content_node_id,
                                to_id=entity_nodes[entity_name],
                                rel_type="MENTIONS",
                                properties={}
                            )
                            content_entity_nodes.append(entity_nodes[entity_name])
                        except Exception as e:
                            logger.error(f"Error creating MENTIONS relationship: {e}", exc_info=True)
                    
                    # Create relationships between entities that co-occur in this content
                    for i in range(len(content_entity_nodes)):
                        for j in range(i + 1, len(content_entity_nodes)):
                            try:
                                # Store relationship in temp DB
                                if db == self.temp_db:
                                    cursor.execute(
                                        """
                                        INSERT OR IGNORE INTO relationships (id, from_entity_id, to_entity_id, relationship_type, weight)
                                        VALUES (?, ?, ?, ?, ?)
                                        """,
                                        (
                                            str(uuid.uuid4()),
                                            content_entity_nodes[i],
                                            content_entity_nodes[j],
                                            "CO_OCCURS",
                                            1.0
                                        )
                                    )
                                
                                # Create relationship in Neo4j
                                self.neo4j_db.create_relationship(
                                    from_id=content_entity_nodes[i],
                                    to_id=content_entity_nodes[j],
                                    rel_type="CO_OCCURS",
                                    properties={"weight": 1.0}
                                )
                            except Exception as e:
                                logger.error(f"Error creating CO_OCCURS relationship: {e}", exc_info=True)
                
                # Commit changes
                conn.commit()
                
                # Create topic clusters
                try:
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
            
            return {
                "status": "error",
                "error": str(e)
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
                    topic_node_id = self.neo4j_db.create_node(
                        label="Topic",
                        properties={
                            "name": topic_name,
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
        Return ONLY a JSON object with the structure specified in the prompt, with no additional text.
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

    def _extract_entities_from_text(self, text: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dictionary of entity types to dictionaries of entity names to entity data
        """
        if not text:
            return {
                "Person": {}, "Organization": {}, "Location": {},
                "Concept": {}, "Technology": {}, "Paper": {}
            }
        
        # Limit text length to avoid token limits
        text = text[:10000]
        
        # Try LLM-based extraction first
        if self.llm_client:
            try:
                prompt = f"""
                Extract named entities from the following text. Identify people, organizations, locations, concepts, technologies, and research papers.
                
                Text:
                {text}
                
                For each entity, provide:
                1. The entity name
                2. The entity type (Person, Organization, Location, Concept, Technology, Paper)
                3. A brief description (2-3 words)
                4. Estimated frequency in the text (1-5)
                
                Return the results as a JSON object with the following structure:
                {{
                    "Person": {{
                        "Person Name": {{
                            "description": "brief description",
                            "frequency": number
                        }}
                    }},
                    "Organization": {{ ... }},
                    "Location": {{ ... }},
                    "Concept": {{ ... }},
                    "Technology": {{ ... }},
                    "Paper": {{ ... }}
                }}
                
                Only include entities that are clearly mentioned in the text. Do not invent entities.
                """
                
                system_prompt = """
                You are an entity extraction system. Your task is to identify named entities in text.
                Return ONLY a JSON object with the structure specified in the prompt, with no additional text.
                """
                
                response = self.llm_client.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Extract JSON from response
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.endswith("```"):
                    response = response[:-3]
                
                # Parse JSON
                entities = json.loads(response)
                
                # Validate structure
                valid_types = ["Person", "Organization", "Location", "Concept", "Technology", "Paper"]
                
                for entity_type in valid_types:
                    if entity_type not in entities:
                        entities[entity_type] = {}
                    elif not isinstance(entities[entity_type], dict):
                        entities[entity_type] = {}
                
                logger.info(f"LLM extraction found {sum(len(entities[t]) for t in valid_types)} entities")
                return entities
                
            except Exception as e:
                logger.error(f"Error in LLM-based entity extraction: {e}", exc_info=True)
                # Fall back to spaCy
        
        # Fall back to spaCy if available
        if self.has_spacy:
            try:
                entities = {
                    "Person": {}, "Organization": {}, "Location": {},
                    "Concept": {}, "Technology": {}, "Paper": {}
                }
                
                doc = self.nlp(text)
                
                # Map spaCy entity types to our types
                type_mapping = {
                    "PERSON": "Person",
                    "ORG": "Organization",
                    "GPE": "Location",
                    "LOC": "Location",
                    "PRODUCT": "Technology",
                    "WORK_OF_ART": "Paper"
                }
                
                # Extract entities
                for ent in doc.ents:
                    entity_type = type_mapping.get(ent.label_, "Concept")
                    entity_name = ent.text.strip()
                    
                    if not entity_name:
                        continue
                    
                    if entity_name not in entities[entity_type]:
                        entities[entity_type][entity_name] = {
                            "description": f"{entity_type.lower()}",
                            "frequency": 1
                        }
                    else:
                        entities[entity_type][entity_name]["frequency"] += 1
                
                logger.info(f"spaCy extraction found {sum(len(entities[t]) for t in entities)} entities")
                return entities
                
            except Exception as e:
                logger.error(f"Error in spaCy-based entity extraction: {e}", exc_info=True)
                # Fall back to regex
        
        # Last resort: regex-based extraction
        try:
            entities = {
                "Person": {}, "Organization": {}, "Location": {},
                "Concept": {}, "Technology": {}, "Paper": {}
            }
            
            # Extract capitalized phrases as potential entities
            capitalized_phrases = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)*\b', text)
            
            for phrase in capitalized_phrases:
                # Skip single letters and common words
                if len(phrase) <= 1 or phrase.lower() in ['the', 'a', 'an', 'of', 'in', 'on', 'at', 'by', 'for']:
                    continue
                
                # Determine entity type based on heuristics
                if len(phrase.split()) >= 3 and any(word in phrase.lower() for word in ['study', 'research', 'paper', 'analysis']):
                    entity_type = "Paper"
                elif any(word in phrase.lower() for word in ['university', 'institute', 'corporation', 'inc', 'ltd', 'company']):
                    entity_type = "Organization"
                elif any(word in phrase.lower() for word in ['algorithm', 'system', 'framework', 'platform', 'language', 'model']):
                    entity_type = "Technology"
                elif len(phrase.split()) <= 2:
                    entity_type = "Concept"
                else:
                    entity_type = "Concept"
                
                if phrase not in entities[entity_type]:
                    entities[entity_type][phrase] = {
                        "description": f"{entity_type.lower()}",
                        "frequency": 1
                    }
                else:
                    entities[entity_type][phrase]["frequency"] += 1
            
            logger.info(f"Regex extraction found {sum(len(entities[t]) for t in entities)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Error in regex-based entity extraction: {e}", exc_info=True)
            
            # Return empty result if all methods fail
            return {
                "Person": {}, "Organization": {}, "Location": {},
                "Concept": {}, "Technology": {}, "Paper": {}
            }
