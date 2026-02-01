"""
Test MongoDB connection script
Run this to verify your MongoDB Atlas connection is working
"""
from dotenv import load_dotenv
import os

# Load .env file before importing config
load_dotenv()

from mongodb_client import mongodb_client
from config import Config

def test_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB Atlas connection...")
    if Config.MONGODB_URI:
        print(f"URI: {Config.MONGODB_URI[:50]}...")  # Show first 50 chars for security
    else:
        print("URI: Not set (check .env file)")
    print(f"Database: {Config.MONGODB_DB_NAME}")
    print("-" * 50)
    
    if mongodb_client.connect():
        print("✓ Successfully connected to MongoDB Atlas!")
        
        # Get database
        db = mongodb_client.get_database()
        if db is not None:
            print(f"✓ Database '{Config.MONGODB_DB_NAME}' accessed successfully")
            
            # List collections
            collections = db.list_collection_names()
            print(f"✓ Collections found: {collections if collections else 'None (database is empty)'}")
            
            # Test write
            test_collection = db['test']
            test_collection.insert_one({"test": "connection", "status": "success"})
            print("✓ Test write successful")
            
            # Clean up test document
            test_collection.delete_one({"test": "connection"})
            print("✓ Test document cleaned up")
            
            return True
        else:
            print("✗ Failed to access database")
            return False
    else:
        print("✗ Failed to connect to MongoDB Atlas")
        print("Please check:")
        print("  1. Your connection string is correct")
        print("  2. Your IP address is whitelisted in MongoDB Atlas")
        print("  3. Your database user credentials are correct")
        return False

if __name__ == '__main__':
    test_connection()

