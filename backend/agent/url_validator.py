"""URL validation and accessibility checking."""
import requests
from typing import Optional, Tuple, Dict
from urllib.parse import urlparse
import time


class URLValidator:
    """Validates URLs and checks if they are accessible."""
    
    def __init__(self, timeout: int = 5, max_redirects: int = 5):
        """
        Initialize URL validator.
        
        Args:
            timeout: Request timeout in seconds
            max_redirects: Maximum number of redirects to follow
        """
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.session = requests.Session()
        self.session.max_redirects = max_redirects
    
    def is_valid_url_format(self, url: str) -> bool:
        """Check if URL has valid format."""
        if not url or not isinstance(url, str):
            return False
        
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except Exception:
            return False
    
    def check_url_accessibility(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL is accessible.
        
        Args:
            url: URL to check
            
        Returns:
            Tuple of (is_accessible: bool, error_message: Optional[str])
        """
        if not self.is_valid_url_format(url):
            return False, "Invalid URL format"
        
        try:
            # Use HEAD request first (faster, doesn't download content)
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; EventIntelligenceBot/1.0)'
                }
            )
            
            # If HEAD is not allowed, try GET
            if response.status_code == 405:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (compatible; EventIntelligenceBot/1.0)'
                    },
                    stream=True  # Don't download full content
                )
            
            # Check if status is successful (2xx or 3xx)
            if 200 <= response.status_code < 400:
                return True, None
            else:
                return False, f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.TooManyRedirects:
            return False, "Too many redirects"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except requests.exceptions.RequestException as e:
            return False, f"Request error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def validate_urls(self, urls: list, check_accessibility: bool = True) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Validate multiple URLs.
        
        Args:
            urls: List of URLs to validate
            check_accessibility: Whether to check if URLs are accessible (slower but more thorough)
            
        Returns:
            Dict mapping URL to (is_valid, error_message) tuple
        """
        results = {}
        
        for url in urls:
            if not url:
                results[url] = (False, "Empty URL")
                continue
            
            if not self.is_valid_url_format(url):
                results[url] = (False, "Invalid URL format")
                continue
            
            if check_accessibility:
                is_accessible, error = self.check_url_accessibility(url)
                results[url] = (is_accessible, error)
            else:
                results[url] = (True, None)
            
            # Small delay to avoid rate limiting
            if check_accessibility:
                time.sleep(0.1)
        
        return results

