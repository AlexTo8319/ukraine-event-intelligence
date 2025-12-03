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
        # Timeframe: next 6 months
        queries = []
        
        # Group A: Planning - focus on specific organizations and real event sources
        planning_keywords = [
            "urban planning Ukraine conference 2025 site:ua",
            "урбаністика Україна конференція 2025",
            "ro3kvit urban planning events Ukraine",
            "cities alliance Ukraine urban recovery"
        ]
        
        # Group B: Recovery - focus on official sources
        recovery_keywords = [
            "Ukraine reconstruction conference 2025 site:gov.ua",
            "відбудова України конференція грудень 2025",
            "Ukraine recovery forum EU 2025",
            "rebuild Ukraine conference registration"
        ]
        
        # Group C: Housing - focus on policy events
        housing_keywords = [
            "housing policy Ukraine forum 2025",
            "affordable housing conference Ukraine site:eu",
            "житлова політика форум Україна 2025"
        ]
        
        # Group D: Governance and capacity building
        governance_keywords = [
            "decentralization Ukraine conference 2025",
            "municipal governance forum Ukraine",
            "місцеве самоврядування форум Україна 2025"
        ]
        
        # Group E: Specific organizations known for real events
        org_keywords = [
            "UNDP Ukraine urban events 2025",
            "World Bank Ukraine reconstruction conference",
            "European Commission Ukraine recovery event"
        ]
        
        # Group F: Energy and sustainability events
        energy_keywords = [
            "energy week Ukraine 2025",
            "тиждень енергоефективності Україна 2025",
            "sustainable energy Ukraine conference",
            "green reconstruction Ukraine forum",
            "энергетический форум Украина 2025"
        ]
        
        # Group G: Infrastructure and construction
        infrastructure_keywords = [
            "infrastructure Ukraine conference 2025",
            "construction forum Ukraine грудень",
            "budivelnyk Ukraine congress"
        ]
        
        # Combine all keywords
        all_keywords = planning_keywords + recovery_keywords + housing_keywords + governance_keywords + org_keywords + energy_keywords + infrastructure_keywords
        
        return all_keywords
    
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
                search_depth="advanced",  # Using advanced for better results and URL extraction
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

