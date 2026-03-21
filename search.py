from ddgs import DDGS

def web_search(query: str, max_results: int = 5) -> list:
    """Free web search using DuckDuckGo"""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r["title"],
                "url": r["href"],
                "snippet": r["body"]
            })
    return results

def format_search_results(results: list) -> str:
    """Format search results into readable text"""
    if not results:
        return "No results found."
    
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(
            f"{i}. {r['title']}\n"
            f"   {r['snippet']}\n"
            f"   Source: {r['url']}"
        )
    return "\n\n".join(formatted)
