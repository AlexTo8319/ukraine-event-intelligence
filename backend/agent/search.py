"""Web search functionality using Tavily API."""
import os
from typing import List, Dict
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()


class SearchAgent:
    """Agent for searching the web for relevant events."""
    
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be set in environment variables")
        self.client = TavilyClient(api_key=api_key)
    
    def get_search_queries(self) -> List[str]:
        """
        Generate search queries based on keyword clusters.
        
        Returns:
            List of search query strings
        """
        # Timeframe: next 4 weeks
        queries = []
        
        # Group A: Planning
        planning_keywords = [
            "урбаністика Україна події",
            "урбан-планування Україна конференція",
            "просторове планування Україна",
            "містобудування Україна події",
            "public space Ukraine events",
            "green infrastructure Ukraine conference",
            "urban planning Ukraine events 2024"
        ]
        
        # Group B: Recovery
        recovery_keywords = [
            "відбудова України події",
            "відновлення громад Україна",
            "стійке відновлення Україна",
            "resilient cities Ukraine events",
            "sustainable urban development Ukraine",
            "post-war recovery Ukraine events",
            "Ukraine reconstruction events 2024"
        ]
        
        # Group C: Housing
        housing_keywords = [
            "житлова політика Україна події",
            "доступне житло Україна",
            "housing policy Ukraine events",
            "архітектура Україна конференція",
            "енергоефективність Україна події",
            "affordable housing Ukraine events"
        ]
        
        # Group D: Governance
        governance_keywords = [
            "розвиток спроможності Україна",
            "capacity building Ukraine events",
            "децентралізація Україна події",
            "місцеве самоврядування Україна",
            "municipal governance Ukraine",
            "digital governance Ukraine events"
        ]
        
        # Combine all keywords
        all_keywords = planning_keywords + recovery_keywords + housing_keywords + governance_keywords
        
        # Add timeframe context to each query
        queries = [f"{keyword} наступні 4 тижні" if any(c in keyword for c in "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя") 
                  else f"{keyword} next 4 weeks" for keyword in all_keywords]
        
        return queries
    
    def search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Search the web for a given query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, and content
        """
        try:
            response = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
                include_raw_content=True
            )
            
            results = []
            for result in response.get("results", []):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "raw_content": result.get("raw_content", "")
                })
            
            return results
        except Exception as e:
            print(f"Error searching for query '{query}': {str(e)}")
            return []

