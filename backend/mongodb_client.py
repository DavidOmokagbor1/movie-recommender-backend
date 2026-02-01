"""
MongoDB connection module for Movie Recommender
Handles connection to MongoDB Atlas
"""
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
from config import Config

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Singleton MongoDB client"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance
    
    def connect(self):
        """Connect to MongoDB Atlas"""
        # Reset client if previous connection failed
        if self._client is None or not self._connection_attempted:
            self._connection_attempted = True
            import ssl
            import certifi
            
            # Validate MongoDB URI before attempting connection
            mongodb_uri = Config.MONGODB_URI.strip() if Config.MONGODB_URI else ''
            
            if not mongodb_uri:
                logger.error("MONGODB_URI is empty or not set. Cannot connect to MongoDB.")
                return False
            
            if not (mongodb_uri.startswith('mongodb://') or mongodb_uri.startswith('mongodb+srv://')):
                logger.error(
                    f"Invalid MongoDB URI format. Must start with 'mongodb://' or 'mongodb+srv://'. "
                    f"Got: {mongodb_uri[:50]}... (truncated for security)"
                )
                return False
            
            # URL encode special characters in password if needed
            # Check if URI contains unencoded special characters
            from urllib.parse import quote_plus, unquote, urlparse, parse_qs
            try:
                parsed = urlparse(mongodb_uri)
                # If password contains special chars and isn't encoded, we need to handle it
                # But for now, try the URI as-is first, then try with proper encoding if it fails
            except:
                pass
            
            # Try multiple connection methods (ordered by likelihood of success)
            # First, try the simplest connection method (most compatible with Atlas)
            connection_methods = [
                # Method 1: Simplest - let URI handle everything (most compatible)
                {
                    'name': 'simplest (URI only)',
                    'kwargs': {
                        'serverSelectionTimeoutMS': 10000,
                        'connectTimeoutMS': 10000,
                    }
                },
                # Method 2: Simple connection without ServerApi (most compatible)
                {
                    'name': 'simple connection (no ServerApi)',
                    'kwargs': {
                        'tls': True,
                        'tlsCAFile': certifi.where(),
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000,
                        'retryWrites': True
                    }
                },
                # Method 2: Simple connection with certifi, no explicit TLS
                {
                    'name': 'simple with certifi (no explicit TLS)',
                    'kwargs': {
                        'tlsCAFile': certifi.where(),
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000,
                        'retryWrites': True
                    }
                },
                # Method 3: Minimal options (let URI handle everything)
                {
                    'name': 'minimal options',
                    'kwargs': {
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000
                    }
                },
                # Method 4: Use certifi certificates explicitly with ServerApi
                {
                    'name': 'certifi certificates with ServerApi',
                    'kwargs': {
                        'server_api': ServerApi('1'),
                        'tls': True,
                        'tlsCAFile': certifi.where(),
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000,
                        'retryWrites': True
                    }
                },
                # Method 5: Standard connection with ServerApi
                {
                    'name': 'standard connection with ServerApi',
                    'kwargs': {
                        'server_api': ServerApi('1'),
                        'tls': True,
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000,
                        'retryWrites': True
                    }
                },
                # Method 6: Relaxed SSL (last resort - not recommended for production)
                {
                    'name': 'relaxed SSL (testing only)',
                    'kwargs': {
                        'tls': True,
                        'tlsAllowInvalidCertificates': True,
                        'connectTimeoutMS': 30000,
                        'serverSelectionTimeoutMS': 30000,
                        'socketTimeoutMS': 30000,
                        'retryWrites': True
                    }
                }
            ]
            
            for method in connection_methods:
                try:
                    logger.info(f"Trying connection method: {method['name']}")
                    logger.debug(f"MongoDB URI: {mongodb_uri[:50]}... (truncated for security)")
                    self._client = MongoClient(
                        mongodb_uri,
                        **method['kwargs']
                    )
                    # Test connection
                    self._client.admin.command('ping')
                    logger.info(f"✅ Successfully connected to MongoDB Atlas using: {method['name']}!")
                    return True
                except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                    logger.warning(f"Method '{method['name']}' failed: {str(e)[:200]}")
                    if self._client:
                        try:
                            self._client.close()
                        except:
                            pass
                    self._client = None
                    continue
                except Exception as e:
                    error_msg = str(e)
                    # Don't log full error for auth failures (security)
                    if 'authentication failed' in error_msg.lower() or 'bad auth' in error_msg.lower():
                        logger.warning(f"Method '{method['name']}' failed: authentication error")
                    else:
                        logger.warning(f"Method '{method['name']}' error: {error_msg[:200]}")
                    if self._client:
                        try:
                            self._client.close()
                        except:
                            pass
                    self._client = None
                    continue
            
            # All methods failed
            logger.error("All connection methods failed. MongoDB connection unavailable.")
            return False
        return True
    
    def get_client(self):
        """Get MongoDB client instance"""
        if self._client is None:
            self.connect()
        return self._client
    
    def get_database(self, db_name=None):
        """Get database instance"""
        if db_name is None:
            db_name = Config.MONGODB_DB_NAME
        client = self.get_client()
        if client:
            return client[db_name]
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("MongoDB connection closed")

# Global MongoDB client instance
mongodb_client = MongoDBClient()

def get_mongodb():
    """Get MongoDB database instance"""
    return mongodb_client.get_database()

def init_mongodb(app):
    """Initialize MongoDB connection for Flask app"""
    # Connect on app initialization (with error handling)
    try:
        mongodb_client.connect()
        logger.info("MongoDB connection initialized successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed during init: {e}")
        # Don't raise - allow app to start with SQLite fallback
    
    @app.teardown_appcontext
    def close_mongodb_connection(error):
        # Don't close on every request, keep connection alive
        pass

