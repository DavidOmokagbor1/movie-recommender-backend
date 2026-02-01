# Endpoint Testing Guide

This document describes how to test all backend endpoints and verify frontend-backend communication.

## Quick Start

### Prerequisites

1. Backend server running (default: `http://localhost:5555`)
2. Python 3.7+ with `requests` library installed

### Install Dependencies

```bash
pip install requests
```

Or if using the full requirements:

```bash
pip install -r requirements.txt
```

### Run Tests

#### Basic Test (Default Configuration)

```bash
cd fullstack_recsys/backend
python test_endpoints.py
```

#### Test Against Production/Staging

```bash
# Test against deployed backend
TEST_API_URL=https://movie-recommender-backend.onrender.com python test_endpoints.py

# Test with specific frontend origin for CORS
TEST_API_URL=https://movie-recommender-backend.onrender.com \
TEST_FRONTEND_ORIGIN=https://your-app.vercel.app \
python test_endpoints.py
```

## What Gets Tested

### Core Endpoints

1. **GET /init** - Initialize and load all movies
2. **GET /api/movies** - Get paginated movies
3. **GET /api/movies/<id>** - Get movie by ID
4. **GET /api/movies/<id>/details** - Get enhanced movie details
5. **GET /api/movies/search** - Search movies by title/genre
6. **GET /api/stats** - Get database statistics
7. **POST /recommend** - Get movie recommendations

### Error Handling

- 404 Not Found (non-existent movie/endpoint)
- 400 Bad Request (missing/invalid parameters)
- Empty context validation
- Missing required fields

### CORS Configuration

- Preflight OPTIONS requests
- CORS headers presence
- Cross-origin request support

### Frontend-Backend Communication

Verifies that all endpoints used by the React frontend are working:
- `/init` - Used on app startup
- `/recommend` - Used for getting recommendations
- `/api/movies/{id}/details` - Used for movie detail modal

## Test Output

The test script provides:

1. **Individual Test Results**: Each endpoint test shows:
   - ✅ PASS or ❌ FAIL
   - Test description
   - Response details (on failure)

2. **Summary Statistics**:
   - Total tests run
   - Passed/Failed counts
   - Success rate percentage

3. **Frontend-Backend Verification**:
   - Status of endpoints critical for frontend functionality

## Example Output

```
======================================================================
Movie Recommender Backend - Endpoint Testing
======================================================================
Testing against: http://localhost:5555
Frontend Origin: http://localhost:3000
======================================================================

Testing GET /init endpoint...
✅ PASS: GET /init - Initialize movies
   Should return all movies
   Found sample movie ID: 0

Testing GET /api/movies endpoint...
✅ PASS: GET /api/movies - Paginated movies
   Should return paginated movies

...

======================================================================
Test Summary
======================================================================
Total Tests: 16
✅ Passed: 15
❌ Failed: 1
Success Rate: 93.8%

======================================================================
Frontend-Backend Communication Verification
======================================================================

✅ Load movies on app start: Working
✅ Get recommendations: Working
✅ Load movie details in modal: Working

======================================================================
```

## Troubleshooting

### Backend Not Running

If you see connection errors:

```bash
# Make sure backend is running
cd fullstack_recsys/backend
flask run
# or
python run.py
```

### CORS Issues

If CORS tests fail:

1. Check `app/__init__.py` CORS configuration
2. Verify `VERCEL_URL` environment variable is set (for production)
3. Ensure frontend origin is in allowed origins list

### ML API Not Available

The `/recommend` endpoint requires the ML API to be running. If it's not available:

- The test will show a 503 error (expected)
- This is acceptable if ML API is deployed separately
- Frontend will handle this gracefully

### MongoDB Connection Issues

If database-related tests fail:

1. Check MongoDB connection string in environment variables
2. Verify MongoDB Atlas IP whitelist allows your IP
3. Check `db_helper.py` for database connection logic

## Integration with CI/CD

You can integrate this test script into your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Test Backend Endpoints
  run: |
    cd fullstack_recsys/backend
    python test_endpoints.py
  env:
    TEST_API_URL: ${{ secrets.TEST_API_URL }}
```

## Manual Testing Checklist

For manual verification, test these scenarios:

- [ ] Frontend loads movies from `/init`
- [ ] Search functionality works (`/api/movies/search`)
- [ ] Movie selection works (client-side)
- [ ] Recommendations work (`/recommend`)
- [ ] Movie detail modal loads (`/api/movies/{id}/details`)
- [ ] No CORS errors in browser console
- [ ] Error handling works (try invalid movie ID)
- [ ] Pagination works (`/api/movies?page=1&per_page=10`)

## Notes

- The test script uses a sample movie ID from the `/init` response
- Some tests may be skipped if no sample movie is available
- The ML API endpoint (`/recommend`) may fail if ML service is not running (expected in some deployments)
- CORS tests verify preflight requests, which are critical for frontend-backend communication




