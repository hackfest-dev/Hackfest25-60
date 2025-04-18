"""SQLite Agent for handling database operations."""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import uuid
from datetime import datetime
from crew_ai.config.config import Config
from crew_ai.agents.base_agent import BaseAgent


class SQLiteAgent(BaseAgent):
    """Agent responsible for SQLite database operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the SQLite agent."""
        super().__init__(name="SQLiteAgent", description="Agent responsible for SQLite database operations")
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
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                content_id = content.get("id") or str(uuid.uuid4())
                
                # If source_id is not provided, create a new source
                if not source_id:
                    source_id = str(uuid.uuid4())
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
        except Exception as e:
            print(f"Error storing content: {e}")
            return ""
    
    def store_entity(self, name: str, entity_type: str, metadata: Dict[str, Any] = None) -> str:
        """Store an entity in the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                entity_id = str(uuid.uuid4())
                
                cursor.execute(
                    """
                    INSERT INTO entities 
                    (id, name, entity_type, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        entity_id,
                        name,
                        entity_type,
                        json.dumps(metadata or {})
                    )
                )
                
                conn.commit()
                return entity_id
        except Exception as e:
            print(f"Error storing entity: {e}")
            return ""
    
    def link_entity_to_content(self, entity_id: str, content_id: str) -> str:
        """Link an entity to content."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                mention_id = str(uuid.uuid4())
                
                cursor.execute(
                    """
                    INSERT INTO entity_mentions 
                    (id, entity_id, content_id)
                    VALUES (?, ?, ?)
                    """,
                    (
                        mention_id,
                        entity_id,
                        content_id
                    )
                )
                
                conn.commit()
                return mention_id
        except Exception as e:
            print(f"Error linking entity to content: {e}")
            return ""
    
    def get_entities_by_type(self, entity_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get entities by type."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT id, name, entity_type, metadata
            FROM entities
            WHERE entity_type = ?
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (entity_type,))
            
            results = []
            for row in cursor.fetchall():
                entity = {
                    "id": row[0],
                    "name": row[1],
                    "entity_type": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {}
                }
                results.append(entity)
            
            return results
    
    def get_content_for_entity(self, entity_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get content associated with an entity."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = """
            SELECT c.id, c.title, c.summary, c.content, c.authors, c.published_date, c.url, c.metadata,
                   s.id as source_id, s.name as source_name, s.url as source_url
            FROM content c
            JOIN sources s ON c.source_id = s.id
            JOIN entity_mentions em ON c.id = em.content_id
            WHERE em.entity_id = ?
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (entity_id,))
            
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
    
    def search_content(self, query: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search content by keyword."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            
            query = """
            SELECT c.id, c.title, c.summary, c.content, c.authors, c.published_date, c.url, c.metadata,
                   s.id as source_id, s.name as source_name, s.url as source_url
            FROM content c
            JOIN sources s ON c.source_id = s.id
            WHERE c.title LIKE ? OR c.summary LIKE ? OR c.content LIKE ?
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, (search_term, search_term, search_term))
            
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
    
    def execute_task(self, task: str, **kwargs) -> Dict[str, Any]:
        """Execute a task based on the task name."""
        if task == "store_content":
            content = kwargs.get("content", {})
            source_id = kwargs.get("source_id")
            content_id = self.store_content(content, source_id)
            return {"content_id": content_id}
        
        elif task == "get_content_items":
            limit = kwargs.get("limit")
            content_items = self.get_content_items(limit)
            return {"content_items": content_items}
        
        elif task == "store_entity":
            name = kwargs.get("name", "")
            entity_type = kwargs.get("entity_type", "")
            metadata = kwargs.get("metadata", {})
            entity_id = self.store_entity(name, entity_type, metadata)
            return {"entity_id": entity_id}
        
        elif task == "link_entity_to_content":
            entity_id = kwargs.get("entity_id", "")
            content_id = kwargs.get("content_id", "")
            mention_id = self.link_entity_to_content(entity_id, content_id)
            return {"mention_id": mention_id}
        
        elif task == "get_entities_by_type":
            entity_type = kwargs.get("entity_type", "")
            limit = kwargs.get("limit")
            entities = self.get_entities_by_type(entity_type, limit)
            return {"entities": entities}
        
        elif task == "get_content_for_entity":
            entity_id = kwargs.get("entity_id", "")
            limit = kwargs.get("limit")
            content_items = self.get_content_for_entity(entity_id, limit)
            return {"content_items": content_items}
        
        elif task == "search_content":
            query = kwargs.get("query", "")
            limit = kwargs.get("limit")
            content_items = self.search_content(query, limit)
            return {"content_items": content_items}
        
        else:
            return {"error": f"Unknown task: {task}"}
