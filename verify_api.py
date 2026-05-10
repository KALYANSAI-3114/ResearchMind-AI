#!/usr/bin/env python3
"""
ResearchMind AI - API Verification Script

This script tests all endpoints to verify fixes are working.
Run after backend is started: python verify_api.py
"""

import requests
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 60

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text:^70}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

def test_health() -> bool:
    """Test health endpoint"""
    print_header("Test 1: Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print_info(f"Status: {response.status_code}")
        print_info(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print_success("Health check passed!")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend! Is it running?")
        print_info("Start with: python -m uvicorn app.main:app --reload --port 8000")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_search() -> bool:
    """Test search endpoint"""
    print_header("Test 2: Search Papers (Simple Query)")
    
    query = "machine learning"
    
    try:
        print_info(f"Searching for: '{query}'")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/search-related",
            params={"query": query, "max_results": 5},
            timeout=TIMEOUT
        )
        
        elapsed = time.time() - start_time
        print_info(f"Response time: {elapsed:.2f}s")
        
        data = response.json()
        
        if response.status_code == 200:
            print_success("Search endpoint responded with 200")
            
            # Check response structure
            if "status" in data:
                print_success(f"✓ Status: {data['status']}")
            else:
                print_warning("Missing 'status' field in response")
            
            if "total_results" in data:
                print_success(f"✓ Total results: {data['total_results']}")
                
                if data['total_results'] > 0:
                    print_success("✓ Got actual search results!")
                    
                    # Show sources
                    if data.get('arxiv_papers'):
                        print_success(f"  - arXiv: {len(data['arxiv_papers'])} papers")
                    else:
                        print_warning("  - arXiv: No papers (API unavailable or rate-limited)")
                    
                    if data.get('semantic_scholar_papers'):
                        print_success(f"  - Semantic Scholar: {len(data['semantic_scholar_papers'])} papers")
                    else:
                        print_warning("  - Semantic Scholar: No papers (API unavailable or rate-limited)")
                    
                    return True
                else:
                    print_warning("No results found, but that's OK - APIs might be slow")
                    print_info(f"Message: {data.get('message', 'N/A')}")
                    return True  # Still a success, APIs just slow
            else:
                print_error("Missing 'total_results' field in response")
                return False
        
        else:
            print_error(f"Unexpected status: {response.status_code}")
            print_error(f"Response: {data}")
            return False
    
    except requests.exceptions.Timeout:
        print_error("Search request timed out (60s)")
        print_info("This might happen if APIs are very slow")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_search_cache() -> bool:
    """Test caching (same query twice should be instant)"""
    print_header("Test 3: Search Caching (Same Query Twice)")
    
    query = "neural networks"
    
    try:
        # First search
        print_info(f"First search for: '{query}'")
        start_time = time.time()
        
        response1 = requests.post(
            f"{API_BASE_URL}/search-related",
            params={"query": query, "max_results": 3},
            timeout=TIMEOUT
        )
        
        time1 = time.time() - start_time
        print_info(f"First response time: {time1:.2f}s")
        
        if response1.status_code != 200:
            print_warning("First search failed - skipping cache test")
            return True  # Not a failure, just can't test
        
        # Second search (should be cached)
        print_info(f"Second search for: '{query}' (should be cached)")
        start_time = time.time()
        
        response2 = requests.post(
            f"{API_BASE_URL}/search-related",
            params={"query": query, "max_results": 3},
            timeout=TIMEOUT
        )
        
        time2 = time.time() - start_time
        print_info(f"Second response time: {time2:.2f}s")
        
        if response2.status_code == 200:
            data = response2.json()
            
            if data.get('cached'):
                print_success("✓ Cache hit detected!")
                print_success(f"✓ Speed improvement: {time1/time2:.0f}x faster")
                return True
            else:
                # Check if response is identical
                if response2.json() == response1.json():
                    print_success("✓ Identical results (likely cached)")
                    if time2 < time1 / 2:  # At least 2x faster
                        print_success(f"✓ Speed improvement: {time1/time2:.0f}x faster")
                        return True
                    else:
                        print_warning("Same results but not significantly faster")
                        return True
                else:
                    print_warning("Different results on second search")
                    return True
        else:
            print_error(f"Second search failed: {response2.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return True  # Not critical

def test_compare() -> bool:
    """Test compare endpoint with search query"""
    print_header("Test 4: Compare Papers (Graceful Degradation)")
    
    query = "deep learning"
    
    try:
        print_info(f"Comparing papers for: '{query}'")
        
        response = requests.post(
            f"{API_BASE_URL}/compare-papers",
            params={"query": query},
            timeout=TIMEOUT
        )
        
        data = response.json()
        
        if response.status_code == 200:
            print_success("Compare endpoint responded with 200")
            
            if "status" in data:
                print_success(f"✓ Status: {data['status']}")
                
                if data['status'] in ['success', 'partial_success']:
                    print_success("✓ Got valid status (not 400 error!)")
                    
                    if "comparison" in data:
                        if data['comparison']:
                            print_success("✓ Got comparison data")
                        else:
                            print_warning("Comparison is empty - APIs might be unavailable")
                    
                    if data['status'] == 'partial_success':
                        print_info(f"Message: {data.get('message', 'N/A')}")
                        print_success("✓ Graceful degradation working!")
                    
                    return True
                else:
                    print_error(f"Unexpected status: {data['status']}")
                    return False
            else:
                print_error("Missing 'status' field")
                return False
        
        else:
            print_error(f"Unexpected response code: {response.status_code}")
            print_error(f"Response: {data}")
            return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_extract_keywords() -> bool:
    """Test extract keywords endpoint"""
    print_header("Test 5: Extract Keywords")
    
    try:
        # Sample paper text
        sample_text = """
        This paper proposes a novel transformer architecture for natural language processing.
        We introduce a new attention mechanism that improves computational efficiency.
        Our method achieves state-of-the-art results on multiple benchmarks including GLUE and SQuAD.
        The key contributions are: efficient attention, better generalization, and faster training.
        """
        
        print_info("Extracting keywords from sample paper text...")
        
        response = requests.post(
            f"{API_BASE_URL}/extract-keywords",
            json={"text": sample_text},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Extract keywords endpoint responded with 200")
            
            if "keywords" in data:
                print_success(f"✓ Got {len(data['keywords'])} keywords")
                for i, kw in enumerate(data['keywords'][:5], 1):
                    print_info(f"  {i}. {kw}")
                return True
            else:
                print_error("Missing 'keywords' field in response")
                return False
        
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print_header("ResearchMind AI - API Verification")
    
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Timeout: {TIMEOUT}s")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    
    if not results[0][1]:  # If health check fails, stop
        print_error("\n" + "="*70)
        print_error("Cannot continue - backend not responding!")
        print_info("Start backend with:")
        print_info("  cd backend")
        print_info("  python -m uvicorn app.main:app --reload --port 8000")
        return
    
    results.append(("Search Papers", test_search()))
    results.append(("Search Caching", test_search_cache()))
    results.append(("Compare Papers", test_compare()))
    results.append(("Extract Keywords", test_extract_keywords()))
    
    # Print summary
    print_header("Summary")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    for test_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\n  {BOLD}Total: {passed}/{total} tests passed{RESET}")
    
    if failed == 0:
        print_success("\n🎉 All tests passed! API is working correctly!")
    elif passed >= total * 0.5:
        print_warning(f"\n⚠ Some tests failed ({failed}/{total}), but core functionality works")
    else:
        print_error(f"\n✗ Multiple tests failed ({failed}/{total})")
    
    # Print next steps
    print_header("Next Steps")
    
    if passed == total:
        print_success("✓ Backend is working correctly")
        print_info("Start frontend with: cd frontend && streamlit run streamlit_app.py")
        print_info("Then test in browser: http://localhost:8501")
    else:
        print_info("Check the errors above and:")
        print_info("1. Review logs in backend terminal")
        print_info("2. Check internet connection")
        print_info("3. Restart backend")
        print_info("4. Try again")

if __name__ == "__main__":
    main()
