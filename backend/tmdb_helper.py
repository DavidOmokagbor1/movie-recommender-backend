"""
Helper module to fetch detailed movie information from TMDB API
"""
import os
import logging
import requests
import re
from config import Config

logger = logging.getLogger(__name__)

TMDB_API_KEY = Config.TMDB_API_KEY
TMDB_BASE_URL = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p'

def clean_movie_title(title):
    """Clean movie title for API search"""
    # Remove year in parentheses
    title = re.sub(r'\s*\(\d{4}\)\s*', '', title).strip()
    # Remove extra whitespace
    title = ' '.join(title.split())
    return title

def extract_year_from_date(date_str):
    """Extract year from date string"""
    if not date_str:
        return None
    match = re.search(r'(\d{4})', str(date_str))
    if match:
        return int(match.group(1))
    return None

def search_movie_in_tmdb(movie_title, release_year=None):
    """
    Search for a movie in TMDB and return the movie ID
    Returns movie_id or None
    """
    if not TMDB_API_KEY:
        logger.debug("TMDB_API_KEY not set")
        return None
    
    try:
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
            return movie.get('id')
        
        return None
        
    except Exception as e:
        logger.warning(f"TMDB search error for '{movie_title}': {e}")
        return None

def get_movie_details_from_tmdb(movie_id):
    """
    Get detailed movie information from TMDB using movie ID
    Returns dict with movie details or None
    """
    if not TMDB_API_KEY:
        return None
    
    try:
        # Get movie details with all related data
        details_url = f"{TMDB_BASE_URL}/movie/{movie_id}"
        params = {
            'api_key': TMDB_API_KEY,
            'language': 'en-US',
            'append_to_response': 'credits,videos,images,similar,recommendations,reviews,watch/providers,keywords,release_dates'
        }
        
        response = requests.get(details_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Format the response
        result = {
            'tmdb_id': data.get('id'),
            'title': data.get('title'),
            'original_title': data.get('original_title'),
            'overview': data.get('overview'),
            'tagline': data.get('tagline'),
            'release_date': data.get('release_date'),
            'runtime': data.get('runtime'),  # in minutes
            'budget': data.get('budget'),
            'revenue': data.get('revenue'),
            'status': data.get('status'),
            'original_language': data.get('original_language'),
            'popularity': data.get('popularity'),
            'vote_average': data.get('vote_average'),
            'vote_count': data.get('vote_count'),
            'poster_path': f"{TMDB_IMAGE_BASE_URL}/w500{data.get('poster_path')}" if data.get('poster_path') else None,
            'backdrop_path': f"{TMDB_IMAGE_BASE_URL}/original{data.get('backdrop_path')}" if data.get('backdrop_path') else None,
            'genres': [g.get('name') for g in data.get('genres', [])],
            'production_companies': [c.get('name') for c in data.get('production_companies', [])],
            'production_countries': [c.get('name') for c in data.get('production_countries', [])],
            'spoken_languages': [l.get('name') for l in data.get('spoken_languages', [])],
            'homepage': data.get('homepage'),
            'imdb_id': data.get('imdb_id'),
        }
        
        # Get rating/certification
        certifications_url = f"{TMDB_BASE_URL}/movie/{movie_id}/release_dates"
        cert_params = {'api_key': TMDB_API_KEY}
        try:
            cert_response = requests.get(certifications_url, params=cert_params, timeout=5)
            if cert_response.status_code == 200:
                cert_data = cert_response.json()
                # Get US rating
                for country in cert_data.get('results', []):
                    if country.get('iso_3166_1') == 'US':
                        releases = country.get('release_dates', [])
                        if releases:
                            result['certification'] = releases[0].get('certification', '')
                            break
        except:
            pass  # Rating is optional
        
        # Get cast and crew
        credits = data.get('credits', {})
        cast = credits.get('cast', [])
        crew = credits.get('crew', [])
        
        # Format cast (top 10)
        result['cast'] = [
            {
                'id': person.get('id'),
                'name': person.get('name'),
                'character': person.get('character'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{person.get('profile_path')}" if person.get('profile_path') else None,
                'order': person.get('order', 999)
            }
            for person in sorted(cast, key=lambda x: x.get('order', 999))[:10]
        ]
        
        # Format crew (directors, writers, etc.)
        directors = [c for c in crew if c.get('job') == 'Director']
        writers = [c for c in crew if c.get('job') in ['Writer', 'Screenplay', 'Story', 'Novel']]
        producers = [c for c in crew if c.get('job') in ['Producer', 'Executive Producer']]
        
        result['directors'] = [
            {
                'id': person.get('id'),
                'name': person.get('name'),
                'job': person.get('job'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{person.get('profile_path')}" if person.get('profile_path') else None
            }
            for person in directors[:3]
        ]
        
        result['writers'] = [
            {
                'id': person.get('id'),
                'name': person.get('name'),
                'job': person.get('job'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{person.get('profile_path')}" if person.get('profile_path') else None
            }
            for person in writers[:5]
        ]
        
        result['producers'] = [
            {
                'id': person.get('id'),
                'name': person.get('name'),
                'job': person.get('job'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{person.get('profile_path')}" if person.get('profile_path') else None
            }
            for person in producers[:3]
        ]
        
        # Get all videos (trailers, teasers, clips, etc.)
        videos = data.get('videos', {}).get('results', [])
        result['videos'] = [
            {
                'id': v.get('id'),
                'key': v.get('key'),
                'name': v.get('name'),
                'site': v.get('site'),
                'type': v.get('type'),
                'url': f"https://www.youtube.com/watch?v={v.get('key')}" if v.get('site') == 'YouTube' else None,
                'thumbnail': f"https://img.youtube.com/vi/{v.get('key')}/hqdefault.jpg" if v.get('site') == 'YouTube' else None
            }
            for v in videos if v.get('site') == 'YouTube'
        ]
        
        # Get trailer (first trailer found)
        trailer = next((v for v in videos if v.get('type') == 'Trailer' and v.get('site') == 'YouTube'), None)
        if trailer:
            result['trailer_key'] = trailer.get('key')
            result['trailer_url'] = f"https://www.youtube.com/watch?v={trailer.get('key')}"
        
        # Get similar movies
        similar = data.get('similar', {}).get('results', [])
        result['similar_movies'] = [
            {
                'id': m.get('id'),
                'title': m.get('title'),
                'poster_path': f"{TMDB_IMAGE_BASE_URL}/w342{m.get('poster_path')}" if m.get('poster_path') else None,
                'release_date': m.get('release_date'),
                'vote_average': m.get('vote_average'),
                'overview': m.get('overview')
            }
            for m in similar[:12]  # Top 12 similar movies
        ]
        
        # Get recommended movies
        recommendations = data.get('recommendations', {}).get('results', [])
        result['recommended_movies'] = [
            {
                'id': m.get('id'),
                'title': m.get('title'),
                'poster_path': f"{TMDB_IMAGE_BASE_URL}/w342{m.get('poster_path')}" if m.get('poster_path') else None,
                'release_date': m.get('release_date'),
                'vote_average': m.get('vote_average'),
                'overview': m.get('overview')
            }
            for m in recommendations[:12]  # Top 12 recommendations
        ]
        
        # Get images
        images = data.get('images', {})
        result['images'] = {
            'posters': [
                {
                    'file_path': f"{TMDB_IMAGE_BASE_URL}/w500{img.get('file_path')}",
                    'aspect_ratio': img.get('aspect_ratio'),
                    'height': img.get('height'),
                    'width': img.get('width')
                }
                for img in images.get('posters', [])[:20]  # Top 20 posters
            ],
            'backdrops': [
                {
                    'file_path': f"{TMDB_IMAGE_BASE_URL}/original{img.get('file_path')}",
                    'aspect_ratio': img.get('aspect_ratio'),
                    'height': img.get('height'),
                    'width': img.get('width')
                }
                for img in images.get('backdrops', [])[:20]  # Top 20 backdrops
            ]
        }
        
        # Get reviews
        reviews = data.get('reviews', {}).get('results', [])
        result['reviews'] = [
            {
                'id': r.get('id'),
                'author': r.get('author'),
                'author_details': {
                    'name': r.get('author_details', {}).get('name'),
                    'username': r.get('author_details', {}).get('username'),
                    'avatar_path': f"{TMDB_IMAGE_BASE_URL}/w45{r.get('author_details', {}).get('avatar_path')}" if r.get('author_details', {}).get('avatar_path') else None,
                    'rating': r.get('author_details', {}).get('rating')
                },
                'content': r.get('content'),
                'created_at': r.get('created_at'),
                'updated_at': r.get('updated_at'),
                'url': r.get('url')
            }
            for r in reviews[:10]  # Top 10 reviews
        ]
        
        # Get watch providers
        watch_providers = data.get('watch/providers', {}).get('results', {})
        us_providers = watch_providers.get('US', {})
        result['watch_providers'] = {
            'buy': [
                {
                    'provider_id': p.get('provider_id'),
                    'provider_name': p.get('provider_name'),
                    'logo_path': f"{TMDB_IMAGE_BASE_URL}/w45{p.get('logo_path')}" if p.get('logo_path') else None
                }
                for p in us_providers.get('buy', [])
            ],
            'rent': [
                {
                    'provider_id': p.get('provider_id'),
                    'provider_name': p.get('provider_name'),
                    'logo_path': f"{TMDB_IMAGE_BASE_URL}/w45{p.get('logo_path')}" if p.get('logo_path') else None
                }
                for p in us_providers.get('rent', [])
            ],
            'flatrate': [
                {
                    'provider_id': p.get('provider_id'),
                    'provider_name': p.get('provider_name'),
                    'logo_path': f"{TMDB_IMAGE_BASE_URL}/w45{p.get('logo_path')}" if p.get('logo_path') else None
                }
                for p in us_providers.get('flatrate', [])
            ]
        }
        
        # Get keywords
        keywords = data.get('keywords', {}).get('keywords', [])
        result['keywords'] = [k.get('name') for k in keywords[:20]]
        
        # Get all crew members (more comprehensive)
        all_crew = crew
        result['all_crew'] = [
            {
                'id': c.get('id'),
                'name': c.get('name'),
                'job': c.get('job'),
                'department': c.get('department'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{c.get('profile_path')}" if c.get('profile_path') else None
            }
            for c in all_crew
        ]
        
        # Get full cast (not just top 10)
        result['full_cast'] = [
            {
                'id': person.get('id'),
                'name': person.get('name'),
                'character': person.get('character'),
                'profile_path': f"{TMDB_IMAGE_BASE_URL}/w185{person.get('profile_path')}" if person.get('profile_path') else None,
                'order': person.get('order', 999)
            }
            for person in sorted(cast, key=lambda x: x.get('order', 999))
        ]
        
        # Get release dates by country
        release_dates = data.get('release_dates', {}).get('results', [])
        result['release_dates'] = {}
        for country in release_dates:
            country_code = country.get('iso_3166_1')
            releases = country.get('release_dates', [])
            if releases:
                result['release_dates'][country_code] = [
                    {
                        'certification': r.get('certification', ''),
                        'release_date': r.get('release_date'),
                        'type': r.get('type'),
                        'note': r.get('note', '')
                    }
                    for r in releases
                ]
        
        return result
        
    except Exception as e:
        logger.warning(f"TMDB details error for movie_id {movie_id}: {e}")
        return None

def get_enhanced_movie_details(movie_title, release_date=None):
    """
    Get enhanced movie details by searching TMDB and fetching full details
    Returns dict with enhanced movie info or None
    """
    if not TMDB_API_KEY:
        return None
    
    # Extract year from release date
    release_year = extract_year_from_date(release_date) if release_date else None
    
    # Search for movie in TMDB
    tmdb_id = search_movie_in_tmdb(movie_title, release_year)
    
    if not tmdb_id:
        return None
    
    # Get detailed information
    return get_movie_details_from_tmdb(tmdb_id)

