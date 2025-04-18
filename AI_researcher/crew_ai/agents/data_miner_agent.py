import time
import datetime
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import concurrent.futures
from tqdm import tqdm
import uuid

from crew_ai.agents.base_agent import BaseAgent
from crew_ai.utils.database import SQLiteDB
from crew_ai.utils.content_moderation import ContentModerator
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.utils.messaging import MessageBroker
from crew_ai.config.config import Config, LLMProvider
from arxiv import Client, Search, SortCriterion, SortOrder

class DataMinerAgent(BaseAgent):
    """Agent for mining data from various sources."""
    
    def __init__(self, agent_id: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None,
                 db: Optional[SQLiteDB] = None,
                 content_moderator: Optional[ContentModerator] = None,
                 max_results: Optional[int] = None):
        """Initialize the DataMinerAgent."""
        super().__init__(agent_id, llm_client, llm_provider, message_broker)
        
        self.db = db or SQLiteDB()
        self.content_moderator = content_moderator or ContentModerator()
        self.max_results = max_results or Config.DUCKDUCKGO_MAX_RESULTS
        self.ddgs = DDGS()
        
        # Register message handlers
        self.register_handler("mine_data", self._handle_mine_data)
        self.register_handler("scrape_url", self._handle_scrape_url)
        self.register_handler("get_stats", self._handle_get_stats)
    
    def _handle_mine_data(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle mine_data messages."""
        query = message.get("data", {}).get("query")
        sources = message.get("data", {}).get("sources", ["reddit", "medium", "linkedin", "arxiv"])
        max_results = message.get("data", {}).get("max_results", self.max_results)
        
        if not query:
            return {"status": "error", "error": "Query is required"}
        
        results = self.mine_data(query, sources, max_results)
        return {"status": "success", "results": results}
    
    def _handle_scrape_url(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle scrape_url messages."""
        url = message.get("data", {}).get("url")
        
        if not url:
            return {"status": "error", "error": "URL is required"}
        
        content, metadata = self.scrape_url(url)
        
        if not content:
            return {"status": "error", "error": "Failed to scrape URL"}
        
        return {
            "status": "success", 
            "content": content[:500] + "..." if len(content) > 500 else content,
            "metadata": metadata
        }
    
    def _handle_get_stats(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle get_stats messages."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get source stats
            cursor.execute("SELECT source_type, COUNT(*) FROM sources GROUP BY source_type")
            source_stats = {row["source_type"]: row[1] for row in cursor.fetchall()}
            
            # Get content stats
            cursor.execute("SELECT COUNT(*) FROM content")
            content_count = cursor.fetchone()[0]
            
            # Get entity stats
            cursor.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
            entity_stats = {row["entity_type"]: row[1] for row in cursor.fetchall()}
            
            # Get quality stats
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN quality_score < 0.3 THEN 'low'
                        WHEN quality_score < 0.7 THEN 'medium'
                        ELSE 'high'
                    END as quality_level,
                    COUNT(*) 
                FROM content 
                GROUP BY quality_level
            """)
            quality_stats = {row["quality_level"]: row[1] for row in cursor.fetchall()}
            
            return {
                "status": "success",
                "source_stats": source_stats,
                "content_count": content_count,
                "entity_stats": entity_stats,
                "quality_stats": quality_stats
            }
    
    def mine_data(self, query: str, sources: List[str] = None, 
                 max_results: int = None) -> Dict[str, Any]:
        """Mine data from various sources."""
        sources = sources or ["reddit", "medium", "linkedin", "arxiv"]
        max_results = max_results or self.max_results
        
        results = {
            "total_sources": 0,
            "successful_sources": 0,
            "failed_sources": 0,
            "filtered_sources": 0,
            "source_breakdown": {}
        }
        
        # Calculate results per source
        results_per_source = max(1, max_results // len(sources))
        
        for source in sources:
            if source == "arxiv":
                results["source_breakdown"][source] = self.mine_arxiv(query, results_per_source)
            else:
                print(f"Mining data from {source}...")
                source_results = self._mine_from_source(query, source, results_per_source)
                
                results["total_sources"] += source_results["total"]
                results["successful_sources"] += source_results["successful"]
                results["failed_sources"] += source_results["failed"]
                results["filtered_sources"] += source_results["filtered"]
                results["source_breakdown"][source] = source_results
        
        return results
    
    def mine_arxiv(self, query: str, max_results: int = 50) -> List[Dict]:
        """Mine data from arXiv."""
        try:
            print(f"Mining data from arXiv for query: {query}")
            
            # Use direct arXiv API instead of DuckDuckGo
            client = Client()
            
            # Create a search object
            search = Search(
                query=query,
                max_results=max_results,
                sort_by=SortCriterion.Relevance,
                sort_order=SortOrder.Descending
            )
            
            # Get the results
            results = []
            for result in client.results(search):
                content = {
                    "title": result.title,
                    "summary": result.summary,
                    "authors": ", ".join(author.name for author in result.authors),
                    "published": str(result.published),
                    "url": result.pdf_url,
                    "source": "arxiv"
                }
                results.append(content)
                
                # Store in database
                try:
                    self.db.store_content(content)
                except Exception as e:
                    print(f"Error storing content: {e}")
                
            print(f"Found {len(results)} results from arXiv")
            
            # If no results found, create a dummy result to avoid empty vocabulary error
            if not results:
                dummy_content = {
                    "title": f"No results found for: {query}",
                    "summary": f"The search for '{query}' did not yield any results from arXiv. This is a placeholder entry to ensure the knowledge graph has at least one document to process.",
                    "authors": "System",
                    "published": "2025-04-18",
                    "url": "https://arxiv.org",
                    "source": "arxiv"
                }
                results.append(dummy_content)
                try:
                    self.db.store_content(dummy_content)
                except Exception as e:
                    print(f"Error storing dummy content: {e}")
                print("Added dummy content to prevent empty vocabulary error")
                
            return results
            
        except Exception as e:
            print(f"Error mining from arXiv: {e}")
            # Create a fallback result
            fallback_content = {
                "title": f"Error searching for: {query}",
                "summary": f"An error occurred while searching for '{query}' on arXiv: {str(e)}. This is a placeholder entry to ensure the knowledge graph has at least one document to process.",
                "authors": "System",
                "published": "2025-04-18",
                "url": "https://arxiv.org",
                "source": "arxiv"
            }
            try:
                self.db.store_content(fallback_content)
            except Exception as e:
                print(f"Error storing fallback content: {e}")
            return [fallback_content]
    
    def _mine_from_source(self, query: str, source: str, max_results: int) -> Dict[str, Any]:
        """Mine data from a specific source."""
        source_results = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "filtered": 0
        }
        
        # Construct source-specific query
        source_query = f"{query} site:{self._get_source_domain(source)}"
        
        try:
            # Search for URLs
            search_results = list(self.ddgs.text(source_query, max_results=max_results))
            source_results["total"] = len(search_results)
            
            if not search_results:
                return source_results
            
            # Process search results in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for result in search_results:
                    url = result.get("href")
                    title = result.get("title", "")
                    snippet = result.get("body", "")
                    
                    futures.append(
                        executor.submit(
                            self._process_search_result,
                            url, title, snippet, source
                        )
                    )
                
                # Process results as they complete
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc=f"Processing {source}"):
                    success, filtered = future.result()
                    
                    if success:
                        source_results["successful"] += 1
                    else:
                        source_results["failed"] += 1
                    
                    if filtered:
                        source_results["filtered"] += 1
        
        except Exception as e:
            print(f"Error mining from {source}: {e}")
            source_results["failed"] = source_results["total"]
        
        return source_results
    
    def _get_source_domain(self, source: str) -> str:
        """Get the domain for a source."""
        source_domains = {
            "reddit": "reddit.com",
            "medium": "medium.com",
            "linkedin": "linkedin.com",
            "arxiv": "arxiv.org"
        }
        
        return source_domains.get(source.lower(), source)
    
    def _process_search_result(self, url: str, title: str, snippet: str, source: str) -> Tuple[bool, bool]:
        """Process a search result."""
        try:
            # Skip if URL is empty
            if not url:
                return False, False
            
            # Check if URL already exists in database
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM sources WHERE url = ?", (url,))
                existing = cursor.fetchone()
                
                if existing:
                    # URL already processed
                    return True, False
            
            # Scrape the URL
            content, metadata = self.scrape_url(url)
            
            if not content:
                return False, False
            
            # Filter content
            filtered_content, quality_score, is_harmful = self.content_moderator.filter_content(content)
            
            if is_harmful or not filtered_content:
                # Content was filtered out
                return True, True
            
            # Insert source into database
            timestamp = datetime.datetime.now().isoformat()
            source_id = self.db.insert_source(
                url=url,
                title=title or metadata.get("title", ""),
                source_type=source,
                timestamp=timestamp,
                metadata=metadata
            )
            
            # Insert content into database
            self.db.insert_content(
                source_id=source_id,
                content_text=filtered_content,
                content_type="text",
                quality_score=quality_score
            )
            
            return True, False
        
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return False, False
    
    def scrape_url(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """Scrape content from a URL."""
        try:
            # Send request with appropriate headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Extract content based on source type
            domain = urlparse(url).netloc
            
            if "reddit.com" in domain:
                content = self._extract_reddit_content(soup)
            elif "medium.com" in domain:
                content = self._extract_medium_content(soup)
            elif "linkedin.com" in domain:
                content = self._extract_linkedin_content(soup)
            elif "arxiv.org" in domain:
                content = self._extract_arxiv_content(soup)
            else:
                content = self._extract_generic_content(soup)
            
            # Clean content
            cleaned_content = self._clean_content(content)
            
            return cleaned_content, metadata
        
        except Exception as e:
            print(f"Error scraping URL {url}: {e}")
            return "", {}
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.text.strip()
        
        # Extract meta description
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag:
            metadata["description"] = description_tag.get("content", "").strip()
        
        # Extract meta keywords
        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag:
            metadata["keywords"] = keywords_tag.get("content", "").strip()
        
        # Extract author
        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag:
            metadata["author"] = author_tag.get("content", "").strip()
        
        # Extract publication date
        date_tag = soup.find("meta", attrs={"name": "date"})
        if date_tag:
            metadata["publication_date"] = date_tag.get("content", "").strip()
        
        return metadata
    
    def _extract_reddit_content(self, soup: BeautifulSoup) -> str:
        """Extract content from Reddit."""
        content = []
        
        # Extract post title
        post_title = soup.find("h1")
        if post_title:
            content.append(post_title.text.strip())
        
        # Extract post content
        post_content = soup.find("div", attrs={"data-test-id": "post-content"})
        if post_content:
            content.append(post_content.text.strip())
        
        # Extract comments
        comments = soup.find_all("div", class_=re.compile("Comment__body"))
        for comment in comments[:20]:  # Limit to top 20 comments
            content.append(comment.text.strip())
        
        return "\n\n".join(filter(None, content))
    
    def _extract_medium_content(self, soup: BeautifulSoup) -> str:
        """Extract content from Medium."""
        content = []
        
        # Extract article title
        article_title = soup.find("h1")
        if article_title:
            content.append(article_title.text.strip())
        
        # Extract article content
        article_sections = soup.find_all(["p", "h2", "h3", "blockquote", "pre"])
        for section in article_sections:
            content.append(section.text.strip())
        
        return "\n\n".join(filter(None, content))
    
    def _extract_linkedin_content(self, soup: BeautifulSoup) -> str:
        """Extract content from LinkedIn."""
        content = []
        
        # Extract post content
        post_content = soup.find("div", class_=re.compile("share-update-card__description"))
        if post_content:
            content.append(post_content.text.strip())
        
        # Extract article content if it's an article
        article_sections = soup.find_all(["p", "h2", "h3"])
        for section in article_sections:
            content.append(section.text.strip())
        
        # Extract comments
        comments = soup.find_all("div", class_=re.compile("comment-body"))
        for comment in comments[:10]:  # Limit to top 10 comments
            content.append(comment.text.strip())
        
        return "\n\n".join(filter(None, content))
    
    def _extract_arxiv_content(self, soup: BeautifulSoup) -> str:
        """Extract content from arXiv."""
        content = []
        
        # Extract paper title
        paper_title = soup.find("h1", class_="title")
        if paper_title:
            content.append(paper_title.text.replace("Title:", "").strip())
        
        # Extract authors
        authors = soup.find("div", class_="authors")
        if authors:
            content.append(authors.text.replace("Authors:", "").strip())
        
        # Extract abstract
        abstract = soup.find("blockquote", class_="abstract")
        if abstract:
            content.append(abstract.text.replace("Abstract:", "").strip())
        
        return "\n\n".join(filter(None, content))
    
    def _extract_generic_content(self, soup: BeautifulSoup) -> str:
        """Extract content from a generic webpage."""
        content = []
        
        # Extract title
        title = soup.find("title")
        if title:
            content.append(title.text.strip())
        
        # Extract main content
        main_content = soup.find("main")
        if main_content:
            content.append(main_content.text.strip())
        else:
            # Try to find article content
            article = soup.find("article")
            if article:
                content.append(article.text.strip())
            else:
                # Extract all paragraphs
                paragraphs = soup.find_all("p")
                for p in paragraphs:
                    content.append(p.text.strip())
        
        return "\n\n".join(filter(None, content))
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove URLs
        content = re.sub(r'https?://\S+', '', content)
        
        # Remove email addresses
        content = re.sub(r'\S+@\S+', '', content)
        
        # Remove special characters
        content = re.sub(r'[^\w\s.,;:!?\'"-]', ' ', content)
        
        # Remove extra whitespace again
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def store_content(self, content: Dict[str, Any]) -> None:
        """Store content in the database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Generate a unique ID for the content
                content_id = str(uuid.uuid4())
                source_id = str(uuid.uuid4())
                
                # First check if the tables exist with the right schema
                cursor.execute("PRAGMA table_info(sources)")
                source_columns = [col[1] for col in cursor.fetchall()]
                
                if 'source_type' in source_columns and 'name' not in source_columns:
                    # Old schema - need to update
                    cursor.execute("ALTER TABLE sources ADD COLUMN name TEXT")
                    conn.commit()
                
                # Insert into sources table
                if 'source_type' in source_columns:
                    # Old schema
                    cursor.execute(
                        "INSERT OR IGNORE INTO sources (id, source_type, url, name) VALUES (?, ?, ?, ?)",
                        (source_id, content.get("source", "unknown"), content.get("url", ""), content.get("source", "unknown"))
                    )
                else:
                    # New schema
                    cursor.execute(
                        "INSERT OR IGNORE INTO sources (id, name, url) VALUES (?, ?, ?)",
                        (source_id, content.get("source", "unknown"), content.get("url", ""))
                    )
                
                # Check content table schema
                cursor.execute("PRAGMA table_info(content)")
                content_columns = [col[1] for col in cursor.fetchall()]
                
                # Insert into content table
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO content 
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
                
        except Exception as e:
            print(f"Error storing content: {e}")
            # Try to create tables if they don't exist
            try:
                self.db._create_tables()
            except:
                pass
    
    def run(self, query: str, sources: List[str] = None, max_results: int = None):
        """Run the data mining process."""
        print(f"Starting data mining for query: {query}")
        results = self.mine_data(query, sources, max_results)
        
        print("Data mining completed:")
        print(f"- Total sources: {results['total_sources']}")
        print(f"- Successful sources: {results['successful_sources']}")
        print(f"- Failed sources: {results['failed_sources']}")
        print(f"- Filtered sources: {results['filtered_sources']}")
        
        for source, stats in results["source_breakdown"].items():
            print(f"- {source}: {stats['successful']}/{stats['total']} successful")
        
        return results
