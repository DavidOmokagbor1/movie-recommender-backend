import json
import logging
import os
from datetime import datetime
from flask.json import jsonify
from flask import request
import requests

from flask import render_template

from app import app, db, migrate, flask_bcrypt
from app.model import User, Movie, Interaction
from db_helper import get_all_movies, get_movies_by_ids, get_movie_by_id, use_mongodb, save_interaction
from tmdb_helper import get_enhanced_movie_details
import jwt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get ML API URL from environment variable, with fallback for local development
ML_API_BASE = os.getenv('ML_API_URL', 'http://localhost:8000')
# Ensure the URL format is correct for string formatting
if ML_API_BASE.endswith('%s'):
    API_ADDRESS = ML_API_BASE
else:
    API_ADDRESS = f"{ML_API_BASE}%s"

@app.route('/', methods=['GET'])
def index():
	"""Root endpoint - API info and health"""
	return jsonify({
		'service': 'Movie Recommender API',
		'status': 'running',
		'endpoints': {
			'health': '/health',
			'movies': '/api/movies',
			'recommend': '/recommend (POST)',
			'trending': '/api/trending',
		},
		'timestamp': datetime.utcnow().isoformat()
	}), 200

@app.route('/recommend', methods=['POST', 'OPTIONS'])
def recommend():
	"""Get movie recommendations"""
	# Handle OPTIONS preflight request
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		data = request.get_json()
		
		if not data:
			return jsonify({'message': 'No data provided', 'error': 'MISSING_DATA'}), 400
		
		if 'context' not in data or not data['context']:
			return jsonify({'message': 'Context (movie IDs) is required', 'error': 'MISSING_CONTEXT'}), 400
		
		if not isinstance(data['context'], list) or len(data['context']) == 0:
			return jsonify({'message': 'Context must be a non-empty array of movie IDs', 'error': 'INVALID_CONTEXT'}), 400
		
		# Validate context contains only integers
		try:
			context_ids = [int(id) for id in data['context']]
			if len(context_ids) == 0:
				return jsonify({'message': 'Context must contain at least one valid movie ID', 'error': 'EMPTY_CONTEXT'}), 400
		except (ValueError, TypeError):
			return jsonify({'message': 'Context must contain only numeric movie IDs', 'error': 'INVALID_CONTEXT_FORMAT'}), 400
		
		if 'model' not in data:
			return jsonify({'message': 'Model name is required', 'error': 'MISSING_MODEL'}), 400
		
		# Validate model name
		valid_models = ['EASE', 'ItemKNN', 'NeuralMF', 'DeepFM']
		if data['model'] not in valid_models:
			return jsonify({
				'message': f'Invalid model. Must be one of: {", ".join(valid_models)}',
				'error': 'INVALID_MODEL',
				'available_models': valid_models
			}), 400
		
		# Call recommendation API
		# Render free tier services sleep after inactivity, so we need longer timeout and retry
		ml_api_url = API_ADDRESS % '/api/recommend'
		max_retries = 2
		timeout = 60  # Increased timeout for sleeping services
		
		for attempt in range(max_retries):
			try:
				response = requests.post(
					ml_api_url, 
					json=data,
					timeout=timeout
				)
				response.raise_for_status()
				res = response.json()
				break  # Success, exit retry loop
			except requests.exceptions.Timeout as e:
				if attempt < max_retries - 1:
					logger.warning(f"ML API timeout (attempt {attempt + 1}/{max_retries}), retrying...")
					import time
					time.sleep(2)  # Brief wait before retry
					continue
				else:
					logger.error(f"ML API request timed out after {max_retries} attempts: {str(e)}")
					return jsonify({
						'message': 'Recommendation service is taking too long to respond. The service may be starting up. Please try again in a moment.',
						'error': 'API_TIMEOUT'
					}), 504
			except requests.exceptions.ConnectionError as e:
				if attempt < max_retries - 1:
					logger.warning(f"ML API connection error (attempt {attempt + 1}/{max_retries}), retrying...")
					import time
					time.sleep(3)  # Longer wait for connection errors
					continue
				else:
					logger.error(f"ML API connection failed after {max_retries} attempts: {str(e)}")
					return jsonify({
						'message': 'Cannot connect to recommendation service. The service may be starting up. Please try again.',
						'error': 'API_CONNECTION_ERROR'
					}), 503
			except requests.exceptions.RequestException as e:
				logger.error(f"ML API request failed: {str(e)}")
				return jsonify({
					'message': 'Recommendation service unavailable',
					'error': 'API_ERROR',
					'details': str(e)
				}), 503
		
		if 'result' not in res:
			logger.error(f"ML API response missing 'result' field: {res}")
			return jsonify({'message': 'Invalid response from recommendation API', 'error': 'INVALID_RESPONSE'}), 500
		
		if not res['result'] or len(res['result']) == 0:
			logger.warning(f"ML API returned empty recommendations for context: {data.get('context')}")
			return jsonify({
				'message': 'No recommendations found for the selected movies',
				'error': 'NO_RECOMMENDATIONS',
				'result': []
			}), 200
		
		# Get movie details from database using unified helper
		logger.info(f"Looking up {len(res['result'])} recommended movie IDs: {res['result'][:10]}")
		recommend_items = get_movies_by_ids(res['result'])
		logger.info(f"Found {len(recommend_items)} movies in database for recommended IDs")
		
		if not recommend_items or len(recommend_items) == 0:
			logger.error(f"Could not find any movies in database for recommended IDs: {res['result']}")
			return jsonify({
				'message': 'Recommended movies not found in database',
				'error': 'MOVIES_NOT_FOUND',
				'result': []
			}), 200
		
		# Save recommendation interaction if user is authenticated
		user_id = None
		try:
			auth_header = request.headers.get('Authorization', '')
			if auth_header.startswith('Bearer '):
				# Extract user from token without requiring decorator
				import jwt
				token = auth_header.split(' ')[1]
				token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
				user_id = token_data.get('user_id')
				
				# Save interactions for recommended movies
				if user_id:
					for movie_id in res['result']:
						save_interaction(user_id, movie_id, 'recommend')
		except Exception as e:
			logger.warning(f"Failed to save recommendation interactions: {str(e)}")
			# Don't fail the request if interaction saving fails
		
		return jsonify({'result': recommend_items}), 200
		
	except Exception as e:
		logger.error(f"Recommendation error: {str(e)}")
		return jsonify({
			'message': 'Failed to get recommendations',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/trending', methods=['GET', 'OPTIONS'])
def get_trending():
	"""Get trending movies - either from TMDB API or sorted by date"""
	# Handle OPTIONS preflight request
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		# Try to get trending from TMDB if API key is available
		tmdb_api_key = os.getenv('TMDB_API_KEY')
		if tmdb_api_key:
			try:
				trending_url = 'https://api.themoviedb.org/3/trending/movie/week'
				params = {
					'api_key': tmdb_api_key,
					'language': 'en-US'
				}
				response = requests.get(trending_url, params=params, timeout=10)
				if response.status_code == 200:
					data = response.json()
					trending_tmdb = data.get('results', [])[:10]
					
					# Map TMDB movies to our format
					trending_movies = []
					for tmdb_movie in trending_tmdb:
						# Try to find matching movie in our database by title
						all_movies = get_all_movies()
						matching = next((m for m in all_movies if m.get('title', '').lower() == tmdb_movie.get('title', '').lower()), None)
						
						if matching:
							# Use our database movie but update poster if TMDB has better one
							if tmdb_movie.get('poster_path'):
								matching['poster'] = f"https://image.tmdb.org/t/p/w500{tmdb_movie.get('poster_path')}"
							trending_movies.append(matching)
						else:
							# Create movie entry from TMDB data
							# Handle genre_ids - they're integers, not objects
							genre_ids = tmdb_movie.get('genre_ids', [])
							genre_str = 'Action'  # Default, since we can't map IDs without genre lookup
							
							trending_movies.append({
								'id': f"tmdb_{tmdb_movie.get('id')}",
								'title': tmdb_movie.get('title'),
								'genre': genre_str,
								'date': tmdb_movie.get('release_date', ''),
								'poster': f"https://image.tmdb.org/t/p/w500{tmdb_movie.get('poster_path')}" if tmdb_movie.get('poster_path') else None
							})
					
					if trending_movies:
						return jsonify({'result': trending_movies}), 200
			except Exception as e:
				logger.warning(f"TMDB trending API error: {e}, falling back to date-based sorting")
		
		# Fallback: Get movies sorted by date (most recent)
		all_items = get_all_movies()
		# Filter movies with valid posters
		movies_with_posters = [
			m for m in all_items 
			if m and m.get('poster') and 
			m.get('poster') != 'null' and 
			m.get('poster') != 'None' and
			'via.placeholder.com' not in str(m.get('poster', ''))
		]
		
		# Sort by date (most recent first), handle missing dates
		def get_date_sort_key(movie):
			date_str = movie.get('date', '') or ''
			if not date_str:
				return '0000-01-01'  # Put movies without dates at the end
			# Try to parse date, return as-is if it's already a string
			try:
				# If it's already YYYY-MM-DD format, use it directly
				if len(date_str) >= 10 and date_str[4] == '-':
					return date_str[:10]
				# Try to parse other formats
				from datetime import datetime
				parsed = datetime.strptime(date_str[:10], '%Y-%m-%d')
				return parsed.strftime('%Y-%m-%d')
			except:
				return date_str[:10] if len(date_str) >= 10 else '0000-01-01'
		
		trending = sorted(
			movies_with_posters,
			key=get_date_sort_key,
			reverse=True
		)[:10]
		
		logger.info(f"Returning {len(trending)} trending movies (date-based)")
		return jsonify({'result': trending}), 200
		
	except Exception as e:
		logger.error(f"Trending error: {str(e)}")
		return jsonify({
			'message': 'Failed to get trending movies',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/init', methods=['GET', 'OPTIONS'])
def init():
	"""Initialize and return all movies"""
	# Handle OPTIONS preflight request
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		# Use unified database helper (works with both SQLite and MongoDB)
		all_items = get_all_movies()
		
		# Validate we got movies
		if not all_items:
			logger.warning("No movies found in database")
			return jsonify({
				'result': [],
				'message': 'No movies found in database',
				'count': 0
			}), 200
		
		all_items = sorted(all_items, key=lambda x: x.get("id", 0))
		
		return jsonify({'result': all_items}), 200
		
	except Exception as e:
		logger.error(f"Init error: {str(e)}")
		return jsonify({
			'message': 'Failed to load movies',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/movies', methods=['GET', 'OPTIONS'])
def get_movies():
	"""Get all movies with optional pagination"""
	try:
		
		# Get pagination parameters
		page = request.args.get('page', 1, type=int)
		per_page = request.args.get('per_page', 50, type=int)
		per_page = min(per_page, 100)  # Limit to 100 per page
		
		# Get all movies
		all_movies = get_all_movies()
		all_movies = sorted(all_movies, key=lambda x: x["id"])
		
		# Calculate pagination
		total = len(all_movies)
		start = (page - 1) * per_page
		end = start + per_page
		movies_page = all_movies[start:end]
		
		return jsonify({
			'result': movies_page,
			'pagination': {
				'page': page,
				'per_page': per_page,
				'total': total,
				'pages': (total + per_page - 1) // per_page
			}
		}), 200
		
	except Exception as e:
		logger.error(f"Get movies error: {str(e)}")
		return jsonify({
			'message': 'Failed to get movies',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/movies/<movie_id>', methods=['GET', 'OPTIONS'])
def get_movie(movie_id):
	"""Get a specific movie by ID"""
	# Handle OPTIONS preflight request
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		# Validate movie_id
		if not movie_id:
			return jsonify({
				'message': 'Movie ID is required',
				'error': 'MISSING_ID'
			}), 400
		
		# Try to convert to int if it's a numeric string
		try:
			movie_id_int = int(movie_id)
			if movie_id_int < 0:
				return jsonify({
					'message': 'Movie ID must be a positive number',
					'error': 'INVALID_ID'
				}), 400
			movie = get_movie_by_id(movie_id_int)
		except ValueError:
			# If movie_id is not numeric, return not found
			return jsonify({
				'message': f'Invalid movie ID format: {movie_id}',
				'error': 'INVALID_ID_FORMAT'
			}), 400
		
		if movie:
			return jsonify({'result': movie}), 200
		else:
			return jsonify({
				'message': f'Movie with ID {movie_id} not found',
				'error': 'NOT_FOUND'
			}), 404
		
	except Exception as e:
		logger.error(f"Get movie error: {str(e)}")
		return jsonify({
			'message': 'Failed to get movie',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/movies/<movie_id>/details', methods=['GET', 'OPTIONS'])
def get_movie_details(movie_id):
	"""Get enhanced movie details with cast, crew, and additional info from TMDB"""
	# Handle OPTIONS preflight request
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		# Validate movie_id
		if not movie_id:
			return jsonify({
				'message': 'Movie ID is required',
				'error': 'MISSING_ID'
			}), 400
		
		# Try to convert to int if it's a numeric string, otherwise use as-is
		movie = None
		try:
			movie_id_int = int(movie_id)
			if movie_id_int < 0:
				return jsonify({
					'message': 'Movie ID must be a positive number',
					'error': 'INVALID_ID'
				}), 400
			movie = get_movie_by_id(movie_id_int)
		except ValueError:
			# If movie_id is not numeric (e.g., "tmdb_1242898"), try to extract numeric part
			import re
			match = re.search(r'(\d+)', str(movie_id))
			if match:
				movie_id_int = int(match.group(1))
				movie = get_movie_by_id(movie_id_int)
				logger.info(f"Extracted numeric ID {movie_id_int} from {movie_id}")
			else:
				logger.warning(f"Non-numeric movie_id received and no numeric part found: {movie_id}")
				return jsonify({
					'message': f'Invalid movie ID format: {movie_id}',
					'error': 'INVALID_ID_FORMAT'
				}), 400
		
		if not movie:
			return jsonify({
				'message': f'Movie with ID {movie_id} not found',
				'error': 'NOT_FOUND'
			}), 404
		
		# Try to get enhanced details from TMDB
		enhanced_details = None
		try:
			enhanced_details = get_enhanced_movie_details(movie.get('title'), movie.get('date'))
		except Exception as e:
			logger.warning(f"Failed to fetch TMDB details: {e}")
		
		# Merge basic movie info with enhanced details
		result = {
			**movie,  # Basic info (id, title, genre, date, poster)
			'enhanced': enhanced_details  # Enhanced details from TMDB
		}
		
		return jsonify({'result': result}), 200
		
	except Exception as e:
		logger.error(f"Get movie details error: {str(e)}")
		return jsonify({
			'message': 'Failed to get movie details',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/movies/search', methods=['GET', 'OPTIONS'])
def search_movies():
	"""Search movies by title or genre"""
	try:
		
		query = request.args.get('q', '').strip().lower()
		genre_filter = request.args.get('genre', '').strip()
		
		if not query and not genre_filter:
			return jsonify({
				'message': 'Search query (q) or genre filter required',
				'error': 'MISSING_PARAMETER'
			}), 400
		
		# Get all movies
		all_movies = get_all_movies()
		
		# Filter movies
		filtered_movies = []
		for movie in all_movies:
			title = movie.get('title', '').lower()
			genre = movie.get('genre', '').lower()
			
			# Check title match
			title_match = query in title if query else True
			
			# Check genre match
			genre_match = genre_filter.lower() in genre if genre_filter else True
			
			if title_match and genre_match:
				filtered_movies.append(movie)
		
		return jsonify({
			'result': filtered_movies,
			'count': len(filtered_movies),
			'query': query,
			'genre': genre_filter
		}), 200
		
	except Exception as e:
		logger.error(f"Search movies error: {str(e)}")
		return jsonify({
			'message': 'Failed to search movies',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/health', methods=['GET'])
def health():
	"""Health check endpoint"""
	try:
		# Check database connectivity
		is_mongo = use_mongodb()
		if is_mongo:
			from mongodb_client import mongodb_client
			mongodb = mongodb_client.get_database()
			if mongodb is not None:
				# Test MongoDB connection
				mongodb.client.admin.command('ping')
				db_status = 'connected'
			else:
				db_status = 'disconnected'
		else:
			# SQLite - just check if db exists
			try:
				db.session.execute(db.text('SELECT 1'))
				db_status = 'connected'
			except:
				db_status = 'disconnected'
		
		return jsonify({
			'status': 'healthy',
			'database': 'MongoDB' if is_mongo else 'SQLite',
			'db_status': db_status,
			'timestamp': datetime.utcnow().isoformat()
		}), 200
	except Exception as e:
		logger.error(f"Health check error: {str(e)}")
		return jsonify({
			'status': 'unhealthy',
			'error': str(e),
			'timestamp': datetime.utcnow().isoformat()
		}), 503

@app.route('/api/stats', methods=['GET'])
def get_stats():
	"""Get database statistics"""
	try:
		from app import mongodb
		from app.model import Movie, User, Interaction
		
		stats = {}
		
		# Check which database is being used
		is_mongo = use_mongodb()
		stats['database'] = 'MongoDB' if is_mongo else 'SQLite'
		
		if is_mongo and mongodb is not None:
			# MongoDB stats
			try:
				movies_count = mongodb['movies'].count_documents({})
				users_count = mongodb['users'].count_documents({})
				interactions_count = mongodb['interactions'].count_documents({})
				
				# Get genre distribution
				movies_collection = mongodb['movies']
				genres = {}
				for movie in movies_collection.find({}, {'genre': 1}):
					genre_str = movie.get('genre', '')
					if genre_str:
						for genre in genre_str.split(','):
							genre = genre.strip()
							if genre:
								genres[genre] = genres.get(genre, 0) + 1
				
				stats['movies'] = movies_count
				stats['users'] = users_count
				stats['interactions'] = interactions_count
				stats['genres'] = genres
			except Exception as e:
				logger.error(f"MongoDB stats error: {e}")
				raise
		else:
			# SQLite stats
			movies_count = Movie.query.count()
			users_count = User.query.count()
			interactions_count = Interaction.query.count()
			
			# Get genre distribution
			genres = {}
			for movie in Movie.query.all():
				if movie.genre:
					for genre in movie.genre.split(','):
						genre = genre.strip()
						if genre:
							genres[genre] = genres.get(genre, 0) + 1
			
			stats['movies'] = movies_count
			stats['users'] = users_count
			stats['interactions'] = interactions_count
			stats['genres'] = genres
		
		return jsonify({
			'result': stats,
			'timestamp': datetime.utcnow().isoformat()
		}), 200
		
	except Exception as e:
		logger.error(f"Get stats error: {str(e)}")
		return jsonify({
			'message': 'Failed to get statistics',
			'error': 'INTERNAL_ERROR',
			'details': str(e)
		}), 500

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
	"""Register a new user"""
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		data = request.get_json()
		
		if not data:
			return jsonify({'message': 'No data provided', 'error': 'MISSING_DATA'}), 400
		
		if 'username' not in data or not data['username']:
			return jsonify({'message': 'Username is required', 'error': 'MISSING_USERNAME'}), 400
		
		if 'password' not in data or not data['password']:
			return jsonify({'message': 'Password is required', 'error': 'MISSING_PASSWORD'}), 400
		
		if 'email' not in data or not data['email']:
			return jsonify({'message': 'Email is required', 'error': 'MISSING_EMAIL'}), 400
		
		username = data['username'].strip()
		password = data['password']
		email = data['email'].strip()
		age = data.get('age', -1)
		gender = data.get('gender', '-')
		
		is_mongo = use_mongodb()
		
		if is_mongo:
			from mongodb_client import mongodb_client
			mongodb = mongodb_client.get_database()
			if mongodb is not None:
				users_collection = mongodb['users']
				existing_user = users_collection.find_one({'$or': [{'username': username}, {'email': email}]})
				if existing_user:
					return jsonify({
						'message': 'Username or email already exists',
						'error': 'USER_EXISTS'
					}), 400
				
				user_doc = {
					'username': username,
					'email': email,
					'password_hash': flask_bcrypt.generate_password_hash(password).decode('utf-8'),
					'age': age if age > 0 else -1,
					'gender': gender if gender else '-',
					'created_at': datetime.utcnow(),
					'is_active': True
				}
				result = users_collection.insert_one(user_doc)
				user_id = result.inserted_id
		else:
			existing_user = User.query.filter(
				(User.username == username) | (User.email == email)
			).first()
			if existing_user:
				return jsonify({
					'message': 'Username or email already exists',
					'error': 'USER_EXISTS'
				}), 400
			
			user = User(
				username=username,
				email=email,
				age=age if age > 0 else -1,
				gender=gender if gender else '-'
			)
			user.set_password(password)
			db.session.add(user)
			db.session.commit()
			user_id = user.id
		
		token = jwt.encode(
			{'user_id': str(user_id), 'username': username},
			app.config['SECRET_KEY'],
			algorithm='HS256'
		)
		
		return jsonify({
			'message': 'User registered successfully',
			'token': token,
			'user': {
				'id': str(user_id),
				'username': username,
				'email': email,
				'age': age,
				'gender': gender
			}
		}), 201
		
	except Exception as e:
		logger.error(f"Registration error: {str(e)}")
		if db.session:
			db.session.rollback()
		return jsonify({
			'message': 'Failed to register user',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
	"""Login user and return JWT token"""
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		data = request.get_json()
		
		if not data:
			return jsonify({'message': 'No data provided', 'error': 'MISSING_DATA'}), 400
		
		if 'username' not in data or not data['username']:
			return jsonify({'message': 'Username is required', 'error': 'MISSING_USERNAME'}), 400
		
		if 'password' not in data or not data['password']:
			return jsonify({'message': 'Password is required', 'error': 'MISSING_PASSWORD'}), 400
		
		username = data['username'].strip()
		password = data['password']
		
		is_mongo = use_mongodb()
		user = None
		user_id = None
		
		if is_mongo:
			from mongodb_client import mongodb_client
			mongodb = mongodb_client.get_database()
			if mongodb is not None:
				users_collection = mongodb['users']
				user_doc = users_collection.find_one({'username': username})
				if user_doc and flask_bcrypt.check_password_hash(user_doc.get('password_hash', ''), password):
					user_id = str(user_doc['_id'])
					user = {
						'id': user_id,
						'username': user_doc.get('username'),
						'email': user_doc.get('email'),
						'age': user_doc.get('age', -1),
						'gender': user_doc.get('gender', '-')
					}
		else:
			user_obj = User.query.filter_by(username=username).first()
			if user_obj and user_obj.check_password(password):
				user_id = user_obj.id
				user = user_obj.to_dict()
		
		if not user:
			return jsonify({
				'message': 'Invalid username or password',
				'error': 'INVALID_CREDENTIALS'
			}), 401
		
		token = jwt.encode(
			{'user_id': str(user_id), 'username': username},
			app.config['SECRET_KEY'],
			algorithm='HS256'
		)
		
		return jsonify({
			'message': 'Login successful',
			'token': token,
			'user': user
		}), 200
		
	except Exception as e:
		logger.error(f"Login error: {str(e)}")
		return jsonify({
			'message': 'Failed to login',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.route('/api/auth/user', methods=['GET', 'OPTIONS'])
def get_current_user():
	"""Get current authenticated user"""
	if request.method == 'OPTIONS':
		return '', 200
	
	try:
		auth_header = request.headers.get('Authorization', '')
		if not auth_header.startswith('Bearer '):
			return jsonify({
				'message': 'Authorization token required',
				'error': 'MISSING_TOKEN'
			}), 401
		
		token = auth_header.split(' ')[1]
		token_data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
		user_id = token_data.get('user_id')
		
		if not user_id:
			return jsonify({
				'message': 'Invalid token',
				'error': 'INVALID_TOKEN'
			}), 401
		
		is_mongo = use_mongodb()
		user = None
		
		if is_mongo:
			from mongodb_client import mongodb_client
			mongodb = mongodb_client.get_database()
			if mongodb is not None:
				users_collection = mongodb['users']
				try:
					from bson.objectid import ObjectId
					user_doc = users_collection.find_one({'_id': ObjectId(user_id)})
				except:
					try:
						user_id_int = int(user_id) if user_id.isdigit() else user_id
						user_doc = users_collection.find_one({'_id': user_id_int})
					except:
						user_doc = users_collection.find_one({'_id': user_id})
				if user_doc:
					user = {
						'id': str(user_doc['_id']),
						'username': user_doc.get('username'),
						'email': user_doc.get('email'),
						'age': user_doc.get('age', -1),
						'gender': user_doc.get('gender', '-')
					}
		else:
			user_obj = User.query.get(int(user_id))
			if user_obj:
				user = user_obj.to_dict()
		
		if not user:
			return jsonify({
				'message': 'User not found',
				'error': 'USER_NOT_FOUND'
			}), 404
		
		return jsonify({
			'user': user
		}), 200
		
	except jwt.ExpiredSignatureError:
		return jsonify({
			'message': 'Token has expired',
			'error': 'TOKEN_EXPIRED'
		}), 401
	except jwt.InvalidTokenError:
		return jsonify({
			'message': 'Invalid token',
			'error': 'INVALID_TOKEN'
		}), 401
	except Exception as e:
		logger.error(f"Get user error: {str(e)}")
		return jsonify({
			'message': 'Failed to get user',
			'error': 'INTERNAL_ERROR'
		}), 500

@app.errorhandler(404)
def not_found(error):
	return jsonify({'message': 'Endpoint not found', 'error': 'NOT_FOUND'}), 404

@app.errorhandler(500)
def internal_error(error):
	# Only rollback if using SQLite (db.session exists and is active)
	try:
		if db.session and hasattr(db.session, 'rollback'):
			db.session.rollback()
	except Exception:
		# Ignore rollback errors (e.g., if using MongoDB)
		pass
	return jsonify({'message': 'Internal server error', 'error': 'INTERNAL_ERROR'}), 500

if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=5555, debug=debug_mode)