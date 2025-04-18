import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import json
from neo4j import GraphDatabase
from crew_ai.config.config import Config

class SQLiteDB:
    """SQLite database wrapper."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite database wrapper."""
        self.db_path = db_path or Config.SQLITE_DB_PATH or "data.db"
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Drop existing tables if they exist
            cursor.execute("DROP TABLE IF EXISTS entity_mentions")
            cursor.execute("DROP TABLE IF EXISTS entities")
            cursor.execute("DROP TABLE IF EXISTS content")
            cursor.execute("DROP TABLE IF EXISTS sources")
            
            # Create sources table
            cursor.execute('''
            CREATE TABLE sources (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create content table
            cursor.execute('''
            CREATE TABLE content (
                id TEXT PRIMARY KEY,
                source_id TEXT,
                title TEXT,
                summary TEXT,
                content TEXT,
                authors TEXT,
                published_date TEXT,
                url TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
            ''')
            
            # Create entities table
            cursor.execute('''
            CREATE TABLE entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                entity_type TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create entity_mentions table
            cursor.execute('''
            CREATE TABLE entity_mentions (
                id TEXT PRIMARY KEY,
                entity_id TEXT,
                content_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                FOREIGN KEY (content_id) REFERENCES content(id)
            )
            ''')
            
            conn.commit()
    
    def get_content_items(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get content items from the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT c.id, c.title, c.summary, c.content, c.authors, c.published_date, c.url, c.metadata,
                   s.id as source_id, s.name as source_name, s.url as source_url
            FROM content c
            JOIN sources s ON c.source_id = s.id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                content_item = {
                    "id": row[0],
                    "title": row[1],
                    "summary": row[2],
                    "content": row[3],
                    "authors": row[4],
                    "published_date": row[5],
                    "url": row[6],
                    "metadata": json.loads(row[7]) if row[7] else {},
                    "source": {
                        "id": row[8],
                        "name": row[9],
                        "url": row[10]
                    }
                }
                results.append(content_item)
            
            return results
    
    def store_content(self, content: Dict[str, Any], source_id: Optional[str] = None) -> str:
        """Store content in the database."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            content_id = content.get("id") or os.urandom(16).hex()
            
            # If source_id is not provided, create a new source
            if not source_id:
                source_id = os.urandom(16).hex()
                source_name = content.get("source", "unknown")
                source_url = content.get("url", "")
                
                cursor.execute(
                    "INSERT INTO sources (id, name, url) VALUES (?, ?, ?)",
                    (source_id, source_name, source_url)
                )
            
            # Insert content
            cursor.execute(
                """
                INSERT INTO content 
                (id, source_id, title, summary, content, authors, published_date, url, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    content_id,
                    source_id,
                    content.get("title", ""),
                    content.get("summary", ""),
                    content.get("content", content.get("summary", "")),
                    content.get("authors", ""),
                    content.get("published", ""),
                    content.get("url", ""),
                    json.dumps(content)
                )
            )
            
            conn.commit()
            return content_id

class Neo4jDB:
    """Neo4j database wrapper."""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """Initialize Neo4j database wrapper."""
        self.uri = uri or Config.NEO4J_URI
        self.user = user or Config.NEO4J_USER
        self.password = password or Config.NEO4J_PASSWORD
        self.driver = None
        
        # Print connection details for debugging
        print(f"Connecting to Neo4j at {self.uri} with user {self.user}")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test the connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    print("Successfully connected to Neo4j")
                else:
                    print("Connected to Neo4j but test query failed")
        except Exception as e:
            print(f"Error connecting to Neo4j: {e}")
            # Create in-memory fallback
            self._create_fallback_db()
    
    def _create_fallback_db(self):
        """Create in-memory fallback database."""
        print("Creating in-memory fallback for Neo4j")
        self.is_fallback = True
        self.nodes = {}
        self.relationships = []
    
    def close(self):
        """Close Neo4j connection."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            return
            
        if self.driver:
            self.driver.close()
    
    def run_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run a Cypher query."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            print(f"Fallback mode: Query would be: {query}")
            return []
            
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                return [record.data() for record in result]
        except Exception as e:
            print(f"Error running Neo4j query: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            return []
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Optional[str]:
        """Create a node in the graph database."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            node_id = properties.get('id', str(len(self.nodes) + 1))
            self.nodes[node_id] = {
                'label': label,
                'properties': properties
            }
            return node_id
            
        query = f"""
        CREATE (n:{label} $properties)
        RETURN id(n) as node_id
        """
        try:
            result = self.run_query(query, {"properties": properties})
            return result[0]["node_id"] if result else None
        except Exception as e:
            print(f"Error creating node: {e}")
            return None
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           relationship_type: str, properties: Dict[str, Any] = None) -> Optional[str]:
        """Create a relationship between two nodes."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            rel_id = str(len(self.relationships) + 1)
            self.relationships.append({
                'start': start_node_id,
                'end': end_node_id,
                'type': relationship_type,
                'properties': properties or {}
            })
            return rel_id
            
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $start_id AND id(b) = $end_id
        CREATE (a)-[r:{relationship_type} $properties]->(b)
        RETURN id(r) as relationship_id
        """
        try:
            result = self.run_query(query, {
                "start_id": start_node_id,
                "end_id": end_node_id,
                "properties": properties or {}
            })
            return result[0]["relationship_id"] if result else None
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return None
    
    def create_entity_node(self, entity_type: str, name: str, properties: Dict[str, Any] = None) -> str:
        """Create a node in the knowledge graph."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            node_id = str(len(self.nodes) + 1)
            self.nodes[node_id] = {
                'label': 'Entity',
                'properties': {
                    'name': name,
                    'entity_type': entity_type,
                    **(properties or {})
                }
            }
            return node_id
            
        # Check if the entity already exists
        query = """
        MATCH (e:Entity {name: $name, entity_type: $entity_type})
        RETURN id(e) as node_id
        """
        
        try:
            result = self.run_query(query, {"name": name, "entity_type": entity_type})
            
            if result and result[0]["node_id"]:
                return result[0]["node_id"]
            
            # Create a new entity node
            props = {"name": name, "entity_type": entity_type}
            if properties:
                props.update(properties)
                
            return self.create_node("Entity", props)
        except Exception as e:
            print(f"Error creating entity node: {e}")
            return None
    
    def create_content_node(self, content_id: str, title: str, summary: str, url: str, source: str) -> str:
        """Create a content node in the knowledge graph."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            node_id = str(len(self.nodes) + 1)
            self.nodes[node_id] = {
                'label': 'Content',
                'properties': {
                    'content_id': content_id,
                    'title': title,
                    'summary': summary,
                    'url': url,
                    'source': source
                }
            }
            return node_id
            
        # Check if the content already exists
        query = """
        MATCH (c:Content {content_id: $content_id})
        RETURN id(c) as node_id
        """
        
        try:
            result = self.run_query(query, {"content_id": content_id})
            
            if result and result[0]["node_id"]:
                return result[0]["node_id"]
            
            # Create a new content node
            return self.create_node("Content", {
                "content_id": content_id,
                "title": title,
                "summary": summary,
                "url": url,
                "source": source
            })
        except Exception as e:
            print(f"Error creating content node: {e}")
            return None
    
    def create_relationship(self, content_id: str, entity_name: str, relationship_type: str) -> str:
        """Create a relationship between a content node and an entity node."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            rel_id = str(len(self.relationships) + 1)
            self.relationships.append({
                'start': content_id,
                'end': entity_name,
                'type': relationship_type
            })
            return rel_id
            
        # Find the content node
        content_query = """
        MATCH (c:Content {content_id: $content_id})
        RETURN id(c) as node_id
        """
        
        # Find the entity node
        entity_query = """
        MATCH (e:Entity {name: $entity_name})
        RETURN id(e) as node_id
        """
        
        try:
            content_result = self.run_query(content_query, {"content_id": content_id})
            entity_result = self.run_query(entity_query, {"entity_name": entity_name})
            
            if not content_result or not entity_result:
                return None
                
            content_node_id = content_result[0]["node_id"]
            entity_node_id = entity_result[0]["node_id"]
            
            # Create relationship
            relationship_query = f"""
            MATCH (c:Content), (e:Entity)
            WHERE id(c) = $content_id AND id(e) = $entity_id
            CREATE (c)-[r:{relationship_type}]->(e)
            RETURN id(r) as relationship_id
            """
            
            result = self.run_query(relationship_query, {
                "content_id": content_node_id,
                "entity_id": entity_node_id
            })
            
            return result[0]["relationship_id"] if result else None
        except Exception as e:
            print(f"Error creating relationship: {e}")
            return None
    
    def find_similar_entities(self, embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Find entities similar to the given embedding."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            print("Fallback mode: Would search for similar entities")
            return []
            
        # Use standard Neo4j vector similarity instead of GDS
        query = """
        MATCH (n:Entity) 
        WHERE n.embedding IS NOT NULL 
        WITH n, apoc.text.distance(n.embedding, $embedding) AS score 
        ORDER BY score ASC 
        LIMIT $limit 
        RETURN n.name AS name, n.entity_type AS entity_type, score, id(n) AS node_id
        """
        
        # If APOC is not available, use a simpler query
        try:
            result = self.run_query(query, {"embedding": embedding, "limit": limit})
            if not result:
                # Fallback to a simpler query without similarity
                query = """
                MATCH (n:Entity) 
                RETURN n.name AS name, n.entity_type AS entity_type, 0.5 AS score, id(n) AS node_id
                LIMIT $limit
                """
                result = self.run_query(query, {"limit": limit})
            return result
        except Exception as e:
            print(f"Error finding similar entities: {e}")
            # Fallback to a simpler query without similarity
            try:
                query = """
                MATCH (n:Entity) 
                RETURN n.name AS name, n.entity_type AS entity_type, 0.5 AS score, id(n) AS node_id
                LIMIT $limit
                """
                return self.run_query(query, {"limit": limit})
            except:
                return []
    
    def semantic_search(self, entity_type: str, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search on the knowledge graph."""
        # This assumes you have a vector index set up in Neo4j
        if hasattr(self, 'is_fallback') and self.is_fallback:
            print("Fallback mode: Would perform semantic search")
            return []
            
        try:
            # Try with vector similarity
            query = """
            MATCH (n:Entity)
            WHERE n.entity_type = $entity_type AND n.embedding IS NOT NULL
            WITH n, apoc.text.distance(n.embedding, $embedding) AS score
            ORDER BY score ASC
            LIMIT $limit
            RETURN n.name AS name, n.entity_type AS entity_type, score
            """
            
            result = self.run_query(query, {
                "entity_type": entity_type,
                "embedding": query_embedding,
                "limit": limit
            })
            
            if result:
                return result
                
            # Fallback to simple search
            query = """
            MATCH (n:Entity)
            WHERE n.entity_type = $entity_type
            RETURN n.name AS name, n.entity_type AS entity_type, 0.5 AS score
            LIMIT $limit
            """
            
            return self.run_query(query, {
                "entity_type": entity_type,
                "limit": limit
            })
        except Exception as e:
            print(f"Error performing semantic search: {e}")
            return []
    
    def get_entity_context(self, entity_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get context for an entity from the knowledge graph."""
        if hasattr(self, 'is_fallback') and self.is_fallback:
            print("Fallback mode: Would get entity context")
            return []
            
        query = """
        MATCH (e:Entity {name: $entity_name})<-[r]-(c:Content)
        RETURN c.title AS title, c.summary AS summary, c.url AS url, c.source AS source
        LIMIT $limit
        """
        
        try:
            return self.run_query(query, {"entity_name": entity_name, "limit": limit})
        except Exception as e:
            print(f"Error getting entity context: {e}")
            return []
