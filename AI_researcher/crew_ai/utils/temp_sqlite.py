"""Temporary SQLite Database Utility for AgentSus2.

This module provides a temporary SQLite database implementation
that ensures proper data storage and retrieval for the knowledge graph creation.
"""

import os
import json
import sqlite3
import uuid
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TempSQLiteDB')

class TempSQLiteDB:
    """Temporary SQLite database wrapper for AgentSus2."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize temporary SQLite database wrapper.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path or "temp_data.db"
        self._create_tables()
        logger.info(f"Initialized temporary SQLite database at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection.
        
        Yields:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create sources table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                id TEXT PRIMARY KEY,
                name TEXT,
                url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create content table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS content (
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
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT,
                entity_type TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create entity_mentions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS entity_mentions (
                id TEXT PRIMARY KEY,
                entity_id TEXT,
                content_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES entities(id),
                FOREIGN KEY (content_id) REFERENCES content(id)
            )
            ''')
            
            # Create relationships table (new)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_entity_id TEXT,
                target_entity_id TEXT,
                relationship_type TEXT,
                weight REAL,
                properties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entity_id) REFERENCES entities(id),
                FOREIGN KEY (target_entity_id) REFERENCES entities(id)
            )
            ''')
            
            conn.commit()
            logger.info("Database tables created successfully")
    
    def store_source(self, name: str, url: str) -> str:
        """Store a source in the database.
        
        Args:
            name: Name of the source
            url: URL of the source
            
        Returns:
            ID of the created source
        """
        source_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sources (id, name, url) VALUES (?, ?, ?)",
                (source_id, name, url)
            )
            conn.commit()
        
        logger.info(f"Stored source: {name} with ID {source_id}")
        return source_id
    
    def store_content(self, content: Dict[str, Any], source_id: Optional[str] = None) -> str:
        """Store content in the database.
        
        Args:
            content: Content data
            source_id: ID of the source
            
        Returns:
            ID of the created content
        """
        try:
            content_id = str(uuid.uuid4())
            
            # Create source if not provided
            if not source_id:
                source_id = self.store_source(
                    content.get("source", "unknown"),
                    content.get("url", "")
                )
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
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
                        content.get("published_date", ""),
                        content.get("url", ""),
                        json.dumps(content)
                    )
                )
                conn.commit()
            
            logger.info(f"Stored content: {content.get('title', 'Untitled')} with ID {content_id}")
            return content_id
            
        except Exception as e:
            logger.error(f"Error storing content: {e}")
            raise
    
    def store_entity(self, name: str, entity_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store an entity in the database.
        
        Args:
            name: Name of the entity
            entity_type: Type of the entity
            metadata: Additional metadata
            
        Returns:
            ID of the created entity
        """
        entity_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if entity already exists
            cursor.execute(
                "SELECT id FROM entities WHERE name = ? AND entity_type = ?",
                (name, entity_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Create new entity
            cursor.execute(
                "INSERT INTO entities (id, name, entity_type, metadata) VALUES (?, ?, ?, ?)",
                (entity_id, name, entity_type, json.dumps(metadata or {}))
            )
            conn.commit()
        
        logger.info(f"Stored entity: {name} ({entity_type}) with ID {entity_id}")
        return entity_id
    
    def link_entity_to_content(self, entity_id: str, content_id: str) -> str:
        """Link an entity to content.
        
        Args:
            entity_id: ID of the entity
            content_id: ID of the content
            
        Returns:
            ID of the created mention
        """
        mention_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if mention already exists
            cursor.execute(
                "SELECT id FROM entity_mentions WHERE entity_id = ? AND content_id = ?",
                (entity_id, content_id)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Create new mention
            cursor.execute(
                "INSERT INTO entity_mentions (id, entity_id, content_id) VALUES (?, ?, ?)",
                (mention_id, entity_id, content_id)
            )
            conn.commit()
        
        logger.info(f"Linked entity {entity_id} to content {content_id}")
        return mention_id
    
    def create_relationship(self, source_entity_id: str, target_entity_id: str, 
                           relationship_type: str, weight: float = 1.0,
                           properties: Dict[str, Any] = None) -> str:
        """Create a relationship between two entities.
        
        Args:
            source_entity_id: ID of the source entity
            target_entity_id: ID of the target entity
            relationship_type: Type of the relationship
            weight: Weight of the relationship
            properties: Additional properties
            
        Returns:
            ID of the created relationship
        """
        relationship_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if relationship already exists
            cursor.execute(
                """
                SELECT id FROM relationships 
                WHERE source_entity_id = ? AND target_entity_id = ? AND relationship_type = ?
                """,
                (source_entity_id, target_entity_id, relationship_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                return existing[0]
            
            # Create new relationship
            cursor.execute(
                """
                INSERT INTO relationships 
                (id, source_entity_id, target_entity_id, relationship_type, weight, properties)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    relationship_id, 
                    source_entity_id, 
                    target_entity_id, 
                    relationship_type, 
                    weight,
                    json.dumps(properties or {})
                )
            )
            conn.commit()
        
        logger.info(f"Created relationship: {relationship_type} between {source_entity_id} and {target_entity_id}")
        return relationship_id
    
    def get_all_content(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all content from the database.
        
        Args:
            limit: Maximum number of content items to retrieve
            
        Returns:
            List of content items
        """
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
                results.append(content_item)
            
            logger.info(f"Retrieved {len(results)} content items")
            return results
    
    def get_all_entities(self, entity_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all entities from the database.
        
        Args:
            entity_type: Filter by entity type
            limit: Maximum number of entities to retrieve
            
        Returns:
            List of entities
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, name, entity_type, metadata FROM entities"
            params = []
            
            if entity_type:
                query += " WHERE entity_type = ?"
                params.append(entity_type)
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row[3]) if row[3] else {}
                entity = {
                    "id": row[0],
                    "name": row[1],
                    "entity_type": row[2],
                    "metadata": metadata
                }
                results.append(entity)
            
            logger.info(f"Retrieved {len(results)} entities")
            return results
    
    def get_all_relationships(self, relationship_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all relationships from the database.
        
        Args:
            relationship_type: Filter by relationship type
            limit: Maximum number of relationships to retrieve
            
        Returns:
            List of relationships
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT r.id, r.relationship_type, r.weight, r.properties,
                   e1.id as source_id, e1.name as source_name, e1.entity_type as source_type,
                   e2.id as target_id, e2.name as target_name, e2.entity_type as target_type
            FROM relationships r
            JOIN entities e1 ON r.source_entity_id = e1.id
            JOIN entities e2 ON r.target_entity_id = e2.id
            """
            params = []
            
            if relationship_type:
                query += " WHERE r.relationship_type = ?"
                params.append(relationship_type)
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                properties = json.loads(row[3]) if row[3] else {}
                relationship = {
                    "id": row[0],
                    "relationship_type": row[1],
                    "weight": row[2],
                    "properties": properties,
                    "source": {
                        "id": row[4],
                        "name": row[5],
                        "entity_type": row[6]
                    },
                    "target": {
                        "id": row[7],
                        "name": row[8],
                        "entity_type": row[9]
                    }
                }
                results.append(relationship)
            
            logger.info(f"Retrieved {len(results)} relationships")
            return results
