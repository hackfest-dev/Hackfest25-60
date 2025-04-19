from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.utilities.arxiv import ArxivAPIWrapper
from langchain_community.agent_toolkits.nasa.toolkit import NasaToolkit
from langchain_community.utilities.nasa import NasaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools.wikidata.tool import WikidataAPIWrapper, WikidataQueryRun
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.utilities import StackExchangeAPIWrapper
from langchain_community.tools.reddit_search.tool import RedditSearchRun
from langchain_community.utilities.reddit_search import RedditSearchAPIWrapper

from langchain.agents import tool as tool_decorator

# Initialize the RedditSearchRun tool
try:
    redit_search_tool = RedditSearchRun(
        name="reddit_search",
        description="Search Reddit posts by query, time, subreddit, and sort order.",
        api_wrapper=RedditSearchAPIWrapper(
            reddit_client_id="8V_NiMJIavgaQOGxB0wb4A",
            reddit_client_secret="UR70jVsAg9YaqHmrAxgrLDouKsZBig",
            reddit_user_agent="arhgejthej",
        )
    )
except Exception as e:
    print(f"Error initializing Reddit search: {str(e)}")
    redit_search_tool = None

# Initialize NASA tools
try:
    nasa = NasaAPIWrapper()
    # Instead of using the toolkit directly, we'll extract the tools from it
    nasa_toolkit_instance = NasaToolkit.from_nasa_api_wrapper(nasa)
    # Get the first tool from the toolkit or create a custom one
    if nasa_toolkit_instance.get_tools():
        nasa_toolkit = nasa_toolkit_instance.get_tools()[0]  # Get the first tool
    else:
        # Create a custom NASA tool
        @tool_decorator("NASA Search")
        def nasa_search(query: str) -> str:
            """Search NASA data for information about the query."""
            try:
                return nasa.run(query)
            except Exception as e:
                return f"Error searching NASA data: {str(e)}"
        nasa_toolkit = nasa_search
except Exception as e:
    print(f"Error initializing NASA tools: {str(e)}")
    nasa_toolkit = None

# Initialize StackExchange - create a custom tool wrapper
try:
    stackexchange_wrapper = StackExchangeAPIWrapper(max_results=7)
    
    # Create a custom tool for StackExchange
    @tool_decorator("StackExchange Search")
    def stackexchange_search(query: str) -> str:
        """Search StackExchange for information related to the query."""
        try:
            return stackexchange_wrapper.run(query)
        except Exception as e:
            return f"Error searching StackExchange: {str(e)}"
    
    stackexchange = stackexchange_search
except Exception as e:
    print(f"Error initializing StackExchange: {str(e)}")
    stackexchange = None

# Initialize Wikipedia and Wikidata
try:
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=8, doc_content_chars_max=400000))
except Exception as e:
    print(f"Error initializing Wikipedia: {str(e)}")
    wikipedia = None

try:
    wikidata = WikidataQueryRun(api_wrapper=WikidataAPIWrapper(top_k_results=8, doc_content_chars_max=400000))
except Exception as e:
    print(f"Error initializing Wikidata: {str(e)}")
    wikidata = None

# Initialize Yahoo Finance
try:
    tools_finance = YahooFinanceNewsTool()
except Exception as e:
    print(f"Error initializing Yahoo Finance: {str(e)}")
    tools_finance = None

# Initialize Arxiv
try:
    tool_arxive = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=8, max_results=100, sort_by="lastUpdatedDate", doc_content_chars_max=90000))
except Exception as e:
    print(f"Error initializing Arxiv: {str(e)}")
    tool_arxive = None

# Initialize DuckDuckGo
try:
    wrapper = DuckDuckGoSearchAPIWrapper(time="d", max_results=5)
    web_search = DuckDuckGoSearchResults(api_wrapper=wrapper)
except Exception as e:
    print(f"Error initializing DuckDuckGo: {str(e)}")
    web_search = None

# Create a dummy search tool as fallback
@tool_decorator("Search the web")
def web_search_fallback(query: str) -> str:
    """Search the web for information about the query."""
    return f"Web search results for: {query}\n\nThis is a fallback search tool that simulates web search results."

# Collect working tools
research_tools = []
for tool in [tool_arxive, wikipedia, wikidata, tools_finance, redit_search_tool, stackexchange, nasa_toolkit, web_search]:
    if tool is not None:
        research_tools.append(tool)

# Ensure we have at least the fallback
if not research_tools:
    print("Warning: No tools initialized successfully. Using fallback web search tool.")
    research_tools = [web_search_fallback]
else:
    print(f"Successfully initialized {len(research_tools)} research tools")
