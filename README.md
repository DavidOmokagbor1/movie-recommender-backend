# Apple TV Prototype - Backend API

A production-ready backend API for the Apple TV Prototype project. This backend provides RESTful endpoints for movie data, user authentication, and personalized recommendations using multiple machine learning models.

## 🎯 Project Overview

This backend powers the Apple TV Prototype application, providing:
- **Movie Data**: Access to 1,682 movies from the MovieLens 100K dataset
- **Recommendations**: 4 ML models (EASE, ItemKNN, NeuralMF, DeepFM) for personalized movie recommendations
- **User Management**: JWT-based authentication and user profiles
- **Trending Content**: Real-time trending movies

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ (Python 3.11 recommended)
- MongoDB Atlas account (for production) or SQLite (for local development)
- pip and virtualenv

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/DavidOmokagbor1/apple-tv-prototype-backend.git
cd apple-tv-prototype-backend
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
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
# Backend runs on http://localhost:5555
```

**Terminal 2 - ML API:**
```bash
cd api
source venv/bin/activate  # On Windows: venv\Scripts\activate
python api.py
# ML API runs on http://localhost:8000
```

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete API endpoint documentation with examples
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Step-by-step guide for frontend developers
- **[Setup Guide](docs/SETUP.md)** - Detailed setup and deployment instructions

## 🏗 Architecture

```
┌─────────────────┐
│  Apple TV App  │  (Frontend)
│   (Frontend)    │
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
│  - NeuralMF      │
│  - DeepFM       │
└─────────────────┘
```

### Component Responsibilities

- **Backend API (Flask)**: Business logic, authentication, database operations, API orchestration
- **ML API (Flask)**: Model loading, recommendation generation, model inference
- **Database (MongoDB/SQLite)**: User data, movie data, interaction history

## 🔑 API Base URLs

### Local Development
- **Backend API**: `http://localhost:5555`
- **ML API**: `http://localhost:8000`

### Production
- **Backend API**: Set via deployment platform environment variables
- **ML API**: Set via deployment platform environment variables

## ✨ Features

### 🎬 Movie Management
- Get all movies with pagination
- Search movies by title or genre
- Get movie details with enhanced information
- Trending movies endpoint

### 🤖 Machine Learning Recommendations
- **4 Recommendation Algorithms**:
  - **EASE** (Embarrassingly Shallow Autoencoders) - Fast, efficient collaborative filtering
  - **ItemKNN** - Item-based collaborative filtering
  - **NeuralMF** - Neural Matrix Factorization with PyTorch
  - **DeepFM** - Deep Factorization Machine for complex feature interactions
- Real-time recommendation generation
- Model evaluation metrics (Precision@K, Recall@K, NDCG@K)

### 🔐 User Authentication & Management
- JWT-based authentication with secure token management
- User registration and login with password hashing (Flask-Bcrypt)
- Protected API routes with role-based access
- User profile management

### 📊 User Interaction Tracking
- Track user movie views, ratings, and interactions
- Batch interaction logging for performance
- Personalized recommendations based on user history

## 📊 Dataset

This project uses the **MovieLens 100K** dataset:
- **943 users**
- **1,682 movies**
- **100,000 ratings**
- Pre-loaded in the database for immediate use

## 🔧 Environment Variables

See `.env.example` for all required environment variables.

**Required:**
- `SECRET_KEY` - Flask secret key for JWT tokens (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `MONGODB_URI` - MongoDB connection string (optional for local SQLite)

**Optional:**
- `TMDB_API_KEY` - For enhanced movie details
- `ML_API_URL` - ML API service URL (defaults to localhost:8000)
- `FLASK_ENV` - Environment (development/production)

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

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete documentation with examples.

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

## 🤝 For Frontend Developers

If you're building the Apple TV frontend, check out:
- **[Frontend Integration Guide](docs/FRONTEND_INTEGRATION.md)** - Step-by-step integration guide with code examples
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation with request/response examples

## 🛠 Tech Stack

### Backend
- **Flask 2.3.3** - Python web framework
- **Flask-SQLAlchemy** - ORM for database operations
- **Flask-Bcrypt** - Password hashing
- **Flask-CORS** - Cross-origin resource sharing
- **PyJWT** - JSON Web Token authentication
- **Gunicorn** - Production WSGI server

### Machine Learning
- **PyTorch** - Deep learning framework for NeuralMF and DeepFM
- **NumPy** - Numerical computing
- **Scikit-learn** - Machine learning utilities
- **Pandas** - Data manipulation

### Database & Storage
- **MongoDB Atlas** - Cloud NoSQL database (production)
- **SQLite** - Local development database

## 📁 Project Structure

```
apple-tv-prototype-backend/
├── backend/          # Main Flask backend application
│   ├── app/          # Application modules
│   ├── run.py        # Application entry point
│   └── requirements.txt
├── api/              # ML API service
│   ├── recommend/    # Recommendation models
│   ├── api.py        # API server
│   └── requirements.txt
└── docs/             # Documentation
    ├── API_REFERENCE.md
    ├── FRONTEND_INTEGRATION.md
    └── SETUP.md
```

## 🔗 Related Repositories

- **Frontend**: [apple-tv-prototype-frontend](https://github.com/DavidOmokagbor1/apple-tv-prototype-frontend) - Apple TV application frontend

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**David Omokagbor**
- GitHub: [@DavidOmokagbor1](https://github.com/DavidOmokagbor1)

---

**Note**: This is a backend-only repository. The frontend code is maintained separately in the [apple-tv-prototype-frontend](https://github.com/DavidOmokagbor1/apple-tv-prototype-frontend) repository.
