# Movie Poster API Integration Guide

This guide explains how to set up and use real movie posters from TMDB and OMDb APIs.

## Quick Start

### 1. Get API Keys

#### TMDB API (Recommended)
1. Go to https://www.themoviedb.org/signup
2. Create a free account
3. Go to Settings → API → Request API Key
4. Choose "Developer" option
5. Fill out the form and submit
6. Copy your API key

#### OMDb API (Alternative/Fallback)
1. Go to https://www.omdbapi.com/apikey.aspx
2. Choose "FREE" tier (1000 requests/day)
3. Enter your email
4. Check your email for the API key
5. Copy your API key

### 2. Set Environment Variables

**Option A: Export in terminal (temporary)**
```bash
export TMDB_API_KEY='your_tmdb_api_key_here'
export OMDB_API_KEY='your_omdb_api_key_here'
```

**Option B: Add to your shell profile (permanent)**
```bash
# Add to ~/.zshrc or ~/.bash_profile
echo 'export TMDB_API_KEY="your_tmdb_api_key_here"' >> ~/.zshrc
echo 'export OMDB_API_KEY="your_omdb_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**Option C: Create a .env file (recommended for development)**
```bash
# Create .env file in backend directory
cd fullstack_recsys/backend
cat > .env << EOF
TMDB_API_KEY=your_tmdb_api_key_here
OMDB_API_KEY=your_omdb_api_key_here
EOF
```

### 3. Install Dependencies

```bash
cd fullstack_recsys/backend
pip3 install requests --user
```

### 4. Run the Script

**Fetch real posters for all movies:**
```bash
python3 fetch_real_posters.py
```

**Test with first 5 movies:**
```bash
python3 fetch_real_posters.py --test
```

**Use placeholders only (no API calls):**
```bash
python3 fetch_real_posters.py --no-apis
```

**Update limited number of movies:**
```bash
python3 fetch_real_posters.py --limit 100
```

## How It Works

1. **Priority Order:**
   - First tries TMDB API (better quality posters)
   - Falls back to OMDb API if TMDB fails
   - Uses placeholder if both APIs fail

2. **Rate Limiting:**
   - TMDB: ~0.25s delay between requests (40 req/10s limit)
   - OMDb: 1s delay (1000 req/day free tier)
   - Script automatically handles rate limits

3. **Smart Updates:**
   - Skips movies that already have API-sourced posters
   - Only updates placeholders or missing posters
   - Extracts year from movie title for better matching

## API Limits

### TMDB API
- **Free tier:** 40 requests per 10 seconds
- **No daily limit** (reasonable use)
- **Best for:** High-quality poster images

### OMDb API
- **Free tier:** 1,000 requests per day
- **Paid tier:** Unlimited (starting at $1/month)
- **Best for:** Fallback when TMDB doesn't have the movie

## Troubleshooting

### "No API keys found" warning
- Make sure you've set the environment variables
- Check with: `echo $TMDB_API_KEY`
- Restart terminal after adding to shell profile

### Rate limit errors
- Script automatically handles rate limits
- If you see errors, wait a few minutes and retry
- Use `--limit` to update in smaller batches

### Movies not found
- Some movies may not be in TMDB/OMDb databases
- Script automatically falls back to placeholder
- This is normal for obscure or very old movies

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip3 install requests --user
```

## Example Output

```
🎬 Fetching Real Movie Posters
==================================================
Using APIs: TMDB=✓, OMDb=✓
Found 1682 movies to update
Progress: 50/1682 updated, 0 skipped, 0 errors
Progress: 100/1682 updated, 0 skipped, 0 errors
...
==================================================
✅ Update complete!
   Updated: 1682
   Skipped: 0
   Errors: 0
```

## Notes

- The script preserves existing API-sourced posters
- Placeholder posters are replaced with real ones when available
- You can re-run the script anytime to update missing posters
- API keys are stored in environment variables (not in code)






