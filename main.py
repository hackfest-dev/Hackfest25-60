#!/usr/bin/env python3
import os
import sys
import click
import dotenv
from crew_ai.orchestrator import Orchestrator
from crew_ai.config.config import Config, LLMProvider

# Load environment variables
dotenv.load_dotenv()

@click.group()
def cli():
    """Crew AI Framework - A decentralized multi-agent research system."""
    pass

@cli.command()
@click.option('--llm_provider', type=click.Choice(['ollama', 'groq_ai', 'openrouter']), 
              default='ollama', help='LLM provider to use')
@click.option('--query', required=True, help='Research query to process')
@click.option('--sources', multiple=True, 
              help='Sources to mine data from (reddit, medium, linkedin, arxiv)')
@click.option('--max_results', type=int, default=400, 
              help='Maximum number of results to mine')
@click.option('--output', default='report.pdf', help='Output path for the report')
def research(llm_provider, query, sources, max_results, output):
    """Run the complete research pipeline."""
    # Set LLM provider in environment
    os.environ['LLM_PROVIDER'] = llm_provider
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(LLMProvider(llm_provider))
    
    # Run research pipeline
    try:
        click.echo(f"Starting research pipeline with {llm_provider} provider...")
        click.echo(f"Research query: {query}")
        
        if sources:
            click.echo(f"Sources: {', '.join(sources)}")
        else:
            sources = None
            click.echo("Sources: All available")
        
        click.echo(f"Max results: {max_results}")
        click.echo(f"Output path: {output}")
        click.echo("This process may take a while. Please be patient.")
        
        result = orchestrator.run_research_pipeline(
            research_query=query,
            sources=sources,
            max_results=max_results,
            output_path=output
        )
        
        if result.get("status") == "success":
            click.echo("\n✅ Research pipeline completed successfully!")
            click.echo(f"Execution time: {result.get('execution_time', 0):.2f} seconds")
            click.echo(f"Report generated: {result.get('report_path', '')}")
        else:
            click.echo("\n❌ Research pipeline failed!")
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
            click.echo(f"Details: {result.get('details', {})}")
    
    except Exception as e:
        click.echo(f"\n❌ An error occurred: {e}", err=True)
        sys.exit(1)
    
    finally:
        # Stop orchestrator
        orchestrator.stop()

@cli.command()
@click.option('--llm_provider', type=click.Choice(['ollama', 'groq_ai', 'openrouter']), 
              default='ollama', help='LLM provider to use')
@click.option('--query', required=True, help='Query to answer')
def answer(llm_provider, query):
    """Answer a single query using the knowledge graph."""
    # Set LLM provider in environment
    os.environ['LLM_PROVIDER'] = llm_provider
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(LLMProvider(llm_provider))
    
    # Answer query
    try:
        click.echo(f"Answering query with {llm_provider} provider: {query}")
        
        result = orchestrator.answer_query(query)
        
        if result.get("status") == "success":
            click.echo("\n✅ Query answered successfully!")
            click.echo(f"Answer: {result.get('answer', '')}")
            
            validation = result.get("validation", {})
            if validation:
                click.echo("\nValidation scores:")
                scores = validation.get("scores", {})
                for score_name, score_value in scores.items():
                    click.echo(f"- {score_name}: {score_value}/10")
        else:
            click.echo("\n❌ Failed to answer query!")
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"\n❌ An error occurred: {e}", err=True)
        sys.exit(1)
    
    finally:
        # Stop orchestrator
        orchestrator.stop()

@cli.command()
@click.option('--llm_provider', type=click.Choice(['ollama', 'groq_ai', 'openrouter']), 
              default='ollama', help='LLM provider to use')
@click.option('--query', required=True, help='Query to mine data for')
@click.option('--sources', multiple=True, 
              help='Sources to mine data from (reddit, medium, linkedin, arxiv)')
@click.option('--max_results', type=int, default=400, 
              help='Maximum number of results to mine')
def mine(llm_provider, query, sources, max_results):
    """Mine data for a query."""
    # Set LLM provider in environment
    os.environ['LLM_PROVIDER'] = llm_provider
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(LLMProvider(llm_provider))
    
    # Mine data
    try:
        click.echo(f"Mining data with {llm_provider} provider...")
        click.echo(f"Query: {query}")
        
        if sources:
            click.echo(f"Sources: {', '.join(sources)}")
        else:
            sources = None
            click.echo("Sources: All available")
        
        click.echo(f"Max results: {max_results}")
        click.echo("This process may take a while. Please be patient.")
        
        result = orchestrator.mine_data(
            query=query,
            sources=sources,
            max_results=max_results
        )
        
        if result.get("status") == "success":
            click.echo("\n✅ Data mining completed successfully!")
            results = result.get("results", {})
            click.echo(f"Total sources: {results.get('total_sources', 0)}")
            click.echo(f"Successful sources: {results.get('successful_sources', 0)}")
            click.echo(f"Failed sources: {results.get('failed_sources', 0)}")
            click.echo(f"Filtered sources: {results.get('filtered_sources', 0)}")
            
            click.echo("\nSource breakdown:")
            for source, stats in results.get("source_breakdown", {}).items():
                click.echo(f"- {source}: {stats.get('successful', 0)}/{stats.get('total', 0)} successful")
        else:
            click.echo("\n❌ Data mining failed!")
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"\n❌ An error occurred: {e}", err=True)
        sys.exit(1)
    
    finally:
        # Stop orchestrator
        orchestrator.stop()

@cli.command()
@click.option('--llm_provider', type=click.Choice(['ollama', 'groq_ai', 'openrouter']), 
              default='ollama', help='LLM provider to use')
def create_graph(llm_provider):
    """Create a knowledge graph from the mined data."""
    # Set LLM provider in environment
    os.environ['LLM_PROVIDER'] = llm_provider
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    
    # Initialize orchestrator
    orchestrator = Orchestrator(LLMProvider(llm_provider))
    
    # Create knowledge graph
    try:
        click.echo(f"Creating knowledge graph with {llm_provider} provider...")
        click.echo("This process may take a while. Please be patient.")
        
        result = orchestrator.create_knowledge_graph()
        
        if result.get("status") == "success":
            click.echo("\n✅ Knowledge graph creation completed successfully!")
            results = result.get("results", {})
            click.echo(f"Execution time: {results.get('execution_time', 0):.2f} seconds")
            click.echo(f"Content nodes: {results.get('content_nodes', 0)}")
            click.echo(f"Entity nodes: {results.get('entity_nodes', 0)}")
            click.echo(f"Entity types: {', '.join(results.get('entity_types', []))}")
        else:
            click.echo("\n❌ Knowledge graph creation failed!")
            click.echo(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        click.echo(f"\n❌ An error occurred: {e}", err=True)
        sys.exit(1)
    
    finally:
        # Stop orchestrator
        orchestrator.stop()

if __name__ == '__main__':
    cli()
