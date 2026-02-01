# Frontend Integration Guide

This guide helps frontend developers integrate with the Movie Recommender Backend API.

## Quick Start

### 1. API Base URL Configuration

Set your API base URL based on environment:

**Local Development:**
```swift
// Swift/SwiftUI example
let API_BASE_URL = "http://localhost:5555"
```

**Production:**
```swift
let API_BASE_URL = "https://your-backend-api.onrender.com"
```

### 2. Make Your First Request

**Get All Movies:**
```swift
// Swift example
let url = URL(string: "\(API_BASE_URL)/api/movies?page=1&per_page=20")!
let (data, _) = try await URLSession.shared.data(from: url)
let response = try JSONDecoder().decode(MoviesResponse.self, from: data)
```

**JavaScript/TypeScript example:**
```javascript
const response = await fetch('http://localhost:5555/api/movies?page=1&per_page=20');
const data = await response.json();
console.log(data.result); // Array of movies
```

---

## API Service Layer

### Recommended Structure

Create an API service class to handle all API calls:

**Swift Example:**
```swift
class MovieAPIService {
    private let baseURL = "http://localhost:5555"
    private var authToken: String?
    
    func setAuthToken(_ token: String) {
        self.authToken = token
    }
    
    func getMovies(page: Int = 1, perPage: Int = 20) async throws -> [Movie] {
        let url = URL(string: "\(baseURL)/api/movies?page=\(page)&per_page=\(perPage)")!
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(MoviesResponse.self, from: data)
        return response.result
    }
    
    func getRecommendations(movieIds: [Int], model: String = "EASE") async throws -> [Movie] {
        let url = URL(string: "\(baseURL)/recommend")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        let body = ["model": model, "context": movieIds]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        let response = try JSONDecoder().decode(RecommendationResponse.self, from: data)
        return response.result
    }
}
```

**JavaScript/TypeScript Example:**
```typescript
class MovieAPIService {
    private baseURL = 'http://localhost:5555';
    private authToken: string | null = null;
    
    setAuthToken(token: string) {
        this.authToken = token;
    }
    
    private async request(endpoint: string, options: RequestInit = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...options.headers,
        };
        
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        const response = await fetch(url, {
            ...options,
            headers,
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return response.json();
    }
    
    async getMovies(page = 1, perPage = 20) {
        const data = await this.request(`/api/movies?page=${page}&per_page=${perPage}`);
        return data.result;
    }
    
    async getRecommendations(movieIds: number[], model = 'EASE') {
        const data = await this.request('/recommend', {
            method: 'POST',
            body: JSON.stringify({
                model,
                context: movieIds,
            }),
        });
        return data.result;
    }
}
```

---

## Data Models

### Movie Model

**Swift:**
```swift
struct Movie: Codable, Identifiable {
    let id: Int
    let title: String
    let genre: String
    let date: String
    let poster: String?
}
```

**TypeScript:**
```typescript
interface Movie {
    id: number;
    title: string;
    genre: string;
    date: string;
    poster: string | null;
}
```

### Response Models

**Swift:**
```swift
struct MoviesResponse: Codable {
    let result: [Movie]
    let pagination: Pagination?
}

struct Pagination: Codable {
    let page: Int
    let perPage: Int
    let total: Int
    let pages: Int
}

struct RecommendationResponse: Codable {
    let result: [Movie]
}
```

---

## Key Features Integration

### 1. Browse Movies

**Get paginated movies:**
```swift
let movies = try await apiService.getMovies(page: 1, perPage: 20)
```

### 2. Search Movies

**Search by title:**
```swift
let url = URL(string: "\(baseURL)/api/movies/search?q=\(query)")!
// ... make request
```

### 3. Get Recommendations

**Get recommendations based on selected movies:**
```swift
let recommendations = try await apiService.getRecommendations(
    movieIds: [1, 2, 3],
    model: "EASE"
)
```

**Available Models:**
- `EASE` - Fast, efficient (recommended for most cases)
- `ItemKNN` - Item-based collaborative filtering
- `NeuralMF` - Neural network model (requires PyTorch)
- `DeepFM` - Deep factorization machine (requires PyTorch)

### 4. User Authentication

**Register:**
```swift
let url = URL(string: "\(baseURL)/api/auth/register")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body = [
    "username": "user123",
    "email": "user@example.com",
    "password": "password123"
]
request.httpBody = try JSONSerialization.data(withJSONObject: body)

let (data, _) = try await URLSession.shared.data(for: request)
let response = try JSONDecoder().decode(AuthResponse.self, from: data)
// Save response.token for future requests
```

**Login:**
```swift
// Similar to register, but use /api/auth/login endpoint
// Save the token and use it for authenticated requests
apiService.setAuthToken(response.token)
```

### 5. Get Trending Movies

```swift
let url = URL(string: "\(baseURL)/api/trending")!
// ... make GET request
```

---

## Error Handling

**Swift:**
```swift
do {
    let movies = try await apiService.getMovies()
} catch {
    if let apiError = error as? APIError {
        switch apiError {
        case .unauthorized:
            // Handle authentication error
        case .notFound:
            // Handle not found
        case .serverError:
            // Handle server error
        }
    }
}
```

**TypeScript:**
```typescript
try {
    const movies = await apiService.getMovies();
} catch (error) {
    if (error.response?.status === 401) {
        // Handle authentication error
    } else if (error.response?.status === 404) {
        // Handle not found
    }
}
```

---

## Best Practices

### 1. Environment Configuration

Use environment variables or configuration files:

```swift
enum Environment {
    case development
    case production
    
    var apiBaseURL: String {
        switch self {
        case .development:
            return "http://localhost:5555"
        case .production:
            return "https://your-backend-api.onrender.com"
        }
    }
}
```

### 2. Token Management

Store JWT tokens securely:

```swift
// iOS Keychain
import Security

func saveToken(_ token: String) {
    // Save to Keychain
}

func loadToken() -> String? {
    // Load from Keychain
}
```

### 3. Request Retry Logic

Implement retry for failed requests:

```swift
func requestWithRetry<T>(_ request: () async throws -> T, maxRetries: Int = 3) async throws -> T {
    var lastError: Error?
    for _ in 0..<maxRetries {
        do {
            return try await request()
        } catch {
            lastError = error
            try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
        }
    }
    throw lastError!
}
```

### 4. Loading States

Show loading indicators during API calls:

```swift
@State private var isLoading = false
@State private var movies: [Movie] = []

func loadMovies() async {
    isLoading = true
    defer { isLoading = false }
    
    movies = try await apiService.getMovies()
}
```

---

## Testing

### Test API Connection

```bash
# Health check
curl http://localhost:5555/health

# Get movies
curl http://localhost:5555/api/movies?page=1&per_page=5
```

### Test Recommendations

```bash
curl -X POST http://localhost:5555/recommend \
  -H "Content-Type: application/json" \
  -d '{"model": "EASE", "context": [1, 2, 3]}'
```

---

## Common Issues

### CORS Errors
- Backend has CORS enabled for all origins
- If you encounter CORS issues, check that the backend is running

### Connection Refused
- Ensure backend is running on the correct port (5555)
- Check firewall settings

### Authentication Errors
- Verify token is included in Authorization header
- Check token hasn't expired
- Ensure token format: `Bearer <token>`

---

## Support

For API questions or issues:
1. Check [API Reference](API_REFERENCE.md)
2. Review error messages in API responses
3. Test endpoints with curl or Postman first

---

## Example: Complete Integration

**SwiftUI Example:**
```swift
import SwiftUI

struct MovieListView: View {
    @StateObject private var viewModel = MovieViewModel()
    
    var body: some View {
        NavigationView {
            List(viewModel.movies) { movie in
                MovieRow(movie: movie)
            }
            .onAppear {
                Task {
                    await viewModel.loadMovies()
                }
            }
        }
    }
}

class MovieViewModel: ObservableObject {
    @Published var movies: [Movie] = []
    private let apiService = MovieAPIService()
    
    func loadMovies() async {
        do {
            movies = try await apiService.getMovies()
        } catch {
            print("Error loading movies: \(error)")
        }
    }
}
```

---

Happy coding! 🎬
