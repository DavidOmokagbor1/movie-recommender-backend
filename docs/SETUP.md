# Setup Guide

Detailed setup instructions for the Movie Recommender Backend.

## Prerequisites

- **Python 3.9+** (Python 3.11 recommended)
- **pip** (Python package manager)
- **MongoDB Atlas account** (for production) or **SQLite** (for local development)
- **Git** (for version control)

## Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd movie-recommender-backend
```

## Step 2: Backend Setup

### 2.1 Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp ../.env.example backend/.env
# Edit backend/.env with your values
```

**Required Variables:**
- `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
- `MONGODB_URI` - Your MongoDB Atlas connection string (optional for local SQLite)

**Optional Variables:**
- `ML_API_URL` - ML API URL (defaults to `http://localhost:8000`)
- `TMDB_API_KEY` - For enhanced movie details
- `FLASK_ENV` - Set to `development` or `production`

### 2.4 Initialize Database (Optional)

If using SQLite (default for local development):

```bash
python initialize_ml100k_db.py
```

This will populate the database with 1,682 movies from the MovieLens 100K dataset.

## Step 3: ML API Setup

### 3.1 Create Virtual Environment

```bash
cd ../api
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3.2 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** For neural models (NeuralMF, DeepFM), you'll need PyTorch. See `requirements-with-torch.txt` for PyTorch dependencies.

### 3.3 Train Models (Optional)

Pre-trained models are included, but you can retrain:

```bash
# Train EASE model
python fit_offline.py --model EASE --save_dir recommend/ckpt

# Train ItemKNN model
python fit_offline.py --model ItemKNN --save_dir recommend/ckpt
```

**Note:** Training neural models (NeuralMF, DeepFM) requires PyTorch and takes longer.

## Step 4: Run Services

### 4.1 Start Backend API

**Terminal 1:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python run.py
```

Backend will run on `http://localhost:5555`

### 4.2 Start ML API

**Terminal 2:**
```bash
cd api
source venv/bin/activate  # On Windows: venv\Scripts\activate
python api.py
```

ML API will run on `http://localhost:8000`

### 4.3 Verify Services

**Test Backend:**
```bash
curl http://localhost:5555/health
```

**Test ML API:**
```bash
curl http://localhost:8000/api/health
```

**Test Recommendations:**
```bash
curl -X POST http://localhost:5555/recommend \
  -H "Content-Type: application/json" \
  -d '{"model": "EASE", "context": [1, 2, 3]}'
```

## MongoDB Setup (Production)

### Option 1: MongoDB Atlas (Cloud)

1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Create a database user
4. Whitelist your IP address (or use `0.0.0.0/0` for all IPs)
5. Get connection string
6. Set `MONGODB_URI` in `.env`:

```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=MovieRecommender
```

### Option 2: Local MongoDB

1. Install MongoDB locally
2. Start MongoDB service
3. Set `MONGODB_URI` in `.env`:

```
MONGODB_URI=mongodb://localhost:27017/movierecommender
```

## Environment Variables Reference

### Backend (.env)

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=movierecommender
DATABASE_URL=sqlite:///app.db  # Fallback

# ML API
ML_API_URL=http://localhost:8000

# Optional APIs
TMDB_API_KEY=your-tmdb-key
OMDB_API_KEY=your-omdb-key
```

## Troubleshooting

### Port Already in Use

If port 5555 or 8000 is already in use:

```bash
# Find process using port
lsof -i :5555  # macOS/Linux
netstat -ano | findstr :5555  # Windows

# Kill process or change port in run.py/api.py
```

### MongoDB Connection Issues

1. Check MongoDB URI is correct
2. Verify IP is whitelisted (for Atlas)
3. Check database user credentials
4. Backend will fallback to SQLite if MongoDB unavailable

### ML API Not Responding

1. Ensure ML API is running on port 8000
2. Check `ML_API_URL` in backend `.env`
3. Verify models are trained (check `api/recommend/ckpt/` directory)

### Import Errors

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Database Migration Issues

```bash
cd backend
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Production Deployment

### Render.com

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn run:app --bind 0.0.0.0:$PORT`
5. Add environment variables
6. Deploy

### Heroku

1. Install Heroku CLI
2. Create `Procfile`: `web: gunicorn run:app --bind 0.0.0.0:$PORT`
3. Deploy: `git push heroku main`

### AWS/Docker

See deployment-specific documentation for containerized deployments.

## Next Steps

- Read [API Reference](API_REFERENCE.md) for endpoint documentation
- Check [Frontend Integration Guide](FRONTEND_INTEGRATION.md) for frontend setup
- Test API endpoints with curl or Postman
- Set up CI/CD pipeline (optional)

## Support

For issues or questions:
1. Check error logs in `backend.log` or `ml_api.log`
2. Review environment variables
3. Test endpoints individually
4. Check database connectivity

---

Happy coding! 🚀
