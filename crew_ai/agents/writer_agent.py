import os
import json
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pylatex import Document, Section, Subsection, Command, Figure, Package
from pylatex.utils import italic, bold, NoEscape
import fitz  # PyMuPDF

from crew_ai.agents.base_agent import BaseAgent
from crew_ai.models.llm_client import LLMClient, get_llm_client
from crew_ai.utils.messaging import MessageBroker
from crew_ai.config.config import Config, LLMProvider

class WriterAgent(BaseAgent):
    """Agent for generating LaTeX reports."""
    
    def __init__(self, agent_id: Optional[str] = None,
                 llm_client: Optional[LLMClient] = None,
                 llm_provider: Optional[LLMProvider] = None,
                 message_broker: Optional[MessageBroker] = None,
                 latex_temp_dir: Optional[str] = None):
        """Initialize the WriterAgent."""
        super().__init__(agent_id, llm_client, llm_provider, message_broker)
        
        self.latex_temp_dir = latex_temp_dir or Config.LATEX_TEMP_DIR
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.latex_temp_dir, exist_ok=True)
        
        # Register message handlers
        self.register_handler("generate_report", self._handle_generate_report)
        self.register_handler("generate_section", self._handle_generate_section)
    
    def _handle_generate_report(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle generate_report messages."""
        title = message.get("data", {}).get("title", "Research Report")
        queries = message.get("data", {}).get("queries", [])
        answers = message.get("data", {}).get("answers", [])
        output_path = message.get("data", {}).get("output_path", "report.pdf")
        
        if not queries or not answers:
            return {"status": "error", "error": "Queries and answers are required"}
        
        report_path = self.generate_report(title, queries, answers, output_path)
        
        return {
            "status": "success",
            "report_path": report_path
        }
    
    def _handle_generate_section(self, message: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
        """Handle generate_section messages."""
        section_type = message.get("data", {}).get("section_type")
        content = message.get("data", {}).get("content", {})
        
        if not section_type:
            return {"status": "error", "error": "Section type is required"}
        
        latex_code = self.generate_section(section_type, content)
        
        return {
            "status": "success",
            "latex_code": latex_code
        }
    
    def generate_report(self, title: str, queries: List[str], answers: List[str], 
                       output_path: str = "report.pdf") -> str:
        """Generate a LaTeX report based on queries and answers."""
        print(f"Generating report: {title}")
        
        # Generate report structure
        report_structure = self._generate_report_structure(title, queries, answers)
        
        # Generate LaTeX code for each section
        report_sections = {}
        for section_type, content in report_structure.items():
            report_sections[section_type] = self.generate_section(section_type, content)
        
        # Compile the report
        report_path = self._compile_latex_report(title, report_sections, output_path)
        
        print(f"Report generated: {report_path}")
        return report_path
    
    def _generate_report_structure(self, title: str, queries: List[str], 
                                 answers: List[str]) -> Dict[str, Any]:
        """Generate the structure of the report."""
        # Combine queries and answers
        qa_pairs = []
        for i in range(min(len(queries), len(answers))):
            qa_pairs.append({
                "query": queries[i],
                "answer": answers[i]
            })
        
        prompt = f"""
        Generate a structure for a research report based on the following queries and answers.
        The report should have the following sections:
        - Abstract
        - Introduction
        - Methods
        - Results
        - Discussion
        - Conclusion
        
        Title: {title}
        
        Queries and Answers:
        {json.dumps(qa_pairs, indent=2)}
        
        For each section, provide:
        1. A brief description of what should be included
        2. Key points to cover
        3. Any subsections that should be included
        
        Return the structure as a JSON object with sections as keys and their details as values.
        """
        
        system_prompt = """
        You are a research report planner. Your task is to create a structured outline for a research report
        based on a set of queries and answers. The structure should follow standard academic format with
        abstract, introduction, methods, results, discussion, and conclusion sections.
        
        Return your plan as a JSON object with sections as keys and their details as values.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1500
        )
        
        try:
            # Extract JSON object from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            report_structure = json.loads(response)
            
            # Ensure all required sections are present
            required_sections = ["abstract", "introduction", "methods", "results", "discussion", "conclusion"]
            for section in required_sections:
                if section not in report_structure:
                    report_structure[section] = {
                        "description": f"This section contains the {section} of the report.",
                        "key_points": [],
                        "subsections": []
                    }
            
            # Add queries and answers to the structure
            report_structure["qa_pairs"] = qa_pairs
            report_structure["title"] = title
            
            return report_structure
        
        except Exception as e:
            print(f"Error generating report structure: {e}")
            
            # Return a default structure
            return {
                "title": title,
                "qa_pairs": qa_pairs,
                "abstract": {
                    "description": "This section contains the abstract of the report.",
                    "key_points": [],
                    "subsections": []
                },
                "introduction": {
                    "description": "This section contains the introduction of the report.",
                    "key_points": [],
                    "subsections": []
                },
                "methods": {
                    "description": "This section contains the methods of the report.",
                    "key_points": [],
                    "subsections": []
                },
                "results": {
                    "description": "This section contains the results of the report.",
                    "key_points": [],
                    "subsections": []
                },
                "discussion": {
                    "description": "This section contains the discussion of the report.",
                    "key_points": [],
                    "subsections": []
                },
                "conclusion": {
                    "description": "This section contains the conclusion of the report.",
                    "key_points": [],
                    "subsections": []
                }
            }
    
    def generate_section(self, section_type: str, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for a section."""
        # Prepare prompt based on section type
        if section_type == "abstract":
            return self._generate_abstract(content)
        elif section_type == "introduction":
            return self._generate_introduction(content)
        elif section_type == "methods":
            return self._generate_methods(content)
        elif section_type == "results":
            return self._generate_results(content)
        elif section_type == "discussion":
            return self._generate_discussion(content)
        elif section_type == "conclusion":
            return self._generate_conclusion(content)
        else:
            return self._generate_generic_section(section_type, content)
    
    def _generate_abstract(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the abstract section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        
        prompt = f"""
        Generate a LaTeX abstract for a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        The abstract should be a single paragraph of 150-250 words that summarizes the entire report.
        It should include the purpose, methods, results, and conclusions of the research.
        
        Return only the LaTeX code for the abstract section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for an abstract section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_introduction(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the introduction section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        subsections = content.get("subsections", [])
        
        prompt = f"""
        Generate LaTeX code for the introduction section of a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        Subsections:
        {json.dumps(subsections, indent=2)}
        
        The introduction should provide background information, state the research problem,
        explain the significance of the research, and outline the structure of the report.
        
        Return only the LaTeX code for the introduction section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for an introduction section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_methods(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the methods section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        subsections = content.get("subsections", [])
        
        prompt = f"""
        Generate LaTeX code for the methods section of a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        Subsections:
        {json.dumps(subsections, indent=2)}
        
        The methods section should describe the data collection process, the knowledge graph creation,
        and the query answering process. Include details about the tools and techniques used.
        
        Return only the LaTeX code for the methods section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for a methods section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_results(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the results section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        subsections = content.get("subsections", [])
        
        prompt = f"""
        Generate LaTeX code for the results section of a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        Subsections:
        {json.dumps(subsections, indent=2)}
        
        Queries and Answers:
        {json.dumps(qa_pairs, indent=2)}
        
        The results section should present the findings of the research, including the answers to the queries.
        Organize the results in a logical manner, possibly using subsections for different topics.
        
        Return only the LaTeX code for the results section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for a results section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1500
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_discussion(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the discussion section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        subsections = content.get("subsections", [])
        
        prompt = f"""
        Generate LaTeX code for the discussion section of a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        Subsections:
        {json.dumps(subsections, indent=2)}
        
        Queries and Answers:
        {json.dumps(qa_pairs, indent=2)}
        
        The discussion section should interpret the results, explain their significance, compare them with existing literature,
        discuss limitations of the research, and suggest directions for future research.
        
        Return only the LaTeX code for the discussion section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for a discussion section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_conclusion(self, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for the conclusion section."""
        title = content.get("title", "Research Report")
        qa_pairs = content.get("qa_pairs", [])
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        
        prompt = f"""
        Generate LaTeX code for the conclusion section of a research report with the following details:
        
        Title: {title}
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        The conclusion should summarize the main findings, restate the significance of the research,
        and provide closing thoughts.
        
        Return only the LaTeX code for the conclusion section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for a conclusion section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _generate_generic_section(self, section_type: str, content: Dict[str, Any]) -> str:
        """Generate LaTeX code for a generic section."""
        description = content.get("description", "")
        key_points = content.get("key_points", [])
        
        prompt = f"""
        Generate LaTeX code for a {section_type} section of a research report with the following details:
        
        Description: {description}
        
        Key Points:
        {json.dumps(key_points, indent=2)}
        
        Return only the LaTeX code for the section, without any explanations.
        """
        
        system_prompt = """
        You are a LaTeX document generator. Your task is to generate LaTeX code for a section
        of a research report. Return only the LaTeX code, without any explanations or markdown formatting.
        """
        
        response = self.llm_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Clean up response
        response = response.strip()
        if response.startswith("```latex"):
            response = response[8:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response.strip()
    
    def _compile_latex_report(self, title: str, sections: Dict[str, str], 
                            output_path: str) -> str:
        """Compile the LaTeX report."""
        # Create a temporary directory for LaTeX files
        with tempfile.TemporaryDirectory(dir=self.latex_temp_dir) as temp_dir:
            # Create the LaTeX file
            latex_file_path = os.path.join(temp_dir, "report.tex")
            
            with open(latex_file_path, "w") as f:
                f.write(self._generate_latex_document(title, sections))
            
            # Compile the LaTeX file
            try:
                # Run pdflatex twice to resolve references
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "report.tex"],
                    cwd=temp_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "report.tex"],
                    cwd=temp_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Copy the PDF to the output path
                pdf_file_path = os.path.join(temp_dir, "report.pdf")
                
                # Ensure the output directory exists
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                
                # Copy the PDF
                with open(pdf_file_path, "rb") as src, open(output_path, "wb") as dst:
                    dst.write(src.read())
                
                return output_path
            
            except subprocess.CalledProcessError as e:
                print(f"Error compiling LaTeX: {e}")
                print(f"stdout: {e.stdout.decode('utf-8')}")
                print(f"stderr: {e.stderr.decode('utf-8')}")
                
                # Return the LaTeX file path as a fallback
                return latex_file_path
    
    def _generate_latex_document(self, title: str, sections: Dict[str, str]) -> str:
        """Generate the complete LaTeX document."""
        latex_code = []
        
        # Document class and packages
        latex_code.append(r"\documentclass[11pt,a4paper]{article}")
        latex_code.append(r"\usepackage[utf8]{inputenc}")
        latex_code.append(r"\usepackage[T1]{fontenc}")
        latex_code.append(r"\usepackage{lmodern}")
        latex_code.append(r"\usepackage{amsmath}")
        latex_code.append(r"\usepackage{amsfonts}")
        latex_code.append(r"\usepackage{amssymb}")
        latex_code.append(r"\usepackage{graphicx}")
        latex_code.append(r"\usepackage{hyperref}")
        latex_code.append(r"\usepackage{booktabs}")
        latex_code.append(r"\usepackage{natbib}")
        latex_code.append(r"\usepackage{fancyhdr}")
        latex_code.append(r"\usepackage{geometry}")
        latex_code.append(r"\geometry{a4paper, margin=1in}")
        latex_code.append(r"\pagestyle{fancy}")
        latex_code.append(r"\fancyhf{}")
        latex_code.append(r"\rhead{\thepage}")
        latex_code.append(r"\lhead{\nouppercase{\leftmark}}")
        latex_code.append("")
        
        # Title
        latex_code.append(r"\title{" + title + r"}")
        latex_code.append(r"\author{Crew AI Framework}")
        latex_code.append(r"\date{\today}")
        latex_code.append("")
        
        # Begin document
        latex_code.append(r"\begin{document}")
        latex_code.append("")
        
        # Maketitle
        latex_code.append(r"\maketitle")
        latex_code.append("")
        
        # Abstract
        if "abstract" in sections:
            latex_code.append(r"\begin{abstract}")
            latex_code.append(sections["abstract"])
            latex_code.append(r"\end{abstract}")
            latex_code.append("")
        
        # Table of contents
        latex_code.append(r"\tableofcontents")
        latex_code.append(r"\newpage")
        latex_code.append("")
        
        # Sections
        section_order = ["introduction", "methods", "results", "discussion", "conclusion"]
        
        for section in section_order:
            if section in sections:
                latex_code.append(r"\section{" + section.capitalize() + r"}")
                latex_code.append(sections[section])
                latex_code.append("")
        
        # End document
        latex_code.append(r"\end{document}")
        
        return "\n".join(latex_code)
    
    def run(self, title: str, queries: List[str], answers: List[str], output_path: str = "report.pdf"):
        """Run the report generation process."""
        print(f"Generating report: {title}")
        report_path = self.generate_report(title, queries, answers, output_path)
        
        print(f"Report generated: {report_path}")
        return report_path
