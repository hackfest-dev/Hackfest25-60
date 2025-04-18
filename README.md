# Crew AI Framework

A decentralized multi-agent research system that orchestrates multiple specialized agents to collect, process, analyze, and present information in a structured research report.

## Features

- **Data Mining**: Scrapes 300-400 relevant sources using DuckDuckGo WebSearch API
- **Knowledge Graph**: Creates semantic knowledge graphs using Neo4j
- **RAG-based Query Answering**: Performs semantic graph traversal to answer user queries
- **Validation**: Reviews LLM-generated outputs for accuracy and completeness
- **LaTeX Report Generation**: Creates professional research reports in PDF format

## Architecture

The system consists of the following agents:

1. **DataMinerAgent**: Scrapes and processes data from various sources
2. **Knowledge Graph Creation**: Post-processing step to create a semantic knowledge graph
3. **LiteRAGAgent**: Answers user queries using the knowledge graph
4. **ValidatorAgent**: Validates LLM-generated outputs
5. **WriterAgent**: Generates LaTeX reports

## Requirements

- Python 3.9+
- RabbitMQ server
- Neo4j database
- SQLite
- LaTeX installation (for PDF generation)

## Installation

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file (see `.env.example`)
4. Start RabbitMQ server
5. Start Neo4j database

## Usage

```bash
python main.py --llm_provider [ollama|groq_ai|openrouter]
```

## LLM Provider Options

- `ollama`: Use local Ollama models
- `groq_ai`: Use Groq AI API
- `openrouter`: Use OpenRouter API

## License

MIT
