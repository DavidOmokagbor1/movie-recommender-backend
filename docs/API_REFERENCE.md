# API Reference

Complete API documentation for the Movie Recommender Backend.

## Base URLs

### Local Development
- **Backend API**: `http://localhost:5555`
- **ML API**: `http://localhost:8000`

### Production
- **Backend API**: Set by your deployment platform
- **ML API**: Set by your deployment platform

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

---

## Movie Endpoints

### Get All Movies (Paginated)

Get a paginated list of all movies.

**Endpoint:** `GET /api/movies`

**Query Parameters:**
- `page` (optional, default: 1) - Page number
- `per_page` (optional, default: 50, max: 100) - Items per page

**Example Request:**
```bash
curl http://localhost:5555/api/movies?page=1&per_page=20
```

**Response:**
```json
{
  "result": [
    {
      "id": 1,
      "title": "Toy Story",
      "genre": "Animation|Children|Comedy",
      "date": "1995-01-01",
      "poster": "https://..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1682,
    "pages": 85
  }
}
```

---

### Search Movies

Search movies by title or filter by genre.

**Endpoint:** `GET /api/movies/search`

**Query Parameters:**
- `q` (optional) - Search query (searches in movie title)
- `genre` (optional) - Filter by genre

**Example Request:**
```bash
curl "http://localhost:5555/api/movies/search?q=action&genre=Action"
```

**Response:**
```json
{
  "result": [
    {
      "id": 123,
      "title": "Action Movie",
      "genre": "Action|Thriller",
      "date": "2020-01-01",
      "poster": "https://..."
    }
  ],
  "count": 1,
  "query": "action",
  "genre": "Action"
}
```

---

### Get Movie by ID

Get a specific movie by its ID.

**Endpoint:** `GET /api/movies/<movie_id>`

**Example Request:**
```bash
curl http://localhost:5555/api/movies/1
```

**Response:**
```json
{
  "result": {
    "id": 1,
    "title": "Toy Story",
    "genre": "Animation|Children|Comedy",
    "date": "1995-01-01",
    "poster": "https://..."
  }
}
```

---

### Get Enhanced Movie Details

Get detailed movie information including cast, crew, and ratings from TMDB.

**Endpoint:** `GET /api/movies/<movie_id>/details`

**Example Request:**
```bash
curl http://localhost:5555/api/movies/1/details
```

**Response:**
```json
{
  "result": {
    "id": 1,
    "title": "Toy Story",
    "genre": "Animation|Children|Comedy",
    "date": "1995-01-01",
    "poster": "https://...",
    "enhanced": {
      "overview": "Movie description...",
      "cast": [...],
      "crew": [...],
      "rating": 8.3
    }
  }
}
```

---

### Get Trending Movies

Get currently trending movies.

**Endpoint:** `GET /api/trending`

**Example Request:**
```bash
curl http://localhost:5555/api/trending
```

**Response:**
```json
{
  "result": [
    {
      "id": 123,
      "title": "Popular Movie",
      "genre": "Action",
      "date": "2024-01-01",
      "poster": "https://..."
    }
  ]
}
```

---

## Recommendation Endpoints

### Get Recommendations

Get personalized movie recommendations based on selected movies.

**Endpoint:** `POST /recommend`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <token> (optional, for logging interactions)
```

**Request Body:**
```json
{
  "model": "EASE",
  "context": [1, 2, 3]
}
```

**Parameters:**
- `model` (required) - One of: `EASE`, `ItemKNN`, `NeuralMF`, `DeepFM`
- `context` (required) - Array of movie IDs that the user likes

**Example Request:**
```bash
curl -X POST http://localhost:5555/recommend \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "model": "EASE",
    "context": [1, 2, 3]
  }'
```

**Response:**
```json
{
  "result": [
    {
      "id": 456,
      "title": "Recommended Movie",
      "genre": "Action|Drama",
      "date": "2020-01-01",
      "poster": "https://..."
    }
  ]
}
```

**Available Models:**
- `EASE` - Embarrassingly Shallow Autoencoders (fast, efficient)
- `ItemKNN` - Item-based Collaborative Filtering
- `NeuralMF` - Neural Matrix Factorization (requires PyTorch)
- `DeepFM` - Deep Factorization Machine (requires PyTorch)

---

## Authentication Endpoints

### Register User

Create a new user account.

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "age": 25,
  "gender": "M"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:5555/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "secure_password",
    "age": 25,
    "gender": "M"
  }'
```

**Response:**
```json
{
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    "gender": "M"
  }
}
```

---

### Login User

Authenticate and get JWT token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:5555/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "secure_password"
  }'
```

**Response:**
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    "gender": "M"
  }
}
```

---

### Get Current User

Get the authenticated user's information.

**Endpoint:** `GET /api/auth/user`

**Headers:**
```
Authorization: Bearer <token>
```

**Example Request:**
```bash
curl http://localhost:5555/api/auth/user \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "user": {
    "id": "123",
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    "gender": "M"
  }
}
```

---

## Utility Endpoints

### Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Example Request:**
```bash
curl http://localhost:5555/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "MongoDB",
  "db_status": "connected",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

### Get Statistics

Get database statistics (movies, users, interactions, genres).

**Endpoint:** `GET /api/stats`

**Example Request:**
```bash
curl http://localhost:5555/api/stats
```

**Response:**
```json
{
  "result": {
    "database": "MongoDB",
    "movies": 1682,
    "users": 943,
    "interactions": 100000,
    "genres": {
      "Action": 251,
      "Comedy": 505,
      "Drama": 436
    }
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## Error Responses

All endpoints may return the following error formats:

### 400 Bad Request
```json
{
  "message": "Error description",
  "error": "ERROR_CODE"
}
```

### 401 Unauthorized
```json
{
  "message": "Authorization token required",
  "error": "MISSING_TOKEN"
}
```

### 404 Not Found
```json
{
  "message": "Resource not found",
  "error": "NOT_FOUND"
}
```

### 500 Internal Server Error
```json
{
  "message": "Internal server error",
  "error": "INTERNAL_ERROR"
}
```

### 503 Service Unavailable
```json
{
  "message": "ML API unavailable",
  "error": "API_CONNECTION_ERROR"
}
```

---

## Rate Limiting

Currently, there are no rate limits. In production, consider implementing rate limiting.

## CORS

CORS is enabled for all origins. In production, restrict to specific frontend domains.
