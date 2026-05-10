"""
Paper Retrieval Service
Search for related papers using arXiv and Semantic Scholar APIs
"""

import requests
from typing import List, Dict, Any
import time
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache for search results
_search_cache = {}

class PaperRetriever:
    """Search for papers from external APIs with retry logic and caching."""
    
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
    
    # Default headers
    HEADERS = {
        "User-Agent": "ResearchMindAI/1.0 (+https://github.com/yourusername/researchmind-ai)"
    }
    
    @staticmethod
    def _get_cache_key(query: str, source: str) -> str:
        """Generate cache key for search results."""
        return f"{source}:{query.lower()}"
    
    @staticmethod
    def search_arxiv(query: str, max_results: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers with retry logic and caching.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            use_cache: Whether to use cached results
        
        Returns:
            List of paper metadata
        """
        # Check cache first
        cache_key = PaperRetriever._get_cache_key(query, "arxiv")
        if use_cache and cache_key in _search_cache:
            logger.info(f"Using cached arXiv results for: {query}")
            return _search_cache[cache_key]
        
        papers = []
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                params = {
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "relevance",
                    "sortOrder": "descending"
                }
                
                # Increased timeout to 30 seconds
                response = requests.get(
                    PaperRetriever.ARXIV_API_URL,
                    params=params,
                    timeout=30,
                    headers=PaperRetriever.HEADERS
                )
                response.raise_for_status()
                
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                namespace = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for entry in root.findall('atom:entry', namespace):
                    paper = {
                        "source": "arXiv",
                        "title": entry.find('atom:title', namespace).text.strip(),
                        "authors": [author.find('atom:name', namespace).text 
                                   for author in entry.findall('atom:author', namespace)],
                        "summary": entry.find('atom:summary', namespace).text.strip(),
                        "published": entry.find('atom:published', namespace).text,
                        "arxiv_id": entry.find('atom:id', namespace).text.split('/abs/')[-1],
                        "url": entry.find('atom:id', namespace).text.replace('abs', 'pdf') + '.pdf'
                    }
                    papers.append(paper)
                
                # Cache results
                _search_cache[cache_key] = papers
                logger.info(f"Found {len(papers)} papers on arXiv for: {query}")
                return papers
                
            except requests.exceptions.Timeout:
                wait_time = 2 ** attempt
                logger.warning(f"arXiv timeout (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"arXiv error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        logger.warning(f"Failed to fetch from arXiv after {max_retries} attempts")
        return []
    
    @staticmethod
    def search_semantic_scholar(query: str, max_results: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers with retry logic and rate limit handling.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            use_cache: Whether to use cached results
        
        Returns:
            List of paper metadata
        """
        # Check cache first
        cache_key = PaperRetriever._get_cache_key(query, "semantic_scholar")
        if use_cache and cache_key in _search_cache:
            logger.info(f"Using cached Semantic Scholar results for: {query}")
            return _search_cache[cache_key]
        
        papers = []
        max_retries = 4
        
        for attempt in range(max_retries):
            try:
                params = {
                    "query": query,
                    "limit": max_results,
                    "fields": "title,authors,abstract,year,url,citationCount"
                }
                
                response = requests.get(
                    PaperRetriever.SEMANTIC_SCHOLAR_API_URL,
                    params=params,
                    timeout=30,
                    headers=PaperRetriever.HEADERS
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 3  # Exponential backoff: 3s, 6s, 12s, 24s
                    logger.warning(f"Semantic Scholar rate limit (429). Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                
                for paper in data.get("data", []):
                    paper_data = {
                        "source": "Semantic Scholar",
                        "title": paper.get("title", "Unknown"),
                        "authors": [f"{a['name']}" for a in paper.get("authors", [])],
                        "abstract": paper.get("abstract", ""),
                        "year": paper.get("year"),
                        "url": paper.get("url", ""),
                        "citation_count": paper.get("citationCount", 0),
                        "paper_id": paper.get("paperId", "")
                    }
                    papers.append(paper_data)
                
                # Cache results
                _search_cache[cache_key] = papers
                logger.info(f"Found {len(papers)} papers on Semantic Scholar for: {query}")
                return papers
                
            except requests.exceptions.Timeout:
                wait_time = 2 ** attempt
                logger.warning(f"Semantic Scholar timeout (attempt {attempt + 1}/{max_retries}). Waiting {wait_time}s...")
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                continue
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Semantic Scholar error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                continue
        
        logger.warning(f"Failed to fetch from Semantic Scholar after {max_retries} attempts")
        return []
    
    @staticmethod
    def search_both(query: str, max_results: int = 5, use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search both arXiv and Semantic Scholar with caching and retry logic.
        
        Args:
            query: Search query
            max_results: Maximum number of results per source
            use_cache: Whether to use cached results
        
        Returns:
            Dictionary with results from both sources
        """
        arxiv_results = PaperRetriever.search_arxiv(query, max_results, use_cache)
        time.sleep(1)  # Rate limiting
        semantic_results = PaperRetriever.search_semantic_scholar(query, max_results, use_cache)
        
        return {
            "arxiv": arxiv_results,
            "semantic_scholar": semantic_results,
            "total": len(arxiv_results) + len(semantic_results)
        }
    
    @staticmethod
    def extract_keywords(text: str, num_keywords: int = 5) -> List[str]:
        """
        Extract keywords from text for retrieval.
        
        Args:
            text: Text to extract keywords from
            num_keywords: Number of keywords to extract
        
        Returns:
            List of keywords
        """
        # Simple keyword extraction (can be improved with YAKE or KeyBERT)
        from collections import Counter
        
        # Simple tokenization and filtering
        words = text.lower().split()
        # Filter common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'this', 'that', 'these', 'those', 'which', 'who', 'what', 'when', 'where'
        }
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
        most_common = Counter(filtered_words).most_common(num_keywords)
        
        return [word for word, _ in most_common]


# Convenience functions
def search_papers(query: str, max_results: int = 5, use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """Search for papers using both APIs with caching."""
    return PaperRetriever.search_both(query, max_results, use_cache)


def extract_keywords(text: str, num_keywords: int = 5) -> List[str]:
    """Extract keywords from text."""
    return PaperRetriever.extract_keywords(text, num_keywords)


def clear_search_cache():
    """Clear the search cache."""
    global _search_cache
    _search_cache.clear()
    logger.info("Search cache cleared")


def get_cache_size():
    """Get the current cache size."""
    return len(_search_cache)


def get_cached_query(cache_key: str):
    """Get a cached result by key."""
    return _search_cache.get(cache_key)
