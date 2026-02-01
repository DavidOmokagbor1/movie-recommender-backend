# Movie Recommender Backend API

A production-ready backend API for movie recommendations with machine learning integration. This backend provides RESTful endpoints for movie data, user authentication, and personalized recommendations using multiple ML models.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB Atlas account (for production) or SQLite (for local development)
- pip and virtualenv

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd movie-recommender-backend
```

2. **Set up Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up ML API**
```bash
cd ../api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure Environment Variables**
```bash
cd ../backend
cp ../.env.example .env
# Edit .env with your configuration
```

5. **Initialize Database** (Optional - pre-built DB included)
```bash
cd backend
python initialize_ml100k_db.py
```

6. **Train ML Models** (Optional - pre-trained models included)
```bash
cd api
python fit_offline.py --model EASE --save_dir recommend/ckpt
python fit_offline.py --model ItemKNN --save_dir recommend/ckpt
```

### Running Locally

**Terminal 1 - Backend API:**
```bash
cd backend
python run.py
# Backend runs on http://localhost:5555
```

**Terminal 2 - ML API:**
```bash
cd api
python api.py
# ML API runs on http://localhost:8000
```

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete API endpoint documentation
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Guide for frontend developers
- **[Setup Guide](docs/SETUP.md)** - Detailed setup instructions

## 🏗 Architecture

```
┌─────────────────┐
│  Frontend App   │  (Apple TV, Web, Mobile)
│                 │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  Backend API    │  (Flask - Port 5555)
│  - Movies       │
│  - Auth         │
│  - Trending     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ML API        │  (Flask - Port 8000)
│  - EASE         │
│  - ItemKNN      │
│  - NeuralMF     │
│  - DeepFM       │
└─────────────────┘
```

## 🔑 API Base URLs

### Local Development
- **Backend API**: `http://localhost:5555`
- **ML API**: `http://localhost:8000`

### Production
- **Backend API**: Set via `BACKEND_API_URL` environment variable
- **ML API**: Set via `ML_API_URL` environment variable

## ✨ Features

- **Movie Management**: Get, search, and browse 1,682 movies
- **Recommendations**: 4 ML models (EASE, ItemKNN, NeuralMF, DeepFM)
- **User Authentication**: JWT-based auth with secure password hashing
- **Trending Movies**: Real-time trending content
- **Database Support**: MongoDB Atlas (production) or SQLite (local)

## 📊 Dataset

This project uses the **MovieLens 100K** dataset:
- **943 users**
- **1,682 movies**
- **100,000 ratings**

## 🔧 Environment Variables

See `.env.example` for all required environment variables.

**Required:**
- `SECRET_KEY` - Flask secret key for JWT tokens
- `MONGODB_URI` - MongoDB connection string (optional for local SQLite)

**Optional:**
- `TMDB_API_KEY` - For enhanced movie details
- `ML_API_URL` - ML API service URL (defaults to localhost:8000)
- `FLASK_ENV` - Environment (development/production)

## 🚢 Deployment

### Backend Deployment
- **Platform**: Render, Heroku, AWS, etc.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT`

### ML API Deployment
- **Platform**: Render, Heroku, AWS, etc.
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn api:app --bind 0.0.0.0:$PORT`

See [docs/SETUP.md](docs/SETUP.md) for detailed deployment instructions.

## 📝 API Endpoints

### Movies
- `GET /api/movies` - Get all movies (paginated)
- `GET /api/movies/search?q=query` - Search movies
- `GET /api/movies/<id>` - Get movie by ID
- `GET /api/movies/<id>/details` - Get enhanced movie details
- `GET /api/trending` - Get trending movies

### Recommendations
- `POST /recommend` - Get movie recommendations

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/user` - Get current user (protected)

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete documentation.

## 🤝 For Frontend Developers

If you're building the frontend (Apple TV app, web app, etc.), check out:
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Step-by-step integration guide
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation with examples

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**David Omokagbor**
- GitHub: [@DavidOmokagbor1](https://github.com/DavidOmokagbor1)

---

**Note**: This is a backend-only repository. The frontend code is maintained separately by the frontend team.
