import streamlit as st
import os
import time
from pathlib import Path
import pandas as pd
import dotenv
from crew_ai.orchestrator import Orchestrator
from crew_ai.config.config import Config, LLMProvider

# Load environment variables
dotenv.load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Crew AI Research System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.orchestrator = None
    st.session_state.research_results = None
    st.session_state.report_path = None
    st.session_state.research_started = False
    st.session_state.research_step = 0
    st.session_state.research_status = ""

# Sidebar for configuration
st.sidebar.title("Crew AI Configuration")

# Set LLM provider to Groq by default
llm_provider = "groq_ai"
st.sidebar.info("Using Groq AI as the LLM provider")

# Set environment variables
os.environ['LLM_PROVIDER'] = llm_provider
os.environ['USE_MOCK_BROKER'] = "true"  # Use mock message broker by default

# Initialize orchestrator
def initialize_orchestrator():
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
    with st.spinner("Initializing Crew AI system..."):
        if initialize_orchestrator():
            st.sidebar.success("System initialized successfully!")
        else:
            st.sidebar.error("Failed to initialize system. Check configuration.")

# Main content
st.title("Crew AI Research System")
st.markdown("""
This system implements a decentralized multi-agent research framework that orchestrates multiple specialized agents to collect, process, analyze, and present information in a structured research report.

Enter your research query below to start the process.
""")

# Research query input
research_query = st.text_area("Research Query", height=100, placeholder="Enter your research query here...")

# Progress display
progress_placeholder = st.empty()
status_placeholder = st.empty()
result_placeholder = st.empty()

# Run button
if st.button("Start Research", key="run_research"):
    if not st.session_state.initialized:
        st.error("Please initialize the system first!")
    else:
        # Reset state
        st.session_state.research_started = True
        st.session_state.research_step = 0
        st.session_state.research_status = "Starting research pipeline..."
        st.session_state.research_results = None
        st.session_state.report_path = None
        
        # Store the query
        st.session_state.research_query = research_query
        
        # Force a rerun to start the research process
        st.rerun()

# Research process - runs in the main thread
if st.session_state.research_started and st.session_state.research_step < 6:
    try:
        # Display current progress
        progress_placeholder.progress(st.session_state.research_step * 20)
        status_placeholder.text(st.session_state.research_status)
        
        # Step 0: Initialize
        if st.session_state.research_step == 0:
            st.session_state.research_status = "Starting research pipeline..."
            st.session_state.research_step = 1
            st.rerun()
            
        # Step 1: Mine data
        elif st.session_state.research_step == 1:
            st.session_state.research_status = "Step 1/5: Mining data from arXiv..."
            mining_result = st.session_state.orchestrator.mine_data(
                st.session_state.research_query, 
                ["arxiv"],  # Only use arXiv as the data source
                400
            )
            st.session_state.research_step = 2
            st.rerun()
            
        # Step 2: Create knowledge graph
        elif st.session_state.research_step == 2:
            st.session_state.research_status = "Step 2/5: Creating semantic knowledge graph..."
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
            report_result = st.session_state.orchestrator.generate_report(
                title=f"Research Report: {st.session_state.research_query}",
                queries=st.session_state.sub_queries,
                answers=st.session_state.answers,
                output_path="report.pdf"
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
        if st.session_state.research_results.get("status") == "success":
            result_placeholder.success("Research completed successfully!")
            
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

# Footer
st.markdown("---")
st.markdown("Crew AI Framework - A decentralized multi-agent research system")
