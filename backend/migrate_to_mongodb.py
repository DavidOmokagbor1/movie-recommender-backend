"""
Migration script to move data from SQLite to MongoDB
Run this after verifying MongoDB connection works
"""
from app import app, db
from app.model import User, Movie, Interaction
from mongodb_client import mongodb_client
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_to_mongodb():
    """Migrate all data from SQLite to MongoDB"""
    print("Starting migration from SQLite to MongoDB...")
    print("-" * 50)
    
    # Connect to MongoDB
    if not mongodb_client.connect():
        print("✗ Failed to connect to MongoDB. Aborting migration.")
        return False
    
    mongodb = mongodb_client.get_database()
    
    with app.app_context():
        # Migrate Users
        print("\n1. Migrating Users...")
        users = User.query.all()
        users_collection = mongodb['users']
        user_count = 0
        
        for user in users:
            user_doc = {
                '_id': user.id,
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'age': user.age,
                'gender': user.gender,
                'created_at': user.created_at,
                'is_active': user.is_active
            }
            try:
                users_collection.replace_one({'_id': user.id}, user_doc, upsert=True)
                user_count += 1
            except Exception as e:
                logger.error(f"Error migrating user {user.id}: {e}")
        
        print(f"   ✓ Migrated {user_count} users")
        
        # Migrate Movies
        print("\n2. Migrating Movies...")
        movies = Movie.query.all()
        movies_collection = mongodb['movies']
        movie_count = 0
        
        for movie in movies:
            movie_doc = {
                '_id': movie.id,
                'title': movie.title,
                'genre': movie.genre,
                'date': movie.date.isoformat() if movie.date else None,
                'poster': movie.poster
            }
            try:
                movies_collection.replace_one({'_id': movie.id}, movie_doc, upsert=True)
                movie_count += 1
            except Exception as e:
                logger.error(f"Error migrating movie {movie.id}: {e}")
        
        print(f"   ✓ Migrated {movie_count} movies")
        
        # Migrate Interactions
        print("\n3. Migrating Interactions...")
        interactions = Interaction.query.all()
        interactions_collection = mongodb['interactions']
        interaction_count = 0
        
        for interaction in interactions:
            interaction_doc = {
                'user_id': interaction.user_id,
                'movie_id': interaction.movie_id,
                'rating': interaction.rating,
                'timestamp': interaction.timestamp,
                'interaction_type': interaction.interaction_type,
                'created_at': interaction.created_at.isoformat() if interaction.created_at else None
            }
            try:
                # Use compound index for user_id + movie_id
                interactions_collection.replace_one(
                    {'user_id': interaction.user_id, 'movie_id': interaction.movie_id},
                    interaction_doc,
                    upsert=True
                )
                interaction_count += 1
            except Exception as e:
                logger.error(f"Error migrating interaction {interaction.user_id}-{interaction.movie_id}: {e}")
        
        print(f"   ✓ Migrated {interaction_count} interactions")
        
        # Create indexes for better performance
        print("\n4. Creating indexes...")
        try:
            users_collection.create_index('username', unique=True, sparse=True)
            users_collection.create_index('email', unique=True, sparse=True)
            movies_collection.create_index('title')
            interactions_collection.create_index([('user_id', 1), ('movie_id', 1)], unique=True)
            interactions_collection.create_index('user_id')
            interactions_collection.create_index('movie_id')
            print("   ✓ Indexes created successfully")
        except Exception as e:
            logger.warning(f"Some indexes may already exist: {e}")
        
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print(f"Summary:")
        print(f"  - Users: {user_count}")
        print(f"  - Movies: {movie_count}")
        print(f"  - Interactions: {interaction_count}")
        print("=" * 50)
        
        return True

if __name__ == '__main__':
    migrate_to_mongodb()





