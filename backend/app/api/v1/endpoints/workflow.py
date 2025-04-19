import os
import json
import uuid
from tqdm import tqdm
import pandas as pd
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools.base import ToolException
from langchain.chains import LLMChain
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.agents import AgentExecutor, create_react_agent, create_openai_functions_agent, Tool, AgentType
from langchain.agents import initialize_agent
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from .tools import research_tools
from langchain.agents import tool as tool_decorator
import time  # Add this import at the top if not already present
try:
    import psutil
except ImportError:
    print("Installing psutil for memory monitoring...")
    import subprocess
    subprocess.check_call(["pip", "install", "psutil"])
    import psutil

import gc
import re

llm = ChatGroq(api_key="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", model="llama-3.3-70b-versatile")
# llm = ChatGroq(api_key="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", model="llama-3.3-70b-versatile")

# Setup vector database - Make embeddings optional
USE_EMBEDDINGS = False  # Set to False for much faster processing without embeddings
SEARCH_QUERIES_LIMIT = 5  # Reduce from 90 to 10 (adjust as needed for speed vs. completeness)

if USE_EMBEDDINGS:
    try:
        # Only create embeddings if enabled
        embedding_function = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},  # Force CPU usage
            encode_kwargs={"batch_size": 8}  # Smaller batch size for CPU
        )
        
        # Create a directory for persisting the vector database
        PERSIST_DIRECTORY = "research_db"
        os.makedirs(PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize the vector database with CPU-friendly settings
        try:
            vectordb = Chroma(
                persist_directory=PERSIST_DIRECTORY, 
                embedding_function=embedding_function,
                collection_metadata={"hnsw:space": "cosine"}  # CPU-friendly distance metric
            )
            print(f"Vector database initialized at {PERSIST_DIRECTORY} (CPU mode)")
        except Exception as e:
            print(f"Error initializing vector database: {str(e)}")
            print("Falling back to in-memory vector store (CPU mode)")
            vectordb = Chroma(
                embedding_function=embedding_function,
                collection_metadata={"hnsw:space": "cosine"}  # CPU-friendly distance metric
            )
    except Exception as e:
        print(f"Error setting up embeddings: {str(e)}")
        USE_EMBEDDINGS = False  # Disable if setup failed
        vectordb = None
else:
    print("Embeddings disabled for faster processing - using simple file-based storage")
    vectordb = None

# Text splitter for chunking documents - optimized for CPU
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Smaller chunks for CPU
    chunk_overlap=50,  # Reduced overlap for CPU
    separators=["\n\n", "\n", ". ", " ", ""],
)

class ResearchWorkflow:
    def __init__(self, topic, llm=llm, tools=research_tools, max_iterations=30, db=vectordb):
        self.topic = topic
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations
        self.db = db
        self.session_id = str(uuid.uuid4())
        self.research_log = []
        
        # Configuration settings
        self.use_embeddings = USE_EMBEDDINGS
        self.search_limit = SEARCH_QUERIES_LIMIT
        self.cpu_only = True
        self.batch_size = 2  # Very small batches for CPU-only
        
        # Remove all directory creation operations
        
        # Convert multi-input tools to single-input
        self.prepare_tools()
        
    def prepare_tools(self):
        """Convert multi-input tools to single-input format compatible with ZeroShotAgent"""
        compatible_tools = []
        
        for tool in self.tools:
            try:
                if tool.name == "reddit_search":
                    # Create a simplified wrapper for reddit search
                    def create_reddit_wrapper(reddit_tool):
                        @tool_decorator("Search Reddit for information")
                        def search_reddit(query: str) -> str:
                            """Search Reddit for the given query and return relevant posts."""
                            try:
                                return reddit_tool.run({"query": query, "sort": "relevance", "time_filter": "month"})
                            except Exception as e:
                                return f"Error searching Reddit: {str(e)}"
                        return search_reddit
                    
                    compatible_tools.append(create_reddit_wrapper(tool))
                elif hasattr(tool, "run") and callable(tool.run):
                    # Create a simplified version of the tool with a single input
                    def create_simplified_wrapper(t):
                        tool_name = getattr(t, "name", t.__class__.__name__)
                        tool_description = getattr(t, "description", f"Tool for {tool_name}")
                        
                        @tool_decorator(tool_description)
                        def simplified_tool(query: str) -> str:
                            """Run tool with a single query parameter."""
                            try:
                                # First try running with the query directly
                                return t.run(query)
                            except Exception as e1:
                                try:
                                    # Then try with the query as a parameter dict
                                    return t.run({"query": query})
                                except Exception as e2:
                                    return f"Error using {tool_name}: {str(e2)}"
                        
                        # Set the name to match the original tool
                        simplified_tool.name = tool_name
                        return simplified_tool
                    
                    compatible_tools.append(create_simplified_wrapper(tool))
                else:
                    # Tool doesn't have a run method, skip it
                    print(f"Skipping tool {getattr(tool, 'name', tool.__class__.__name__)} - no run method")
            except Exception as e:
                print(f"Error processing tool: {str(e)}")
                # Skip this tool
        
        if not compatible_tools:
            print("Warning: No compatible tools found. Using a simple web search tool as fallback.")
            @tool_decorator("Search the web")
            def web_search_fallback(query: str) -> str:
                """Search the web for information about the query."""
                try:
                    return f"Web search results for: {query}\n\nPlease check online sources for this information."
                except Exception as e:
                    return f"Error searching the web: {str(e)}"
            
            compatible_tools.append(web_search_fallback)
        
        self.tools = compatible_tools
        print(f"Prepared {len(self.tools)} tools for research")
        
    def save_to_vector_db(self, content, metadata=None):
        """Save content to vector database with CPU optimizations"""
        # Skip all file operations
        if not self.use_embeddings or self.db is None:
            return 0
        
        # If embeddings are enabled, proceed with vector DB
        if not content or not isinstance(content, str) or content.strip() == "":
            return 0
            
        if not metadata:
            metadata = {"source": "research", "timestamp": datetime.now().isoformat()}
        
        try:
            # Split text into smaller chunks for CPU processing
            docs = text_splitter.create_documents([content], [metadata])
            
            # Add documents to vector store in smaller batches to reduce memory usage
            if len(docs) > self.batch_size:
                for i in range(0, len(docs), self.batch_size):
                    batch = docs[i:i+self.batch_size]
                    self.db.add_documents(batch)
                    gc.collect()
            else:
                self.db.add_documents(docs)
            
            return len(docs)
        except Exception:
            return 0
    
    def plan_research(self):
        """Create a research plan based on the topic"""
        print("✓ Planning research")
        plan_prompt = ChatPromptTemplate.from_template("""
        You are a world-class researcher planning a focused research project on: {topic}
        
        Create a concise research plan including:
        1. 5-7 specific research questions we should answer
        2. For each question, 2-3 search queries that would help answer it
        3. Specific data sources or tools that would be most valuable for each question (arxiv, wikipedia, web search, etc.)
        
        Your plan should be designed to gather approximately {search_limit} search results across different sources.
        
        Make your research questions focused on the most important aspects of the topic.
        
        Your response MUST be valid JSON that follows this structure EXACTLY:
        {{
            "research_questions": [
                {{
                    "question": "The specific research question",
                    "search_queries": ["query1", "query2"],
                    "data_sources": ["tool1", "tool2"]
                }}
            ]
        }}
        
        IMPORTANT: Ensure your response is ONLY valid JSON with no additional text, markdown formatting, or explanations.
        """)
        
        try:
            chain = plan_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"topic": self.topic, "search_limit": self.search_limit})
            
            # Parse the JSON result
            try:
                # First try parsing as JSON
                plan = json.loads(result)
                return plan
            except json.JSONDecodeError:
                # Try to extract JSON portion if it exists
                try:
                    # Sometimes the model returns markdown-wrapped JSON, try to extract it
                    import re
                    
                    # First pattern: look for JSON inside markdown code blocks
                    json_pattern = r'```(?:json)?\s*(.*?)```'
                    matches = re.findall(json_pattern, result, re.DOTALL)
                    
                    if matches:
                        # Try each potential JSON match
                        for match in matches:
                            try:
                                plan = json.loads(match.strip())
                                return plan
                            except:
                                continue
                    
                    # Second pattern: try to find anything that looks like a complete JSON object
                    json_pattern = r'(\{[\s\S]*?\})'
                    matches = re.findall(json_pattern, result)
                    
                    if matches:
                        # Try each potential JSON match
                        for match in matches:
                            try:
                                plan = json.loads(match.strip())
                                if "research_questions" in plan:
                                    return plan
                            except:
                                continue
                
                    # If we couldn't extract JSON, create a simple fallback plan
                    return self._create_fallback_plan()
                except:
                    # Create fallback plan
                    return self._create_fallback_plan()
        except:
            return self._create_fallback_plan()
    
    def _create_fallback_plan(self):
        """Create a simple fallback research plan when the LLM fails"""
        topic_words = self.topic.split()
        
        # Create some basic research questions based on the topic
        questions = [
            f"What is the current state of {self.topic}?",
            f"What are the key challenges in {self.topic}?",
            f"How has {self.topic} evolved over time?",
            f"What are the future trends in {self.topic}?",
            f"Who are the key experts or organizations in {self.topic}?",
        ]
        
        # Add some topic-specific questions if possible
        if len(topic_words) >= 2:
            questions.append(f"How does {topic_words[0]} relate to {topic_words[-1]}?")
            questions.append(f"What are the ethical considerations in {self.topic}?")
            questions.append(f"What methodologies are used in {self.topic} research?")
        
        # Create a simple plan with these questions
        fallback_plan = {
            "research_questions": []
        }
        
        for q in questions:
            # Create search queries from the question
            search_queries = [
                q,  # The question itself
                f"latest research {q.lower().replace('?', '')}",
                f"examples of {q.lower().replace('?', '')}",
                f"{self.topic} case studies",
            ]
            
            fallback_plan["research_questions"].append({
                "question": q,
                "search_queries": search_queries,
                "data_sources": ["web_search", "wikipedia", "arxiv"]
            })
        
        return fallback_plan
    
    def generate_outline(self):
        """Generate the research outline based on the topic"""
        print("✓ Generating outline")
        
        outline_prompt = ChatPromptTemplate.from_template("""
        You are an expert academic researcher tasked with creating a detailed outline for a research paper on: {topic}
        
        Create a comprehensive outline with 5-7 main sections that would form a complete research paper.
        
        For each section:
        1. Provide a descriptive title
        2. List 3-5 key points that should be addressed in that section
        3. Consider both theoretical foundations and practical applications
        
        Format your response as JSON with the following structure:
        [
            {{
                "section_title": "Clear descriptive title for this section",
                "key_points": ["Key point 1", "Key point 2", "Key point 3"]
            }}
        ]
        
        Ensure the outline follows a logical flow and covers the topic comprehensively from introduction to conclusion.
        """)
        
        try:
            # Execute the chain
            chain = outline_prompt | self.llm | StrOutputParser()
            result = chain.invoke({"topic": self.topic})
            
            # Parse the result
            try:
                # Try direct parsing
                outline = json.loads(result)
                return outline
            except json.JSONDecodeError:
                # Try to extract JSON from markdown
                try:
                    import re
                    json_pattern = r'```(?:json)?\s*(.*?)```'
                    matches = re.findall(json_pattern, result, re.DOTALL)
                    
                    if matches:
                        for match in matches:
                            try:
                                outline = json.loads(match.strip())
                                return outline
                            except:
                                continue
                
                    # Fallback to default outline
                    default_outline = self._create_default_outline()
                    return default_outline
                except:
                    default_outline = self._create_default_outline()
                    return default_outline
        except:
            default_outline = self._create_default_outline()
            return default_outline
    
    def _create_default_outline(self):
        """Create a default outline structure"""
        return [
            {
                "section_title": "Introduction",
                "key_points": [
                    f"Definition and scope of {self.topic}",
                    "Historical background and evolution",
                    "Significance and current relevance"
                ]
            },
            {
                "section_title": "Literature Review",
                "key_points": [
                    "Key theories and frameworks",
                    "Major research findings to date",
                    "Gaps in existing research"
                ]
            },
            {
                "section_title": "Methodology",
                "key_points": [
                    "Research approach",
                    "Data collection methods",
                    "Analysis techniques"
                ]
            },
            {
                "section_title": f"Current Applications of {self.topic}",
                "key_points": [
                    "Industry implementations",
                    "Case studies",
                    "Success metrics and outcomes"
                ]
            },
            {
                "section_title": "Challenges and Limitations",
                "key_points": [
                    "Technical constraints",
                    "Ethical considerations",
                    "Implementation barriers"
                ]
            },
            {
                "section_title": "Future Directions",
                "key_points": [
                    "Emerging trends",
                    "Research opportunities",
                    "Predicted developments"
                ]
            },
            {
                "section_title": "Conclusion",
                "key_points": [
                    "Summary of key findings",
                    "Implications for theory and practice",
                    "Final thoughts and recommendations"
                ]
            }
        ]
    
    def execute_research(self):
        """Execute the research based on the topic and generate a report"""
        print("✓ Executing research")
        
        # Generate the outline
        self.outline = self.generate_outline()
        
        # Initialize sections
        self.sections = []
        
        # For each section in the outline, generate content
        for i, section in enumerate(self.outline):
            try:
                section_title = section.get("section_title", "Untitled Section")
                
                # Generate the section content
                section_result = self.generate_section(section)
                
                # Add to sections list in the format expected by generate_report
                if section_result:
                    section_type = self._determine_section_type(section_title)
                    
                    self.sections.append({
                        "index": i,
                        "parent_id": None,
                        "section_title": section_result.get("section_title", "Untitled Section"),
                        "section_type": section_type,
                        "content": section_result.get("content", "No content generated")
                    })
                else:
                    self.sections.append({
                        "index": i,
                        "parent_id": None,
                        "section_title": section_title,
                        "section_type": "general",
                        "content": "Error: No content could be generated for this section."
                    })
            except Exception as e:
                self.sections.append({
                    "index": i,
                    "parent_id": None,
                    "section_title": section.get("section_title", f"Section {i+1}"),
                    "section_type": "general",
                    "content": f"Error: {str(e)}"
                })
            
            # Add a short delay between sections to prevent rate limiting
            if i < len(self.outline) - 1:
                time.sleep(2)
        
        # Create document structure for backward compatibility
        document = {
            "title": self.topic,
            "sections": []
        }
        
        # Convert sections to old format for backward compatibility
        for section in self.sections:
            document["sections"].append({
                "section_title": section["section_title"],
                "content": section["content"]
            })
        
        return document
    
    def plan_report(self):
        """Plan the structure of the final report"""
        print("✓ Planning report structure")
        if not self.use_embeddings:
            # Without embeddings, use a simpler approach to plan the report
            
            # Create a default fallback plan in case all else fails
            fallback_plan = {
                "title": f"Research Report on {self.topic}",
                "sections": [
                    {
                        "section_title": "Executive Summary",
                        "subsections": [],
                        "key_points": ["Summary of key findings"]
                    },
                    {
                        "section_title": "Introduction",
                        "subsections": ["Background", "Problem Statement"],
                        "key_points": ["Introduce the topic", "Explain the importance"]
                    },
                    {
                        "section_title": "Methodology",
                        "subsections": ["Research Approach"],
                        "key_points": ["How the research was conducted"]
                    },
                    {
                        "section_title": "Results and Analysis",
                        "subsections": ["Key Findings"],
                        "key_points": ["Main research findings"]
                    },
                    {
                        "section_title": "Discussion",
                        "subsections": ["Implications"],
                        "key_points": ["Interpretation of findings"]
                    },
                    {
                        "section_title": "Conclusions",
                        "subsections": ["Recommendations"],
                        "key_points": ["Main conclusions", "Next steps"]
                    },
                    {
                        "section_title": "References",
                        "subsections": [],
                        "key_points": ["Sources cited in the report"]
                    }
                ]
            }
            
            # Create a research summary to include in the prompt
            research_summary = f"Research on {self.topic}."
            
            # Create a simpler plan prompt that explicitly asks for valid JSON
            plan_prompt = """
            You are an expert report planner. Based on our research on {topic}, create a detailed
            outline for an academic-quality report.
            
            Research summary:
            {research_summary}
            
            Include:
            1. Executive summary
            2. Introduction with clear problem statement
            3. 5-8 main sections with subsections
            4. Methodology section describing research approach
            5. Results and analysis
            6. Discussion of findings
            7. Conclusions and recommendations
            8. References section
            
            Your response MUST be ONLY valid JSON without ANY additional text, explanation, or markdown. 
            It must strictly follow this structure:
            {{
                "title": "Report title",
                "sections": [
                    {{
                        "section_title": "Section title",
                        "subsections": ["Subsection 1", "Subsection 2"],
                        "key_points": ["Key point to address 1", "Key point to address 2"]
                    }}
                ]
            }}
            
            IMPORTANT: Return ONLY the valid JSON object, nothing before or after. Do not include ```json``` or any other formatting markers.
            Make sure your JSON is properly formatted with correct quotes, commas, brackets, and braces.
            """
            
            try:
                # First clear memory
                gc.collect()
                
                # Try to get a response from the LLM
                response = self.llm.invoke(plan_prompt.format(
                    topic=self.topic, 
                    research_summary=research_summary
                ))
                
                # Various attempts to extract valid JSON
                try:
                    # First attempt - try to parse directly
                    plan = json.loads(response)
                except json.JSONDecodeError:
                    # Second attempt - try to extract JSON from text with different patterns
                    import re
                    
                    # Look for JSON code blocks
                    json_pattern = r'```(?:json)?\s*(.*?)```'
                    matches = re.findall(json_pattern, response, re.DOTALL)
                    
                    if matches:
                        for match in matches:
                            try:
                                plan = json.loads(match.strip())
                                break
                            except json.JSONDecodeError:
                                continue
                    else:
                        # Try finding braced JSON objects
                        json_pattern = r'(\{[\s\S]*\})'
                        matches = re.findall(json_pattern, response)
                        
                        if matches:
                            for match in matches:
                                try:
                                    plan_candidate = json.loads(match.strip())
                                    # Validate it has the required structure
                                    if "title" in plan_candidate and "sections" in plan_candidate:
                                        plan = plan_candidate
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                    # If we still don't have valid JSON, use fallback
                    if 'plan' not in locals():
                        plan = fallback_plan
                
                # Validate the plan's structure
                if "title" not in plan or "sections" not in plan or not isinstance(plan["sections"], list):
                    plan = fallback_plan
                
                return plan
                
            except Exception:
                return fallback_plan
        else:
            # With embeddings, use RAG as before
            # Query the vector DB for insights to help planning
            retriever = self.db.as_retriever(search_kwargs={"k": 10})  # Reduced from 15 for CPU efficiency
            
            report_plan_prompt = ChatPromptTemplate.from_template("""
            You are an expert report planner. Based on our comprehensive research on {topic}, and the information provided below,
            create a detailed outline for an academic-quality report.
            
            Research context:
            {context}
            
            Include:
            1. Executive summary
            2. Introduction with clear problem statement
            3. 5-8 main sections with subsections
            4. Methodology section describing research approach
            5. Results and analysis
            6. Discussion of findings
            7. Conclusions and recommendations
            8. References section (using academic citation format)
            
            Format your response as JSON with the following structure:
            {{
                "title": "Report title",
                "sections": [
                    {{
                        "section_title": "Section title",
                        "subsections": ["Subsection 1", "Subsection 2"],
                        "key_points": ["Key point to address 1", "Key point to address 2"]
                    }}
                ]
            }}
            """)
            
            # Create RAG chain with memory optimization
            try:
                # First clear memory
                gc.collect()
                
                # Create and run RAG chain with CPU optimization
                rag_chain = (
                    {"context": retriever, "topic": RunnablePassthrough()}
                    | report_plan_prompt
                    | self.llm
                    | StrOutputParser()
                )
                
                result = rag_chain.invoke(self.topic)
                
                # Force garbage collection after RAG operation
                gc.collect()
                
                # Parse the JSON result
                try:
                    plan = json.loads(result)
                    return plan
                except json.JSONDecodeError:
                    # Fallback if JSON parsing fails
                    return {"error": "Failed to parse report plan", "raw_plan": result}
            except Exception:
                return {"error": "Error generating report plan", "details": "Failed to generate plan"}
    
    def generate_section(self, section_info):
        """Generate a section using either embeddings RAG or file-based approach"""
        # Clear memory before starting
        gc.collect()
        
        if not self.use_embeddings:
            # Without embeddings, use a simpler approach
            section_title = section_info.get("section_title", "")
            key_points = section_info.get("key_points", [])
            section_type = section_info.get("section_type", self._determine_section_type(section_title))
            ref_offset = section_info.get("ref_offset", 0)
            section_index = section_info.get("section_index", 0)
            total_sections = section_info.get("total_sections", 0)
            parent_section = section_info.get("parent_section", "")
            
            # Create section-specific guidance
            section_guidance = ""
            if section_type == "introduction":
                section_guidance = """
                For this Introduction section:
                1. Begin with a clear problem statement about the topic
                2. Provide background context and significance of the topic
                3. Include a concise literature review highlighting key previous work
                4. Clearly state the research objectives or questions
                5. End with an outline of the paper structure
                
                Use 2-3 citations max for key foundational works.
                """
            elif section_type == "methodology":
                section_guidance = """
                For this Methodology section:
                1. Describe the research design and approach in detail
                2. Explain data collection methods and sources
                3. Detail analytical frameworks or models used
                4. Discuss data processing procedures
                5. Address limitations of the methodology
                
                Use past tense when describing methods employed. Use 1-2 citations for methodological precedents.
                """
            elif section_type == "results":
                section_guidance = """
                For this Results section:
                1. Present findings objectively without interpretation
                2. Organize results logically following the methodology
                3. Use tables and figures to present complex data
                4. Highlight key statistics and findings
                5. Maintain a neutral tone with factual reporting
                
                Use minimal citations in this section, focus on presenting your own findings.
                """
            elif section_type == "discussion":
                section_guidance = """
                For this Discussion section:
                1. Interpret results in context of existing literature
                2. Compare findings with previous research
                3. Explain unexpected results or contradictions
                4. Discuss theoretical and practical implications
                5. Address limitations of the study
                
                Use 2-3 targeted citations when comparing your findings to existing research.
                """
            elif section_type == "conclusion":
                section_guidance = """
                For this Conclusion section:
                1. Summarize key findings without introducing new information
                2. Restate the significance of the research
                3. Address broader implications for the field
                4. Suggest specific future research directions
                5. End with an impactful statement about the topic's importance
                
                Use minimal or no citations in this section as it focuses on summarizing your own work.
                """
            elif section_type == "references":
                section_guidance = """
                For this References section:
                1. Format all references consistently in academic citation style
                2. Include only sources cited in the text
                3. Organize references alphabetically by author surname
                4. Ensure each reference contains complete information (authors, year, title, source, etc.)
                
                Follow strict academic citation format.
                """
            elif section_type == "subsection":
                section_guidance = f"""
                For this subsection of the {parent_section} section:
                1. Focus specifically on '{section_title}' aspects
                2. Maintain consistency with the main section's theme
                3. Provide specific details and examples
                4. Connect ideas back to the main section
                5. Use clear transitions between paragraphs
                
                Use 1-2 citations max to support key points. This subsection should be shorter than the main section.
                """
            else:
                section_guidance = """
                For this section:
                1. Begin with a clear topic sentence introducing the section focus
                2. Organize content logically with clear paragraph structure
                3. Support claims with evidence but use citations sparingly
                4. Include relevant examples or case studies
                5. Conclude with a summary or transition to the next section
                
                Maintain academic tone and proper scholarly structure while using citations judiciously.
                """
            
            # Create a prompt focused on proper academic paper writing
            section_prompt = f"""
            You are writing content for section {section_index} of {total_sections} in a formal academic research paper on {self.topic}.
            
            IMPORTANT: This is NOT a standalone paper. You are writing ONLY the "{section_title}" section of a larger research paper.
            
            The section you are writing is: "{section_title}"
            
            Key points to address in this section:
            {", ".join(key_points)}
            
            {section_guidance}
            
            ACADEMIC PAPER SECTION GUIDELINES TO FOLLOW STRICTLY:
            1. Remember this is ONLY ONE SECTION of a larger research paper, not a complete paper itself
            2. Maintain formal academic language and tone throughout
            3. Follow proper paragraph structure with clear topic sentences
            4. Use citations SPARINGLY - only 1-3 citations in this entire section
            5. Format tables properly with captions above them (Table X: Description)
            6. Format figures with captions below them (Figure X: Description)
            7. Use consistent citation format - numerical references in square brackets [1]
            8. DO NOT include a References section at the end - references will be collected and compiled centrally
            9. Avoid first-person pronouns and maintain scholarly objectivity
            10. Follow a consistent narrative that flows with other sections of the paper
            
            DO NOT:
            - Include the section heading/title (it will be added separately)
            - Include excessive citations - use at most 3 citations in the entire section
            - Include a References section at the end
            - Write as if this is a complete paper (it is ONE SECTION of a larger paper)
            - Repeat content or context that would be covered in other sections
            
            IMPORTANT FORMATTING INSTRUCTIONS:
            - For tables, use proper Markdown table format:
              | Column 1 | Column 2 | Column 3 |
              |----------|----------|----------|
              | Data 1   | Data 2   | Data 3   |
              Table X: Description of table
            
            - For in-text citations, use numerical format at the END of sentences: According to recent research, AI ethics is a growing concern [1].
            
            - For figures, clearly indicate with:
              [Figure X: Description of figure]
            
            Write approximately 600-800 words of substantive, well-structured content that would meet the standards of a scholarly journal article section.
            """
            
            try:
                # Generate with the LLM with retry logic for rate limits
                max_retries = 3
                retry_count = 0
                retry_delay = 10  # seconds
                
                while retry_count < max_retries:
                    try:
                        # Get the content as plain text
                        response = self.llm.invoke(section_prompt)
                        # Extract the string content from the response
                        if hasattr(response, 'content'):
                            content = response.content  # For ChatMessages
                        elif isinstance(response, str):
                            content = response  # Already a string
                        else:
                            content = str(response)  # Convert to string as fallback
                        
                        break  # Success, exit the retry loop
                    except Exception as e:
                        error_str = str(e)
                        if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                            retry_count += 1
                            if retry_count < max_retries:
                                retry_time = retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                                print(f"Rate limit hit. Retrying in {retry_time} seconds...")
                                time.sleep(retry_time)
                            else:
                                content = f"[Rate limit reached. This section ({section_title}) needs to be regenerated.]"
                        else:
                            # Other error, not rate limit related
                            content = f"[Error generating content: {str(e)}. This section ({section_title}) needs to be regenerated.]"
                            break
                
                # Post-process content to improve formatting
                content = self._format_section_content(content, section_type)
                
                # Make sure there's no references section
                if section_type != "references":
                    # Remove any reference section that might be at the end
                    if "References:" in content:
                        content = content.split("References:")[0].strip()
                    if "Bibliography:" in content:
                        content = content.split("Bibliography:")[0].strip()
                
                # Force memory cleanup after generation
                gc.collect()
                
                return {
                    "section_title": section_title,
                    "content": content
                }
            except Exception as e:
                return {
                    "section_title": section_title,
                    "content": f"Error generating content: {str(e)}\n\nPlease regenerate this section.",
                    "error": str(e)
                }
        else:
            # With embeddings, use RAG as before
            # Use fewer documents for retrieval on CPU
            retriever = self.db.as_retriever(search_kwargs={"k": 8})  # Reduced from 10
            
            # Create more engaging, researcher-like prompt (similar to non-embedding version)
            section_title = section_info.get("section_title", "")
            key_points = section_info.get("key_points", [])
            section_type = section_info.get("section_type", self._determine_section_type(section_title))
            section_index = section_info.get("section_index", 0)
            total_sections = section_info.get("total_sections", 0)
            
            # Create the RAG chain setup
            try:
                # Prepare prompt with same researcher-focused approach
                section_prompt = ChatPromptTemplate.from_template("""
                You are writing a single section for an academic research paper on {topic}.
                
                IMPORTANT: This is NOT a standalone paper. You are writing ONLY the "{section_title}" section (Section {section_index} of {total_sections}) of a larger research paper.
                
                The section you are writing is: {section_title}
                
                Key aspects to address in this section:
                {key_points}
                
                Research information available:
                {context}
                
                ACADEMIC SECTION GUIDELINES TO FOLLOW:
                1. Remember this is ONLY ONE SECTION of a larger research paper, not a complete paper itself
                2. Maintain formal academic language and scholarly tone throughout
                3. Follow proper paragraph structure with clear topic sentences
                4. Use citations SPARINGLY - only 1-3 citations in this entire section
                5. Support claims with evidence but avoid excessive citations
                6. Place tables and figures only where directly relevant
                7. Maintain objectivity and avoid first-person pronouns
                
                IMPORTANT: 
                - DO NOT include the section title in your response - it will be added separately
                - DO NOT include a References section at the end
                - DO NOT write as if this is a standalone paper
                - Use only numerical citation format [1], [2], etc.
                - Length should be approximately 600-800 words
                
                Write substantive, well-structured content that would meet the standards of an academic journal section.
                """)
                
                # Create RAG chain for section generation with CPU optimization
                rag_chain = (
                    {
                        "context": retriever, 
                        "topic": lambda _: self.topic,
                        "section_title": lambda _: section_title,
                        "key_points": lambda _: ", ".join(key_points),
                        "section_index": lambda _: section_index,
                        "total_sections": lambda _: total_sections
                    }
                    | section_prompt
                    | self.llm
                )
                
                # Generate the section with retry logic for rate limits
                max_retries = 3
                retry_count = 0
                retry_delay = 10  # seconds
                
                while retry_count < max_retries:
                    try:
                        # Generate and extract as plain text
                        response = rag_chain.invoke({})
                        # Extract the string content from the response
                        if hasattr(response, 'content'):
                            content = response.content  # For ChatMessages
                        elif isinstance(response, str):
                            content = response  # Already a string
                        else:
                            content = str(response)  # Convert to string as fallback
                            
                        break  # Success, exit the retry loop
                    except Exception as e:
                        error_str = str(e)
                        if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                            retry_count += 1
                            if retry_count < max_retries:
                                retry_time = retry_delay * (2 ** (retry_count - 1))  # Exponential backoff
                                print(f"Rate limit hit. Retrying in {retry_time} seconds...")
                                time.sleep(retry_time)
                            else:
                                content = f"[Rate limit reached. This section ({section_title}) needs to be regenerated.]"
                        else:
                            # Other error, not rate limit related
                            content = f"[Error generating content: {str(e)}. This section ({section_title}) needs to be regenerated.]"
                            break
                
                # Format content
                content = self._format_section_content(content, section_type)
                
                # Make sure there's no references section
                if section_type != "references":
                    # Remove any reference section that might be at the end
                    if "References:" in content:
                        content = content.split("References:")[0].strip()
                    if "Bibliography:" in content:
                        content = content.split("Bibliography:")[0].strip()
                
                # Force memory cleanup after generation
                gc.collect()
                
                return {
                    "section_title": section_title,
                    "content": content
                }
            except Exception as e:
                return {
                    "section_title": section_title,
                    "content": f"Error generating content: {str(e)}\n\nPlease regenerate this section.",
                    "error": str(e)
                }
    
    def _format_section_content(self, content, section_type):
        """Format section content to ensure proper academic paper structure"""
        # Remove any section title that might have been generated
        lines = content.split('\n')
        if lines and (lines[0].startswith('# ') or lines[0].startswith('## ') or lines[0].startswith('### ')):
            lines = lines[1:]
            content = '\n'.join(lines)
        
        # For references section, ensure proper formatting
        if section_type == "references":
            # Make sure references are properly formatted
            ref_pattern = r'\[\d+\]'
            if not re.search(ref_pattern, content):
                # Convert any reference list to proper format
                ref_lines = []
                for line in content.split('\n'):
                    if line.strip() and not line.startswith('#') and not line.startswith('References'):
                        # Check if line looks like a reference
                        if re.search(r'\(\d{4}\)', line) or re.search(r', \d{4}\.', line):
                            # Find the reference number if any
                            ref_num_match = re.search(r'^(\d+)\.\s', line)
                            if ref_num_match:
                                ref_num = ref_num_match.group(1)
                                line = re.sub(r'^(\d+)\.\s', f'[{ref_num}] ', line)
                            else:
                                ref_lines.append(line)
                        else:
                            ref_lines.append(line)
                
                # If we processed any references, update the content
                if ref_lines:
                    content = "References:\n\n" + '\n'.join(ref_lines)
        
        # Fix table formatting if needed
        table_pattern = r'(?:Table \d+:|TABLE \d+:).*?\n\|.*?\|.*?\n\|[-:\s|]+\|'
        table_matches = re.findall(table_pattern, content, re.DOTALL)
        
        if not table_matches:
            # Look for tables without captions and add them
            table_pattern_no_caption = r'\n\|.*?\|.*?\n\|[-:\s|]+\|'
            table_matches_no_caption = re.findall(table_pattern_no_caption, content, re.DOTALL)
            
            table_num = 1
            for table_match in table_matches_no_caption:
                table_caption = f"\nTable {table_num}: Data related to {section_type}\n"
                content = content.replace(table_match, table_caption + table_match)
                table_num += 1
        
        # Make sure figure captions are properly formatted
        figure_pattern = r'(?:Figure \d+:|FIGURE \d+:)'
        if not re.search(figure_pattern, content):
            # Look for potential figure references and format them
            fig_ref_pattern = r'(?:see|in|as shown in|shown in|depicted in) (?:figure|fig\.) (\d+)'
            fig_matches = re.findall(fig_ref_pattern, content, re.IGNORECASE)
            
            for fig_num in fig_matches:
                # Format the figure reference properly
                content = re.sub(
                    r'(?:see|in|as shown in|shown in|depicted in) (?:figure|fig\.) ' + fig_num,
                    f'as shown in Figure {fig_num}',
                    content,
                    flags=re.IGNORECASE
                )
        
        # Ensure consistent citation format throughout the document
        # First, ensure we don't have excessive citations
        citation_count = len(re.findall(r'\[\d+\]', content))
        if citation_count > 4 and section_type != "references":
            # Too many citations, keep only strategic ones 
            sentences = re.split(r'(?<=[.!?])\s+', content)
            processed_sentences = []
            
            # Keep track of which sentences had citations
            citation_sentences = []
            for i, sentence in enumerate(sentences):
                if re.search(r'\[\d+\]', sentence):
                    citation_sentences.append(i)
            
            # If we have too many, keep only some
            if len(citation_sentences) > 3:
                # Keep 3-4 citations evenly distributed
                indices_to_keep = []
                if len(citation_sentences) > 0:
                    # Always keep the first citation
                    indices_to_keep.append(citation_sentences[0])
                    
                    # If we have enough citations, add middle and end
                    if len(citation_sentences) >= 3:
                        middle_idx = citation_sentences[len(citation_sentences) // 2]
                        end_idx = citation_sentences[-1]
                        
                        indices_to_keep.append(middle_idx)
                        indices_to_keep.append(end_idx)
                
                # Remove citations from sentences not in our keep list
                for i, sentence in enumerate(sentences):
                    if i not in indices_to_keep and re.search(r'\[\d+\]', sentence):
                        sentences[i] = re.sub(r'\s*\[\d+\]', '', sentence)
                
                # Rebuild content
                content = ' '.join(sentences)
        
        # If no citations at all, add placeholder citations
        citation_pattern = r'\[\d+\]'
        if not re.search(citation_pattern, content) and section_type != "references":
            # Add 2-3 placeholder citations in different paragraphs
            paragraphs = content.split('\n\n')
            if len(paragraphs) >= 2:
                # Add citation to first paragraph
                first_para = paragraphs[0]
                sentences = re.split(r'(?<=[.!?])\s+', first_para)
                if len(sentences) >= 2:
                    sentences[-1] = sentences[-1] + " [1]"
                    paragraphs[0] = ' '.join(sentences)
                
                # Add citation to middle paragraph if enough paragraphs
                if len(paragraphs) >= 3:
                    mid_idx = len(paragraphs) // 2
                    mid_para = paragraphs[mid_idx]
                    sentences = re.split(r'(?<=[.!?])\s+', mid_para)
                    if len(sentences) >= 2:
                        sentences[-1] = sentences[-1] + " [2]"
                        paragraphs[mid_idx] = ' '.join(sentences)
                
                # Add citation to last paragraph
                last_para = paragraphs[-1]
                sentences = re.split(r'(?<=[.!?])\s+', last_para)
                if len(sentences) >= 2:
                    last_citation = "[2]" if len(paragraphs) < 3 else "[3]"
                    sentences[-1] = sentences[-1] + f" {last_citation}"
                    paragraphs[-1] = ' '.join(sentences)
                
                # Rebuild content
                content = '\n\n'.join(paragraphs)
        
        return content
    
    def print_memory_usage(self):
        """Print current memory usage"""
        mem = psutil.virtual_memory()
        print(f"Memory usage: {mem.percent}% of total ({mem.used / 1024 / 1024:.1f}MB used, {mem.available / 1024 / 1024:.1f}MB available)")
    
    def generate_report(self):
        """Generate the final research report by compiling all sections and return it as text"""
        print("✓ Generating final report")
        if not hasattr(self, 'sections') or not self.sections:
            return "Error: No sections available to generate report"
        
        # Sort sections by index to ensure correct order
        sorted_sections = []
        for section_info in self.sections:
            # Get section content by index
            s_index = section_info.get("index", 0)
            s_title = section_info.get("section_title", "")
            s_type = section_info.get("section_type", "")
            parent_id = section_info.get("parent_id", None)
            
            # Add all relevant data
            sorted_sections.append({
                "index": s_index,
                "parent_id": parent_id,
                "section_title": s_title,
                "section_type": s_type,
                "content": section_info.get("content", "")
            })
        
        # Sort by index
        sorted_sections = sorted(sorted_sections, key=lambda x: x["index"])
        
        # Collect all references from all sections
        citation_map = {}  # Map original citation numbers to new ones
        
        # First pass: collect unique references from all sections
        for section in sorted_sections:
            # Skip adding references from the References section itself
            if section["section_type"] == "references":
                continue
            
            content = section["content"]
            # Extract citation numbers from the content
            citations = re.findall(r'\[(\d+)\]', content)
            
            # For each citation, we'll later assign a new consistent number
            for citation in citations:
                citation_num = int(citation)
                if citation_num not in citation_map:
                    # Assign a new number based on order of appearance
                    new_num = len(citation_map) + 1
                    citation_map[citation_num] = new_num
        
        # Prepare the output content with proper markdown formatting
        output_content = f"# {self.topic}\n\n"
        
        # Add sections with proper heading levels
        for section in sorted_sections:
            content = section["content"]
            section_title = section["section_title"]
            parent_id = section["parent_id"]
            section_type = section["section_type"]
            
            # Determine heading level
            heading_level = "##" if parent_id is None else "###"
            
            # Skip the References section if we're going to generate it ourselves
            if section_type == "references":
                continue
                
            # Add section heading and content
            output_content += f"{heading_level} {section_title}\n\n{content}\n\n"
            
            # Update citation numbers to be consistent across the document
            for old_num, new_num in citation_map.items():
                pattern = r'\[' + str(old_num) + r'\]'
                replacement = f'[{new_num}]'
                output_content = re.sub(pattern, replacement, output_content)
        
        # Generate references section
        output_content += "## References\n\n"
        
        # Add placeholder for references (to be filled by another function or manually)
        ref_count = len(citation_map)
        if ref_count > 0:
            # Generate reference entries based on the AI research results
            references_prompt = f"""
            Generate a comprehensive reference list for a research paper on {self.topic}.
            
            The paper contains {ref_count} citations in numerical format [1], [2], etc.
            
            Create a properly formatted academic reference list with {ref_count} entries. Each entry should be:
            
            1. Relevant to the topic: {self.topic}
            2. Follow academic citation format (include authors, year, title, source)
            3. Be recent (within last 5-10 years where appropriate)
            4. Include a mix of journal articles, books, and reputable online sources
            5. Be numbered consistently from [1] to [{ref_count}]
            
            Format each reference in proper academic style, numbered in the format [1], [2], etc.
            """
            
            try:
                response = self.llm.invoke(references_prompt)
                # Extract response content
                if hasattr(response, 'content'):
                    references_content = response.content
                elif isinstance(response, str):
                    references_content = response
                else:
                    references_content = str(response)
                
                # Clean up references format
                references_content = references_content.strip()
                
                # Add the references to the document
                output_content += references_content
            except Exception:
                # Add placeholder references if generation fails
                for i in range(1, ref_count + 1):
                    output_content += f"[{i}] Author, A. (20XX). Title of the reference. *Journal/Source*, Volume(Issue), pages.\n\n"
        else:
            output_content += "No references were cited in this paper.\n\n"
        
        # Return the complete report content
        return output_content
    
    def _determine_section_type(self, section_title):
        """Determine the type of section based on its title"""
        section_title = section_title.lower()
        if "introduction" in section_title:
            return "introduction"
        elif "methodology" in section_title or "methods" in section_title:
            return "methodology"
        elif "results" in section_title:
            return "results"
        elif "discussion" in section_title:
            return "discussion"
        elif "conclusion" in section_title:
            return "conclusion"
        elif "references" in section_title or "bibliography" in section_title:
            return "references"
        elif "abstract" in section_title:
            return "abstract"
        else:
            return "general"
    
    def run_full_workflow(self):
        """Run the complete research and report generation workflow and return the final report"""
        try:
            print("✓ Starting research workflow on topic: " + self.topic)
            
            # Step 1: Plan the research
            print("✓ Planning research")
            research_plan = self.plan_research()
            
            # Step 2: Execute the research plan
            print("✓ Executing research")
            try:
                research_results = self.execute_research()
            except Exception:
                research_results = {"sections": []}
            
            # Force garbage collection between steps
            gc.collect()
            
            # Step 3: Plan the report structure
            print("✓ Planning report structure")
            report_plan = self.plan_report()
            
            # Always continue with report generation even if the plan has errors
            if "error" in report_plan:
                # Create a default report plan
                report_plan = {
                    "title": f"Research Report: {self.topic}",
                    "sections": [
                        {
                            "section_title": "Executive Summary",
                            "subsections": [],
                            "key_points": ["Overview of findings"]
                        },
                        {
                            "section_title": "Introduction",
                            "subsections": ["Background", "Objectives"],
                            "key_points": ["Introduce the topic", "Research questions"]
                        },
                        {
                            "section_title": "Methodology",
                            "subsections": ["Research Approach", "Data Sources"],
                            "key_points": ["How the research was conducted"]
                        },
                        {
                            "section_title": "Results and Analysis",
                            "subsections": ["Key Findings", "Data Analysis"],
                            "key_points": ["Main research findings"]
                        },
                        {
                            "section_title": "Discussion",
                            "subsections": ["Implications", "Limitations"],
                            "key_points": ["Interpretation of findings"]
                        },
                        {
                            "section_title": "Conclusions and Recommendations",
                            "subsections": ["Summary", "Future Directions"],
                            "key_points": ["Main conclusions", "Recommendations for action"]
                        },
                        {
                            "section_title": "References",
                            "subsections": [],
                            "key_points": ["Sources cited in the report"]
                        }
                    ]
                }
            
            # Force garbage collection
            gc.collect()
            
            # Step 4: Generate the report
            print("✓ Generating sections")
            # Store sections data from report_plan to ensure it's available for the generate_report method
            self.sections = []
            
            # Transform report_plan sections into the format expected by generate_report
            for i, section in enumerate(report_plan.get("sections", [])):
                section_title = section.get("section_title", "")
                section_type = self._determine_section_type(section_title)
                
                # Generate the section content
                section_info = {
                    "section_title": section_title,
                    "key_points": section.get("key_points", []),
                    "section_type": section_type,
                    "section_index": i+1,
                    "total_sections": len(report_plan.get("sections", []))
                }
                
                # Get existing content from research results if available
                content = ""
                for research_section in research_results.get("sections", []):
                    if research_section.get("section_title") == section_title:
                        content = research_section.get("content", "")
                        break
                
                # If no content available, generate it
                if not content:
                    section_result = self.generate_section(section_info)
                    content = section_result.get("content", "")
                
                # Add to sections
                self.sections.append({
                    "index": i,
                    "section_title": section_title,
                    "section_type": section_type,
                    "parent_id": None,
                    "content": content
                })
                
                # Add subsections if present
                if "subsections" in section:
                    for j, subsection_title in enumerate(section["subsections"]):
                        subsection_info = {
                            "section_title": subsection_title,
                            "key_points": section.get("key_points", []),
                            "section_type": "subsection",
                            "parent_section": section_title,
                            "section_index": i+1,
                            "total_sections": len(report_plan.get("sections", []))
                        }
                        
                        # Generate subsection content
                        subsection_result = self.generate_section(subsection_info)
                        subsection_content = subsection_result.get("content", "")
                        
                        # Add to sections
                        self.sections.append({
                            "index": i + (j+1) * 0.1,  # Use decimal for subsection ordering
                            "section_title": subsection_title,
                            "section_type": "subsection",
                            "parent_id": i,  # Link to parent section
                            "content": subsection_content
                        })
            
            # Now call generate_report to get the final content
            report_content = self.generate_report()
            
            # Final cleanup
            gc.collect()
            
            print("✓ Research completed successfully")
            # Return the final report content
            return report_content
            
        except Exception as e:
            return f"Error in research workflow: {str(e)}"
