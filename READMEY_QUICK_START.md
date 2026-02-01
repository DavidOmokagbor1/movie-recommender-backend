# Quick Start Guide - For Frontend Team

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Backend API URL (provided by backend team)
- That's it! No backend setup needed.

### For Apple TV Development

**Base API URL:**
```
http://localhost:5555  (Local development)
https://your-backend-url.onrender.com  (Production - when deployed)
```

### Quick Test

```bash
# Test if backend is running
curl http://localhost:5555/health

# Get movies
curl http://localhost:5555/api/movies?page=1&per_page=10
```

### Essential Endpoints

1. **Get Movies**: `GET /api/movies?page=1&per_page=20`
2. **Search**: `GET /api/movies/search?q=star`
3. **Get Movie**: `GET /api/movies/1`
4. **Trending**: `GET /api/trending`
5. **Recommendations**: `POST /recommend` (see API docs)

### Full Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete endpoint documentation
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Step-by-step integration with code examples

### Need Help?

Check the [Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md) for:
- Swift/SwiftUI code examples
- JavaScript/TypeScript examples
- Error handling
- Authentication flow

---

**Backend Repository**: https://github.com/DavidOmokagbor1/apple-tv-prototype-backend
