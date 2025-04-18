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
    
    def generate_report(self, title: str, queries: List[str], answers: List[Any], 
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
                                 answers: List[Any]) -> Dict[str, Any]:
        """Generate the structure of the report."""
        # Combine queries and answers
        qa_pairs = []
        for i in range(min(len(queries), len(answers))):
            # Check if answer is already a dictionary with query and answer
            if isinstance(answers[i], dict) and "query" in answers[i] and "answer" in answers[i]:
                qa_pairs.append(answers[i])
            else:
                qa_pairs.append({
                    "query": queries[i],
                    "answer": answers[i]
                })
        
        prompt = f"""
        Generate a structured outline for a research report with the following title:
        
        Title: {title}
        
        Based on the following questions and answers:
        
        {json.dumps(qa_pairs, indent=2)}
        
        The report should have the following sections:
        1. Abstract - A brief summary of the entire report
        2. Introduction - Background information and context
        3. Methods - How the research was conducted
        4. Results - Key findings from the research
        5. Discussion - Interpretation of results and implications
        6. Conclusion - Summary of key points and future directions
        
        For each section, provide:
        - A brief description of what should be included
        - Key points to cover
        
        Return the outline as a JSON object with the following structure:
        {{
            "abstract": {{
                "description": "...",
                "key_points": ["...", "..."]
            }},
            "introduction": {{
                "description": "...",
                "key_points": ["...", "..."]
            }},
            ...
        }}
        """
        
        system_prompt = """
        You are a research report planner. Your task is to create a structured outline for a research report
        based on a set of queries and answers. The structure should follow standard academic format with
        abstract, introduction, methods, results, discussion, and conclusion sections.
        
        Return your plan as a JSON object with the following structure:
        {{
            "abstract": {{
                "description": "...",
                "key_points": ["...", "..."]
            }},
            "introduction": {{
                "description": "...",
                "key_points": ["...", "..."]
            }},
            ...
        }}
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
                        "key_points": []
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
                    "key_points": []
                },
                "introduction": {
                    "description": "This section contains the introduction of the report.",
                    "key_points": []
                },
                "methods": {
                    "description": "This section contains the methods of the report.",
                    "key_points": []
                },
                "results": {
                    "description": "This section contains the results of the report.",
                    "key_points": []
                },
                "discussion": {
                    "description": "This section contains the discussion of the report.",
                    "key_points": []
                },
                "conclusion": {
                    "description": "This section contains the conclusion of the report.",
                    "key_points": []
                }
            }
    
    def generate_section(self, section_type: str, content: Any) -> str:
        """Generate LaTeX code for a section."""
        # Handle different section types
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
    
    def _generate_generic_section(self, section_type: str, content: Any) -> str:
        """Generate LaTeX code for a generic section."""
        # Handle string content
        if isinstance(content, str):
            description = content
            key_points = []
        # Handle dictionary content
        elif isinstance(content, dict):
            description = content.get("description", "")
            key_points = content.get("key_points", [])
        else:
            description = str(content)
            key_points = []
        
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
        # Generate LaTeX document
        latex_code = self._generate_latex_document(title, sections)
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp(dir=self.latex_temp_dir)
        
        # Write LaTeX code to file
        latex_file_path = os.path.join(temp_dir, "report.tex")
        with open(latex_file_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        
        # Save the LaTeX source file to the output directory
        latex_output_path = output_path.replace(".pdf", ".tex")
        os.makedirs(os.path.dirname(os.path.abspath(latex_output_path)), exist_ok=True)
        with open(latex_output_path, "w", encoding="utf-8") as f:
            f.write(latex_code)
        
        # Also create a simple HTML version
        html_output_path = output_path.replace(".pdf", ".html")
        html_content = self._generate_html_document(title, sections)
        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Also create a simple Markdown version
        md_output_path = output_path.replace(".pdf", ".md")
        md_content = self._generate_markdown_document(title, sections)
        with open(md_output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        # Try to compile LaTeX to PDF
        try:
            # Check if pdflatex is installed
            subprocess.run(
                ["which", "pdflatex"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Compile LaTeX to PDF
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "report.tex"],
                cwd=temp_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Run again for references
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
            
            print(f"PDF report generated: {output_path}")
            return output_path
            
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"LaTeX compilation failed: {e}")
            print("Falling back to HTML and Markdown versions")
            
            # Return the HTML file path as a fallback
            print(f"HTML report generated: {html_output_path}")
            print(f"Markdown report generated: {md_output_path}")
            print(f"LaTeX source saved: {latex_output_path}")
            
            return html_output_path
    
    def _generate_html_document(self, title: str, sections: Dict[str, str]) -> str:
        """Generate a simple HTML document from the LaTeX sections."""
        html = []
        
        # HTML header
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append(f"<title>{title}</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }")
        html.append("h1 { text-align: center; margin-bottom: 30px; }")
        html.append("h2 { margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 10px; }")
        html.append("p { margin-bottom: 15px; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        
        # Title
        html.append(f"<h1>{title}</h1>")
        
        # Abstract
        if "abstract" in sections:
            html.append("<div class='abstract'>")
            html.append("<h2>Abstract</h2>")
            html.append(self._latex_to_html(sections["abstract"]))
            html.append("</div>")
        
        # Main sections
        section_order = ["introduction", "methods", "results", "discussion", "conclusion"]
        
        for section in section_order:
            if section in sections:
                html.append(f"<h2>{section.capitalize()}</h2>")
                html.append(self._latex_to_html(sections[section]))
        
        # HTML footer
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def _generate_markdown_document(self, title: str, sections: Dict[str, str]) -> str:
        """Generate a simple Markdown document from the LaTeX sections."""
        md = []
        
        # Title
        md.append(f"# {title}")
        md.append("")
        
        # Abstract
        if "abstract" in sections:
            md.append("## Abstract")
            md.append("")
            md.append(self._latex_to_markdown(sections["abstract"]))
            md.append("")
        
        # Main sections
        section_order = ["introduction", "methods", "results", "discussion", "conclusion"]
        
        for section in section_order:
            if section in sections:
                md.append(f"## {section.capitalize()}")
                md.append("")
                md.append(self._latex_to_markdown(sections[section]))
                md.append("")
        
        return "\n".join(md)
    
    def _latex_to_html(self, latex: str) -> str:
        """Convert simple LaTeX to HTML."""
        # Replace common LaTeX commands with HTML
        html = latex
        
        # Replace sections and subsections
        html = html.replace("\\section{", "<h2>").replace("}", "</h2>")
        html = html.replace("\\subsection{", "<h3>").replace("}", "</h3>")
        html = html.replace("\\subsubsection{", "<h4>").replace("}", "</h4>")
        
        # Replace formatting
        html = html.replace("\\textbf{", "<strong>").replace("}", "</strong>")
        html = html.replace("\\textit{", "<em>").replace("}", "</em>")
        
        # Replace paragraphs
        html = html.replace("\n\n", "</p><p>")
        
        # Wrap in paragraph tags
        html = f"<p>{html}</p>"
        
        # Fix double paragraph tags
        html = html.replace("<p><p>", "<p>").replace("</p></p>", "</p>")
        
        return html
    
    def _latex_to_markdown(self, latex: str) -> str:
        """Convert simple LaTeX to Markdown."""
        # Replace common LaTeX commands with Markdown
        md = latex
        
        # Replace sections and subsections
        md = md.replace("\\section{", "## ").replace("}", "")
        md = md.replace("\\subsection{", "### ").replace("}", "")
        md = md.replace("\\subsubsection{", "#### ").replace("}", "")
        
        # Replace formatting
        md = md.replace("\\textbf{", "**").replace("}", "**")
        md = md.replace("\\textit{", "*").replace("}", "*")
        
        # Replace paragraphs
        md = md.replace("\n\n", "\n\n")
        
        return md
    
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
    
    def run(self, title: str, queries: List[str], answers: List[Any], output_path: str = "report.pdf"):
        """Run the report generation process."""
        print(f"Generating report: {title}")
        report_path = self.generate_report(title, queries, answers, output_path)
        
        print(f"Report generated: {report_path}")
        return report_path
