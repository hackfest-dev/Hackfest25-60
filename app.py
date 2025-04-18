import streamlit as st
import os
import time
from pathlib import Path
import pandas as pd
import dotenv
import logging
import tempfile
import uuid

from crew_ai.orchestrator import Orchestrator
from crew_ai.config.config import Config, LLMProvider
from crew_ai.agents.data_miner_agent import DataMinerAgent
from crew_ai.agents.knowledge_graph_agent import KnowledgeGraphAgent
from crew_ai.agents.lite_rag_agent import LiteRAGAgent
from crew_ai.agents.writer_agent import WriterAgent
from crew_ai.models.llm_client import get_llm_client
from crew_ai.utils.temp_sqlite import TempSQLiteDB
from research_pipeline import ResearchPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AgentSus2-App')

# Load environment variables
dotenv.load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="AgentSus2 Research System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.orchestrator = None
    st.session_state.pipeline = None
    st.session_state.research_results = None
    st.session_state.report_path = None
    st.session_state.research_started = False
    st.session_state.research_step = 0
    st.session_state.research_status = ""
    st.session_state.db_path = os.path.join(tempfile.gettempdir(), f"agentsus2_{uuid.uuid4()}.db")
    st.session_state.output_dir = "output"
    st.session_state.use_pipeline = True

# Sidebar for configuration
st.sidebar.title("AgentSus2 Configuration")

# LLM provider selection
llm_provider_options = {
    "OpenAI": "openai",
    "Groq": "groq_ai", 
    "Anthropic": "anthropic",
    "OpenRouter": "openrouter"
}
selected_provider = st.sidebar.selectbox(
    "Select LLM Provider",
    options=list(llm_provider_options.keys()),
    index=1  # Default to Groq
)
llm_provider = llm_provider_options[selected_provider]
st.sidebar.info(f"Using {selected_provider} as the LLM provider")

# Pipeline selection
pipeline_mode = st.sidebar.radio(
    "Select Pipeline Mode",
    ["New Pipeline", "Legacy Orchestrator"],
    index=0
)
st.session_state.use_pipeline = pipeline_mode == "New Pipeline"

# Advanced settings
with st.sidebar.expander("Advanced Settings"):
    max_results = st.number_input("Max Results", min_value=10, max_value=500, value=50)
    sources = st.multiselect(
        "Data Sources",
        ["arxiv", "reddit", "medium", "linkedin"],
        default=["arxiv"]
    )
    
    if st.session_state.use_pipeline:
        db_path = st.text_input("Database Path", value=st.session_state.db_path)
        output_dir = st.text_input("Output Directory", value=st.session_state.output_dir)
        
        if db_path != st.session_state.db_path:
            st.session_state.db_path = db_path
        
        if output_dir != st.session_state.output_dir:
            st.session_state.output_dir = output_dir
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)

# Set environment variables
os.environ['LLM_PROVIDER'] = llm_provider
os.environ['USE_MOCK_BROKER'] = "true"  # Use mock message broker by default

# Initialize system
def initialize_system():
    if st.session_state.use_pipeline:
        try:
            # Initialize the research pipeline
            st.session_state.pipeline = ResearchPipeline(
                db_path=st.session_state.db_path,
                output_dir=st.session_state.output_dir,
                llm_provider=LLMProvider(llm_provider)
            )
            st.session_state.initialized = True
            return True
        except Exception as e:
            logger.error(f"Error initializing pipeline: {e}", exc_info=True)
            st.error(f"Pipeline initialization error: {e}")
            return False
    else:
        # Legacy orchestrator initialization
        if "orchestrator" in st.session_state and st.session_state.orchestrator:
            st.session_state.orchestrator.stop()
        
        try:
            Config.validate()
            st.session_state.orchestrator = Orchestrator(LLMProvider(llm_provider))
            st.session_state.initialized = True
            return True
        except ValueError as e:
            st.error(f"Configuration error: {e}")
            return False

# Initialize button
if st.sidebar.button("Initialize System"):
    with st.spinner("Initializing AgentSus2 system..."):
        if initialize_system():
            st.sidebar.success("System initialized successfully!")
        else:
            st.sidebar.error("Failed to initialize system. Check configuration.")

# Main content
st.title("AgentSus2 Research System")

if st.session_state.use_pipeline:
    st.markdown("""
    This system implements a decentralized multi-agent research framework with improved knowledge graph integration:
    
    1. **Data Mining**: Collects research data from various sources
    2. **Temporary SQLite Storage**: Stores data with proper relationships
    3. **Knowledge Graph Creation**: Creates a graph with entity relationships
    4. **LiteRAG**: Generates structured research content
    5. **LaTeX Report**: Creates a professional research paper
    
    Enter your research query below to start the process.
    """)
else:
    st.markdown("""
    This system implements the legacy Crew AI orchestrator:
    
    1. **Data Mining**: Collects research data from various sources
    2. **Knowledge Graph Creation**: Creates a graph from extracted entities
    3. **Query Generation**: Creates focused research questions
    4. **Query Answering**: Answers questions using the knowledge graph
    5. **Report Generation**: Creates a LaTeX research paper
    
    Enter your research query below to start the process.
    """)

# Research query input
research_query = st.text_area("Research Query", height=100, placeholder="Enter your research query here...")

# Optional paper title
paper_title = st.text_input("Paper Title (Optional)", placeholder="Leave blank to auto-generate")
if paper_title.strip() == "":
    paper_title = None

# Progress display
progress_placeholder = st.empty()
status_placeholder = st.empty()
result_placeholder = st.empty()

# Run button
if st.button("Start Research", key="run_research"):
    if not st.session_state.initialized:
        st.error("Please initialize the system first!")
    elif not research_query:
        st.error("Please enter a research query!")
    else:
        # Reset state
        st.session_state.research_started = True
        st.session_state.research_step = 0
        st.session_state.research_status = "Starting research pipeline..."
        st.session_state.research_results = None
        st.session_state.report_path = None
        
        # Store the query
        st.session_state.research_query = research_query
        st.session_state.paper_title = paper_title
        
        # Force a rerun to start the research process
        st.rerun()

# Research process - runs in the main thread
if st.session_state.research_started and st.session_state.research_step < 6:
    try:
        # Display current progress
        progress_placeholder.progress(st.session_state.research_step * 20)
        status_placeholder.text(st.session_state.research_status)
        
        # New Pipeline Process
        if st.session_state.use_pipeline:
            if st.session_state.research_step == 0:
                st.session_state.research_status = "Starting research pipeline..."
                st.session_state.research_step = 1
                st.rerun()
                
            elif st.session_state.research_step == 1:
                st.session_state.research_status = "Running complete research pipeline..."
                
                # Run the entire pipeline
                with st.spinner("Running research pipeline... This may take a while."):
                    results = st.session_state.pipeline.run(
                        query=st.session_state.research_query,
                        sources=sources,
                        max_results=max_results,
                        paper_title=st.session_state.paper_title
                    )
                
                # Save results
                st.session_state.research_results = results
                st.session_state.report_path = results.get("paper_path", "")
                st.session_state.research_status = "Research pipeline completed successfully!"
                st.session_state.research_step = 6
                st.rerun()
                
        # Legacy Orchestrator Process
        else:
            # Step 0: Initialize
            if st.session_state.research_step == 0:
                st.session_state.research_status = "Starting research pipeline..."
                st.session_state.research_step = 1
                st.rerun()
                
            # Step 1: Mine data
            elif st.session_state.research_step == 1:
                st.session_state.research_status = "Step 1/5: Mining data..."
                mining_result = st.session_state.orchestrator.mine_data(
                    st.session_state.research_query, 
                    sources,
                    max_results
                )
                st.session_state.research_step = 2
                st.rerun()
                
            # Step 2: Create knowledge graph
            elif st.session_state.research_step == 2:
                st.session_state.research_status = "Step 2/5: Creating knowledge graph..."
                graph_result = st.session_state.orchestrator.create_knowledge_graph()
                st.session_state.research_step = 3
                st.rerun()
                
            # Step 3: Generate sub-queries
            elif st.session_state.research_step == 3:
                st.session_state.research_status = "Step 3/5: Generating sub-queries..."
                st.session_state.sub_queries = st.session_state.orchestrator._generate_sub_queries(
                    st.session_state.research_query
                )
                st.session_state.research_step = 4
                st.rerun()
                
            # Step 4: Answer sub-queries
            elif st.session_state.research_step == 4:
                st.session_state.research_status = "Step 4/5: Answering queries using knowledge graph..."
                answers = []
                for query in st.session_state.sub_queries:
                    answer_result = st.session_state.orchestrator.answer_query(query)
                    if answer_result.get("status") == "success":
                        answers.append(answer_result.get("answer", ""))
                    else:
                        answers.append("No answer available.")
                
                st.session_state.answers = answers
                st.session_state.research_step = 5
                st.rerun()
                
            # Step 5: Generate report
            elif st.session_state.research_step == 5:
                st.session_state.research_status = "Step 5/5: Generating LaTeX research report..."
                title = st.session_state.paper_title or f"Research Report: {st.session_state.research_query}"
                report_result = st.session_state.orchestrator.generate_report(
                    title=title,
                    queries=st.session_state.sub_queries,
                    answers=st.session_state.answers,
                    output_path=os.path.join(st.session_state.output_dir, "report.pdf")
                )
                
                # Save results
                st.session_state.research_results = {
                    "status": "success",
                    "research_query": st.session_state.research_query,
                    "sub_queries": st.session_state.sub_queries,
                    "answers": st.session_state.answers,
                    "report_path": report_result.get("report_path", "")
                }
                
                st.session_state.report_path = report_result.get("report_path", "")
                st.session_state.research_status = "Research pipeline completed successfully!"
                st.session_state.research_step = 6
                st.rerun()
    
    except Exception as e:
        logger.error(f"Error in research process: {e}", exc_info=True)
        st.session_state.research_results = {
            "status": "error",
            "error": str(e)
        }
        st.session_state.research_status = f"Error: {e}"
        st.session_state.research_step = 6
        st.rerun()

# Display final results
if st.session_state.research_started and st.session_state.research_step == 6:
    # Final progress update
    progress_placeholder.progress(100)
    status_placeholder.text(st.session_state.research_status)
    
    # Show results
    if st.session_state.research_results:
        if st.session_state.use_pipeline:
            # New pipeline results
            if st.session_state.research_results.get("status") == "success":
                result_placeholder.success("Research completed successfully!")
                
                # Display paper title
                st.subheader("Research Paper")
                st.write(f"**Title:** {st.session_state.research_results['paper_title']}")
                
                # Display available formats
                st.write("**Available Formats:**")
                formats_available = [fmt for fmt, path in st.session_state.research_results["output_formats"].items() if path]
                
                if formats_available:
                    for fmt, path in st.session_state.research_results["output_formats"].items():
                        if path:
                            # Create a button to open the file
                            if fmt == "html":
                                with open(path, "r") as f:
                                    html_content = f.read()
                                st.download_button(
                                    label=f"Download {fmt.upper()} Report",
                                    data=html_content,
                                    file_name=os.path.basename(path),
                                    mime="text/html"
                                )
                                # Display HTML directly in Streamlit
                                with st.expander("View HTML Report"):
                                    st.components.v1.html(html_content, height=500, scrolling=True)
                            elif fmt == "markdown":
                                with open(path, "r") as f:
                                    md_content = f.read()
                                st.download_button(
                                    label=f"Download {fmt.upper()} Report",
                                    data=md_content,
                                    file_name=os.path.basename(path),
                                    mime="text/markdown"
                                )
                                # Display Markdown directly in Streamlit
                                with st.expander("View Markdown Report"):
                                    st.markdown(md_content)
                            else:
                                # For PDF and LaTeX, just provide download buttons
                                try:
                                    with open(path, "rb") as f:
                                        file_content = f.read()
                                    mime_type = "application/pdf" if fmt == "pdf" else "text/plain"
                                    st.download_button(
                                        label=f"Download {fmt.upper()} Report",
                                        data=file_content,
                                        file_name=os.path.basename(path),
                                        mime=mime_type
                                    )
                                except Exception as e:
                                    st.warning(f"Could not read {fmt.upper()} file: {e}")
                else:
                    st.warning("No output formats available.")
                
                # Display research questions and answers
                st.subheader("Research Questions and Answers")
                for i, (question, answer) in enumerate(zip(st.session_state.research_results["research_questions"], st.session_state.research_results["answers"])):
                    with st.expander(f"Q{i+1}: {question}"):
                        st.write(answer)
            else:
                result_placeholder.error(f"Research pipeline failed: {st.session_state.research_results.get('error', 'Unknown error')}")
        
        else:
            # Legacy orchestrator results
            if st.session_state.research_results.get("status") == "success":
                result_placeholder.success("Research completed successfully!")
                
                # Display sub-queries and answers
                with st.expander("Research Questions and Answers", expanded=True):
                    sub_queries = st.session_state.research_results.get("sub_queries", [])
                    answers = st.session_state.research_results.get("answers", [])
                    
                    for i, (query, answer) in enumerate(zip(sub_queries, answers)):
                        st.markdown(f"**Q{i+1}: {query}**")
                        st.markdown(f"*A: {answer}*")
                        st.markdown("---")
                
                # Display report download button if available
                report_path = st.session_state.research_results.get("report_path", "")
                if report_path and Path(report_path).exists():
                    st.subheader("Research Report")
                    
                    try:
                        with open(report_path, "rb") as f:
                            st.download_button(
                                label="Download Research Report (PDF)",
                                data=f,
                                file_name=Path(report_path).name,
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Error loading PDF: {e}")
            else:
                result_placeholder.error(f"Research pipeline failed: {st.session_state.research_results.get('error', 'Unknown error')}")

# Debug information
with st.sidebar.expander("Debug Information"):
    st.write("Session State:")
    st.write({k: v for k, v in st.session_state.items() if k not in ["orchestrator", "pipeline"]})
    
    if st.session_state.use_pipeline and st.session_state.initialized:
        st.write("Database Path:", st.session_state.db_path)
        
        # Add button to view database stats
        if st.button("View Database Stats"):
            try:
                temp_db = TempSQLiteDB(st.session_state.db_path)
                with temp_db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Get content count
                    cursor.execute("SELECT COUNT(*) FROM content")
                    content_count = cursor.fetchone()[0]
                    
                    # Get entity count
                    cursor.execute("SELECT COUNT(*) FROM entities")
                    entity_count = cursor.fetchone()[0]
                    
                    # Get entity types
                    cursor.execute("SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type")
                    entity_types = {row[0]: row[1] for row in cursor.fetchall()}
                    
                    # Get relationship count
                    cursor.execute("SELECT COUNT(*) FROM relationships")
                    relationship_count = cursor.fetchone()[0]
                    
                st.write(f"Content items: {content_count}")
                st.write(f"Entities: {entity_count}")
                st.write(f"Entity types: {entity_types}")
                st.write(f"Relationships: {relationship_count}")
            except Exception as e:
                st.error(f"Error reading database: {e}")

# Footer
st.markdown("---")
st.markdown("AgentSus2 Research System - A decentralized multi-agent research framework")
