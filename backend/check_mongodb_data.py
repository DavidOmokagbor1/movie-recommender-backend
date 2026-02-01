#!/usr/bin/env python3
"""
Check MongoDB Database Status
This script checks if your app data is uploaded to MongoDB
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, mongodb
from app.model import User, Movie, Interaction
from mongodb_client import mongodb_client
from db_helper import use_mongodb

def check_mongodb_status():
    """Check MongoDB connection and data status"""
    print("=" * 60)
    print("🔍 MongoDB Database Status Check")
    print("=" * 60)
    print()
    
    # 1. Check MongoDB Connection
    print("1️⃣  Checking MongoDB Connection...")
    print("-" * 60)
    try:
        if mongodb_client.connect():
            print("✅ MongoDB Connection: SUCCESS")
            db_instance = mongodb_client.get_database()
            if db_instance is not None:
                print(f"✅ Database '{db_instance.name}' accessed")
            else:
                print("❌ Database access failed")
                return
        else:
            print("❌ MongoDB Connection: FAILED")
            print("   The app is currently using SQLite as fallback")
            print()
            print("   Common issues:")
            print("   - SSL/TLS handshake errors (check Python SSL certificates)")
            print("   - Network connectivity issues")
            print("   - MongoDB Atlas IP whitelist restrictions")
            return
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        return
    
    print()
    
    # 2. Check Collections
    print("2️⃣  Checking MongoDB Collections...")
    print("-" * 60)
    try:
        collections = db_instance.list_collection_names()
        print(f"📁 Collections found: {len(collections)}")
        if collections:
            for col in collections:
                print(f"   - {col}")
        else:
            print("   ⚠️  No collections found (database is empty)")
        print()
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return
    
    # 3. Check Data in Each Collection
    print("3️⃣  Checking Data in Collections...")
    print("-" * 60)
    
    # Check Movies
    movie_count = 0
    try:
        movies_collection = db_instance['movies']
        movie_count = movies_collection.count_documents({})
        print(f"🎬 Movies: {movie_count}")
        if movie_count > 0:
            sample = movies_collection.find_one()
            if sample:
                print(f"   Sample: {sample.get('title', 'N/A')} (ID: {sample.get('_id', 'N/A')})")
    except Exception as e:
        print(f"❌ Error checking movies: {e}")
        movie_count = 0
    
    # Check Users
    user_count = 0
    try:
        users_collection = db_instance['users']
        user_count = users_collection.count_documents({})
        print(f"👤 Users: {user_count}")
        if user_count > 0:
            sample = users_collection.find_one()
            if sample:
                print(f"   Sample: {sample.get('username', 'N/A')} (ID: {sample.get('_id', 'N/A')})")
    except Exception as e:
        print(f"❌ Error checking users: {e}")
        user_count = 0
    
    # Check Interactions
    interaction_count = 0
    try:
        interactions_collection = db_instance['interactions']
        interaction_count = interactions_collection.count_documents({})
        print(f"💬 Interactions: {interaction_count}")
    except Exception as e:
        print(f"❌ Error checking interactions: {e}")
        interaction_count = 0
    
    print()
    
    # 4. Compare with SQLite
    print("4️⃣  Comparing with SQLite Database...")
    print("-" * 60)
    
    with app.app_context():
        try:
            sqlite_movies = Movie.query.count()
            sqlite_users = User.query.count()
            sqlite_interactions = Interaction.query.count()
            
            print(f"📊 SQLite Data:")
            print(f"   Movies: {sqlite_movies}")
            print(f"   Users: {sqlite_users}")
            print(f"   Interactions: {sqlite_interactions}")
            print()
            
            print(f"📊 MongoDB Data:")
            print(f"   Movies: {movie_count}")
            print(f"   Users: {user_count}")
            print(f"   Interactions: {interaction_count}")
            print()
            
            # Comparison
            if movie_count == 0 and sqlite_movies > 0:
                print("⚠️  WARNING: SQLite has movies but MongoDB is empty!")
                print("   → Run migration: python3 migrate_to_mongodb.py")
            elif movie_count > 0:
                if movie_count == sqlite_movies:
                    print("✅ Movies match between SQLite and MongoDB")
                else:
                    print(f"⚠️  Movie count mismatch: SQLite={sqlite_movies}, MongoDB={movie_count}")
            
            if user_count == 0 and sqlite_users > 0:
                print("⚠️  WARNING: SQLite has users but MongoDB is empty!")
            elif user_count > 0:
                if user_count == sqlite_users:
                    print("✅ Users match between SQLite and MongoDB")
                else:
                    print(f"⚠️  User count mismatch: SQLite={sqlite_users}, MongoDB={user_count}")
            
        except Exception as e:
            print(f"❌ Error comparing databases: {e}")
    
    print()
    
    # 5. Check which database app is using
    print("5️⃣  Current App Database Status...")
    print("-" * 60)
    try:
        is_using_mongodb = use_mongodb()
        if is_using_mongodb:
            print("✅ App is currently using: MongoDB")
        else:
            print("⚠️  App is currently using: SQLite (fallback)")
            print("   Reason: MongoDB connection failed or has no data")
    except Exception as e:
        print(f"❌ Error checking app status: {e}")
    
    print()
    print("=" * 60)
    print("📋 Summary")
    print("=" * 60)
    
    if movie_count > 0:
        print("✅ MongoDB has data uploaded")
        print(f"   - {movie_count} movies")
        print(f"   - {user_count} users")
        print(f"   - {interaction_count} interactions")
    else:
        print("❌ MongoDB is empty - data has NOT been uploaded")
        print("   To upload data, run:")
        print("   cd backend")
        print("   python3 migrate_to_mongodb.py")
    
    print("=" * 60)

if __name__ == '__main__':
    check_mongodb_status()



