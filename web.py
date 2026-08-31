import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def web_search(query: str) -> list:
    """
    Search the Internet for current or external information.

    Args:
        query: The search query.

    Returns:
        A list of search results containing title, URL,
        content, and relevance score.
    """

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=5,
    )

    results = []

    for result in response.get("results", []):

        results.append(
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "content": result.get("content"),
                "score": result.get("score"),
            }
        )

    return results
