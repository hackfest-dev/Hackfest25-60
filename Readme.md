# Searchify.Ai: AI-Powered Living Research Assistant

<div align="center">
  <img src="https://img.shields.io/badge/status-active-success.svg" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</div>

<p align="center">
  A comprehensive AI-powered research assistant that automates complex research tasks and generates professional reports through a multi-agent system architecture.
</p>

## 🌟 Overview

Searchify is an advanced research automation platform that transforms complex research queries into comprehensive, well-structured research papers. The system leverages a distributed multi-agent architecture to mine data, build knowledge graphs, answer research questions, and generate professional documents—all with minimal human intervention.

## 🚀 What Problem Does It Solve?

Academic and professional research is often time-consuming and resource-intensive, requiring:
- Extensive data collection from diverse sources
- Complex knowledge organization and synthesis
- Critical analysis and structured reporting
- Professional document creation with proper citations

Searchify automates this entire process, allowing researchers, students, and professionals to:
- Get comprehensive research on any topic in minutes instead of days or weeks
- Access information from various sources through a unified interface
- Generate publication-ready documents with proper structure and citations
- Focus on insights and creative work rather than tedious research tasks

## ✨ Key Features

- **Multi-Source Data Mining**: Collects information from academic papers, reddit, medium, and other platforms
- **Knowledge Graph Integration**: Creates a structured representation of entities and relationships
- **LiteRAG Technology**: Generates focused answers to research questions with context awareness
- **Professional Document Generation**: Creates LaTeX-based research papers with proper formatting
- **User-Friendly Interface**: Simple UI for submitting research queries and viewing results
- **Podcast Generation**: Convert research papers and documents into audio podcasts

## 💻 Technical Architecture

The system is built with a modern stack divided into four main components:

### Frontend
- NextJs with TypeScript
- Tailwind CSS & Acerteneity UI and ShadCN for styling
- Next Router for navigation

### Backend
- FastAPI (Python) for the RESTful API
- SQLAlchemy for database operations
- Alembic for database migrations

### AI Research Engine
- Crew AI Framework with specialized agent roles:
  - DataMinerAgent: Scrapes 300-400 relevant sources using search APIs
  - Knowledge Graph Creation: Successfully implemented and tested (see AI_researcher directory), currently toggled off by default for faster response times while preserving the option for deep semantic analysis
  - LiteRAGAgent: Intelligently answers user queries using optimized vector search for speed
  - ValidatorAgent: Reviews outputs for accuracy
  - WriterAgent: Generates LaTeX reports
- Support for multiple LLM providers (OpenAI, Groq, Anthropic, OpenRouter, Ollama)

### Podcast Lab
- PDF-to-Podcast conversion pipeline
- Text-to-speech technology for generating high-quality audio content
- Processing tools to transform research papers into engaging audio formats

## 🏁 Getting Started

Detailed setup instructions can be found in the respective directories:
- [Frontend Setup](./frontend/README.md)
- [Backend Setup](./backend/README.md)
- [AI Researcher Setup](./AI_researcher/README.md)
- [Podcast Lab](./Podcast_lab/pdf_podcast.ipynb)

## 👥 Creators

This project was created by:

- **Akshaykumar**
- **Ramachandra Udupa**
- **Sumedh Navuda**

<p align="center">
  Made with ❤️ and powered by AI
</p>
