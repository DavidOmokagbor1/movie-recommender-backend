#!/usr/bin/env python3
"""
Script to fetch real movie posters from TMDB API and OMDb API
Falls back to placeholder if APIs are unavailable or movie not found
"""
import sys
import os
import time
import re
import logging
from urllib.parse import quote

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, mongodb
from db_helper import use_mongodb

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'  # w500 = 500px width
OMDB_API_KEY = os.getenv('OMDB_API_KEY', '')
OMDB_BASE_URL = 'http://www.omdbapi.com/'

# Rate limiting
TMDB_RATE_LIMIT_DELAY = 0.25  # 40 requests per 10 seconds = ~0.25s between requests
OMDB_RATE_LIMIT_DELAY = 1.0   # Be conservative with OMDb free tier

def clean_movie_title(title):
    """Clean movie title for API search"""
    # Remove year in parentheses
    title = re.sub(r'\s*\(\d{4}\)\s*', '', title).strip()
    # Remove extra whitespace
    title = ' '.join(title.split())
    return title

def extract_year_from_title(title):
    """Extract year from title if present"""
    match = re.search(r'\((\d{4})\)', title)
    if match:
        return int(match.group(1))
    return None

def fetch_poster_from_tmdb(movie_title, release_year=None):
    """
    Fetch movie poster from TMDB API
    Returns poster URL or None
    """
    if not TMDB_API_KEY:
        logger.debug("TMDB_API_KEY not set, skipping TMDB")
        return None
    
    try:
        import requests
        
        # Search for movie
        search_url = f"{TMDB_BASE_URL}/search/movie"
        params = {
            'api_key': TMDB_API_KEY,
            'query': clean_movie_title(movie_title),
            'language': 'en-US'
        }
        
        if release_year:
            params['year'] = release_year
        
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            # Get first result (most relevant)
            movie = data['results'][0]
            poster_path = movie.get('poster_path')
            
            if poster_path:
                poster_url = f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                logger.debug(f"TMDB found poster for '{movie_title}': {poster_url}")
                return poster_url
            else:
                logger.debug(f"TMDB found movie '{movie_title}' but no poster_path")
        else:
            logger.debug(f"TMDB: No results for '{movie_title}'")
        
        return None
        
    except Exception as e:
        logger.warning(f"TMDB API error for '{movie_title}': {e}")
        return None

def fetch_poster_from_omdb(movie_title, release_year=None):
    """
    Fetch movie poster from OMDb API
    Returns poster URL or None
    """
    if not OMDB_API_KEY:
        logger.debug("OMDB_API_KEY not set, skipping OMDb")
        return None
    
    try:
        import requests
        
        # OMDb search by title
        params = {
            'apikey': OMDB_API_KEY,
            't': clean_movie_title(movie_title),
            'type': 'movie'
        }
        
        if release_year:
            params['y'] = release_year
        
        response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Response') == 'True' and data.get('Poster'):
            poster_url = data['Poster']
            # Check if it's a valid URL (not "N/A")
            if poster_url and poster_url != 'N/A' and poster_url.startswith('http'):
                logger.debug(f"OMDb found poster for '{movie_title}': {poster_url}")
                return poster_url
            else:
                logger.debug(f"OMDb found movie '{movie_title}' but poster is N/A")
        else:
            logger.debug(f"OMDb: No results for '{movie_title}'")
        
        return None
        
    except Exception as e:
        logger.warning(f"OMDb API error for '{movie_title}': {e}")
        return None

def generate_placeholder_poster(movie_title):
    """Generate placeholder poster URL as fallback"""
    clean_title = clean_movie_title(movie_title)
    if len(clean_title) > 25:
        clean_title = clean_title[:22] + "..."
    encoded_title = quote(clean_title)
    return f"https://via.placeholder.com/300x450/2c3e50/ecf0f1?text={encoded_title}"

def fetch_movie_poster(movie_title, release_year=None):
    """
    Try to fetch poster from APIs, with fallback to placeholder
    Priority: TMDB -> OMDb -> Placeholder
    """
    # Try TMDB first (better poster quality)
    poster_url = fetch_poster_from_tmdb(movie_title, release_year)
    if poster_url:
        time.sleep(TMDB_RATE_LIMIT_DELAY)  # Rate limiting
        return poster_url
    
    # Try OMDb as fallback
    poster_url = fetch_poster_from_omdb(movie_title, release_year)
    if poster_url:
        time.sleep(OMDB_RATE_LIMIT_DELAY)  # Rate limiting
        return poster_url
    
    # Fallback to placeholder
    logger.debug(f"Using placeholder for '{movie_title}'")
    return generate_placeholder_poster(movie_title)

def update_posters_in_mongodb(use_apis=True, limit=None):
    """
    Update poster URLs for all movies in MongoDB
    Args:
        use_apis: If True, try to fetch from APIs. If False, use placeholders only
        limit: Maximum number of movies to update (None = all)
    """
    with app.app_context():
        if not use_mongodb() or mongodb is None:
            logger.error("MongoDB is not available or has no data")
            return False
        
        try:
            movies_collection = mongodb['movies']
            movies = list(movies_collection.find({}))
            total = len(movies)
            
            if limit:
                movies = movies[:limit]
                total = limit
            
            logger.info(f"Found {total} movies to update")
            
            if use_apis:
                if not TMDB_API_KEY and not OMDB_API_KEY:
                    logger.warning("⚠️  No API keys found! Set TMDB_API_KEY or OMDB_API_KEY environment variables")
                    logger.warning("   Using placeholder posters instead")
                    use_apis = False
                else:
                    logger.info(f"Using APIs: TMDB={'✓' if TMDB_API_KEY else '✗'}, OMDb={'✓' if OMDB_API_KEY else '✗'}")
            
            updated = 0
            skipped = 0
            errors = 0
            
            for idx, movie in enumerate(movies, 1):
                movie_id = movie.get('_id')
                title = movie.get('title', 'Unknown')
                current_poster = movie.get('poster')
                release_year = extract_year_from_title(title)
                
                # Skip if poster already exists and is from API (not placeholder)
                if current_poster and use_apis:
                    if 'image.tmdb.org' in current_poster or 'omdbapi.com' in current_poster or 'imdb.com' in current_poster:
                        logger.debug(f"Movie {movie_id} ({title}) already has API poster, skipping")
                        skipped += 1
                        continue
                
                try:
                    # Fetch poster
                    if use_apis:
                        poster_url = fetch_movie_poster(title, release_year)
                    else:
                        poster_url = generate_placeholder_poster(title)
                    
                    # Update movie in MongoDB
                    movies_collection.update_one(
                        {'_id': movie_id},
                        {'$set': {'poster': poster_url}}
                    )
                    updated += 1
                    
                    if updated % 50 == 0:
                        logger.info(f"Progress: {updated}/{total} updated, {skipped} skipped, {errors} errors")
                    
                except Exception as e:
                    logger.error(f"Error updating movie {movie_id} ({title}): {e}")
                    errors += 1
            
            logger.info("=" * 50)
            logger.info(f"✅ Update complete!")
            logger.info(f"   Updated: {updated}")
            logger.info(f"   Skipped: {skipped}")
            logger.info(f"   Errors: {errors}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating posters: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch real movie posters from TMDB/OMDb APIs')
    parser.add_argument('--no-apis', action='store_true', help='Use placeholders only (no API calls)')
    parser.add_argument('--limit', type=int, help='Limit number of movies to update (for testing)')
    parser.add_argument('--test', action='store_true', help='Test with first 5 movies only')
    
    args = parser.parse_args()
    
    if args.test:
        args.limit = 5
    
    print("🎬 Fetching Real Movie Posters")
    print("=" * 50)
    
    if not args.no_apis:
        if not TMDB_API_KEY and not OMDB_API_KEY:
            print("\n⚠️  WARNING: No API keys found!")
            print("   Set environment variables:")
            print("   export TMDB_API_KEY='your_tmdb_api_key'")
            print("   export OMDB_API_KEY='your_omdb_api_key'")
            print("\n   Continuing with placeholder posters...")
            print("   (Use --no-apis to suppress this warning)")
            time.sleep(2)
    
    success = update_posters_in_mongodb(use_apis=not args.no_apis, limit=args.limit)
    
    if success:
        print("\n✅ Done!")
        if not args.no_apis and (TMDB_API_KEY or OMDB_API_KEY):
            print("\n💡 Tip: Real movie posters have been fetched from APIs")
        else:
            print("\n💡 Tip: To get real posters, set TMDB_API_KEY or OMDB_API_KEY")
            print("   Get free API keys at:")
            print("   - TMDB: https://www.themoviedb.org/settings/api")
            print("   - OMDb: https://www.omdbapi.com/apikey.aspx")
    else:
        print("\n❌ Failed to update posters")
        sys.exit(1)






