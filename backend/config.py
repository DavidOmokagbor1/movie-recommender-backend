import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
	# SECRET_KEY must be set via environment variable for security
	# Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"
	# For localhost development, use a default key
	SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
	if not SECRET_KEY or SECRET_KEY == 'dev-secret-key-change-in-production':
		# Only warn in production, allow default for localhost
		if os.getenv('FLASK_ENV') == 'production':
			raise ValueError(
				"SECRET_KEY environment variable is required in production. "
				"Set it with: export SECRET_KEY='your-secret-key-here' "
				"Or generate one: python -c \"import secrets; print(secrets.token_hex(32))\""
			)
	
	# MongoDB Atlas connection string
	# MUST be set via environment variable - never hardcode credentials
	# For localhost, allow SQLite fallback
	_mongodb_uri_raw = os.getenv('MONGODB_URI')
	if not _mongodb_uri_raw:
		# Only require in production, allow SQLite fallback for localhost
		if os.getenv('FLASK_ENV') == 'production':
			raise ValueError(
				"MONGODB_URI environment variable is required in production. "
				"Set it with: export MONGODB_URI='mongodb+srv://username:password@cluster.mongodb.net/?appName=MovieRecommender'"
			)
		MONGODB_URI = None  # Will use SQLite fallback
	else:
		# Clean whitespace from URI
		MONGODB_URI = _mongodb_uri_raw.strip()
	
	MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'movierecommender')
	
	# SQLite (keep for backward compatibility or gradual migration)
	SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'app.db'))
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	DEBUG = False
	
	# Movie Poster API Keys (optional)
	TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
	OMDB_API_KEY = os.getenv('OMDB_API_KEY', '')

key = Config.SECRET_KEY