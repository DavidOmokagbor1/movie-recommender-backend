#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for Movie Recommender Backend
Tests all endpoints and verifies frontend-backend communication
"""

import requests
import json
import sys
import os
from typing import Dict, List, Tuple

# Configuration
BASE_URL = os.getenv('TEST_API_URL', 'http://localhost:5555')
FRONTEND_ORIGIN = os.getenv('TEST_FRONTEND_ORIGIN', 'http://localhost:3000')

# Test results
test_results: List[Dict] = []

def log_test(name: str, passed: bool, message: str = "", details: Dict = None):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = {
        "name": name,
        "passed": passed,
        "message": message,
        "details": details or {}
    }
    test_results.append(result)
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")
    if details and not passed:
        print(f"   Details: {json.dumps(details, indent=2)}")
    print()

def test_endpoint(method: str, endpoint: str, expected_status: int = 200, 
                  data: Dict = None, headers: Dict = None, description: str = None) -> Tuple[bool, Dict]:
    """Test an endpoint and return (success, response_data)"""
    url = f"{BASE_URL}{endpoint}"
    test_name = description or f"{method} {endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        success = response.status_code == expected_status
        response_data = {}
        
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text[:200]}
        
        return success, {
            "status_code": response.status_code,
            "expected": expected_status,
            "response": response_data,
            "headers": dict(response.headers)
        }
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}

def test_cors_headers(endpoint: str, method: str = 'GET') -> Tuple[bool, Dict]:
    """Test CORS headers"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        # Test preflight OPTIONS request
        options_response = requests.options(
            url,
            headers={
                'Origin': FRONTEND_ORIGIN,
                'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            },
            timeout=10
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers'),
        }
        
        # Check if CORS headers are present
        has_cors = any(cors_headers.values())
        
        return has_cors, {
            "cors_headers": cors_headers,
            "status_code": options_response.status_code
        }
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}

def main():
    """Run all tests"""
    print("=" * 70)
    print("Movie Recommender Backend - Endpoint Testing")
    print("=" * 70)
    print(f"Testing against: {BASE_URL}")
    print(f"Frontend Origin: {FRONTEND_ORIGIN}")
    print("=" * 70)
    print()
    
    # Test 1: Health check - GET /init
    print("Testing GET /init endpoint...")
    success, details = test_endpoint('GET', '/init', 200, 
                                     description="GET /init - Initialize movies")
    log_test("GET /init", success, 
             "Should return all movies" if success else "Failed to load movies",
             details)
    
    # Get a sample movie ID for subsequent tests
    sample_movie_id = None
    if success and 'result' in details.get('response', {}) and details['response']['result']:
        sample_movie_id = details['response']['result'][0].get('id')
        print(f"   Found sample movie ID: {sample_movie_id}")
    
    # Test 2: GET /api/movies (with pagination)
    print("Testing GET /api/movies endpoint...")
    success, details = test_endpoint('GET', '/api/movies?page=1&per_page=10', 200,
                                     description="GET /api/movies - Paginated movies")
    log_test("GET /api/movies", success,
             "Should return paginated movies" if success else "Failed to get paginated movies",
             details)
    
    # Test 3: GET /api/movies/<id>
    if sample_movie_id is not None:
        print(f"Testing GET /api/movies/{sample_movie_id} endpoint...")
        success, details = test_endpoint('GET', f'/api/movies/{sample_movie_id}', 200,
                                         description=f"GET /api/movies/{sample_movie_id} - Get movie by ID")
        log_test(f"GET /api/movies/{sample_movie_id}", success,
                 "Should return movie details" if success else "Failed to get movie",
                 details)
    else:
        log_test("GET /api/movies/<id>", False, "Skipped - no sample movie ID available")
    
    # Test 4: GET /api/movies/<id> - 404 test
    print("Testing GET /api/movies/99999 (404 test)...")
    success, details = test_endpoint('GET', '/api/movies/99999', 404,
                                     description="GET /api/movies/99999 - 404 Not Found")
    log_test("GET /api/movies/99999 (404)", success,
             "Should return 404" if success else "Should return 404 for non-existent movie",
             details)
    
    # Test 5: GET /api/movies/<id>/details
    if sample_movie_id is not None:
        print(f"Testing GET /api/movies/{sample_movie_id}/details endpoint...")
        success, details = test_endpoint('GET', f'/api/movies/{sample_movie_id}/details', 200,
                                         description=f"GET /api/movies/{sample_movie_id}/details - Enhanced details")
        log_test(f"GET /api/movies/{sample_movie_id}/details", success,
                 "Should return enhanced movie details" if success else "Failed to get enhanced details",
                 details)
    else:
        log_test("GET /api/movies/<id>/details", False, "Skipped - no sample movie ID available")
    
    # Test 6: GET /api/movies/search - by title
    print("Testing GET /api/movies/search?q=star endpoint...")
    success, details = test_endpoint('GET', '/api/movies/search?q=star', 200,
                                     description="GET /api/movies/search - Search by title")
    log_test("GET /api/movies/search (title)", success,
             "Should return search results" if success else "Failed to search movies",
             details)
    
    # Test 7: GET /api/movies/search - by genre
    print("Testing GET /api/movies/search?genre=Action endpoint...")
    success, details = test_endpoint('GET', '/api/movies/search?genre=Action', 200,
                                     description="GET /api/movies/search - Filter by genre")
    log_test("GET /api/movies/search (genre)", success,
             "Should return filtered results" if success else "Failed to filter by genre",
             details)
    
    # Test 8: GET /api/movies/search - missing parameter
    print("Testing GET /api/movies/search (missing params - 400 test)...")
    success, details = test_endpoint('GET', '/api/movies/search', 400,
                                     description="GET /api/movies/search - Missing parameters")
    log_test("GET /api/movies/search (400)", success,
             "Should return 400 for missing parameters" if success else "Should validate parameters",
             details)
    
    # Test 9: GET /api/stats
    print("Testing GET /api/stats endpoint...")
    success, details = test_endpoint('GET', '/api/stats', 200,
                                     description="GET /api/stats - Database statistics")
    log_test("GET /api/stats", success,
             "Should return database statistics" if success else "Failed to get stats",
             details)
    
    # Test 10: POST /recommend - valid request
    if sample_movie_id is not None:
        print("Testing POST /recommend endpoint...")
        recommend_data = {
            "context": [sample_movie_id],
            "model": "ItemKNN"
        }
        success, details = test_endpoint('POST', '/recommend', 200,
                                         data=recommend_data,
                                         description="POST /recommend - Get recommendations")
        log_test("POST /recommend", success,
                 "Should return recommendations" if success else "Failed to get recommendations (may need ML API running)",
                 details)
    else:
        log_test("POST /recommend", False, "Skipped - no sample movie ID available")
    
    # Test 11: POST /recommend - missing context
    print("Testing POST /recommend (missing context - 400 test)...")
    recommend_data = {"model": "EASE"}
    success, details = test_endpoint('POST', '/recommend', 400,
                                     data=recommend_data,
                                     description="POST /recommend - Missing context")
    log_test("POST /recommend (missing context)", success,
             "Should return 400 for missing context" if success else "Should validate request body",
             details)
    
    # Test 12: POST /recommend - missing model
    print("Testing POST /recommend (missing model - 400 test)...")
    recommend_data = {"context": [1, 2, 3]}
    success, details = test_endpoint('POST', '/recommend', 400,
                                     data=recommend_data,
                                     description="POST /recommend - Missing model")
    log_test("POST /recommend (missing model)", success,
             "Should return 400 for missing model" if success else "Should validate request body",
             details)
    
    # Test 13: POST /recommend - empty context
    print("Testing POST /recommend (empty context - 400 test)...")
    recommend_data = {"context": [], "model": "EASE"}
    success, details = test_endpoint('POST', '/recommend', 400,
                                     data=recommend_data,
                                     description="POST /recommend - Empty context")
    log_test("POST /recommend (empty context)", success,
             "Should return 400 for empty context" if success else "Should validate context",
             details)
    
    # Test 14: CORS - Test preflight for /init
    print("Testing CORS headers for /init endpoint...")
    success, details = test_cors_headers('/init', 'GET')
    log_test("CORS /init", success,
             "CORS headers present" if success else "CORS headers missing or incorrect",
             details)
    
    # Test 15: CORS - Test preflight for /recommend
    print("Testing CORS headers for /recommend endpoint...")
    success, details = test_cors_headers('/recommend', 'POST')
    log_test("CORS /recommend", success,
             "CORS headers present" if success else "CORS headers missing or incorrect",
             details)
    
    # Test 16: 404 handler
    print("Testing 404 handler...")
    success, details = test_endpoint('GET', '/nonexistent-endpoint', 404,
                                     description="GET /nonexistent-endpoint - 404 handler")
    log_test("404 Handler", success,
             "Should return 404 for non-existent endpoints" if success else "404 handler not working",
             details)
    
    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r['passed'])
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print()
    
    if failed_tests > 0:
        print("Failed Tests:")
        for result in test_results:
            if not result['passed']:
                print(f"  - {result['name']}: {result['message']}")
        print()
    
    # Frontend-Backend Communication Verification
    print("=" * 70)
    print("Frontend-Backend Communication Verification")
    print("=" * 70)
    
    # Check if endpoints used by frontend are working
    frontend_endpoints = [
        ('GET', '/init', 'Load movies on app start'),
        ('POST', '/recommend', 'Get recommendations'),
        ('GET', '/api/movies/{id}/details', 'Load movie details in modal')
    ]
    
    frontend_checks = []
    for method, endpoint, description in frontend_endpoints:
        if '{id}' in endpoint:
            if sample_movie_id:
                target_endpoint = endpoint.replace('{id}', str(sample_movie_id))
            else:
                frontend_checks.append((description, False, "No sample movie ID"))
                continue
        else:
            target_endpoint = endpoint
        
        success, _ = test_endpoint(method, target_endpoint, 200 if method == 'GET' else 200)
        frontend_checks.append((description, success, "Working" if success else "Not working"))
    
    print()
    for description, success, status in frontend_checks:
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {description}: {status}")
    
    print()
    print("=" * 70)
    
    # Return exit code
    return 0 if failed_tests == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

