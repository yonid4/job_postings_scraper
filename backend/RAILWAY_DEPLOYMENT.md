# Railway Deployment Guide

## Quick Deployment Checklist

### ✅ Files Ready for Deployment
- `Dockerfile` - Container configuration with dynamic port support
- `railway.toml` - Railway-specific configuration  
- `requirements.txt` - All Python dependencies included
- `api/working_main.py` - Main FastAPI application
- All scraper modules working with proper imports

### 🚂 Railway Setup Steps

1. **Go to [railway.app](https://railway.app)**
   - Sign up or login
   - Click "New Project"

2. **Choose Deployment Method**
   - Option A: "Deploy from GitHub repo" (recommended)
   - Option B: "Empty Project" + manual upload

3. **Configure Project**
   - Railway auto-detects Dockerfile
   - Uses our railway.toml configuration
   - Sets up health checks at `/health`

4. **Environment Variables**
   Add in Railway dashboard:
   ```
   PYTHONPATH=/app
   DISPLAY=:99
   ```
   
   Optional (for AI scoring):
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Get your production URL

### 🧪 Testing Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app.railway.app/health

# Debug endpoint  
curl https://your-app.railway.app/api/debug/test

# Job search test
curl -X POST https://your-app.railway.app/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{"keywords": "Python Developer", "location": "San Francisco", "jobLimit": 3}'
```

### 🔧 Expected Results

**Health Check:**
```json
{"status": "healthy", "message": "Backend API is running"}
```

**Debug Test:**
```json
{
  "status": "ok",
  "scrapers": {
    "simple_scraper_available": true,
    "api_scraper_available": true, 
    "enhanced_scraper_available": true
  }
}
```

**Job Search:**
```json
{
  "success": true,
  "jobs_count": 50,
  "strategy_info": {"method": "Fast API Mode"},
  "results": [...]
}
```

### 🔄 Frontend Integration

Once Railway is deployed, update your frontend's API endpoint:

In `/frontend-react/.env.local`:
```
SCRAPING_SERVICE_URL=https://your-app.railway.app
```

Or in your API route file:
```typescript
const SCRAPING_SERVICE_URL = process.env.SCRAPING_SERVICE_URL || 'https://your-app.railway.app';
```

### 🤖 Enabling AI Scoring (Optional)

To enable AI-powered job scoring:

1. **Add Gemini API Key** to Railway environment variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   ```

2. **Uncomment AI code** in `api/working_main.py`:
   - Uncomment AI imports (lines 13-18)
   - Uncomment AI analyzer initialization (lines 45-60)  
   - Replace `"score": 75` with `**calculate_ai_score(job)` (lines 278, 318)

3. **Redeploy** to Railway

### 🚨 Troubleshooting

**Build Fails:**
- Check Railway build logs
- Verify all requirements.txt dependencies
- Ensure Dockerfile syntax is correct

**Scrapers Not Available:**
- Check environment variables are set
- Look for import errors in Railway logs
- Verify Python path is correct

**Slow Response:**
- LinkedIn rate limiting (normal)
- Cold start delay (first request after idle)
- High job limit causing timeout

### 📊 Performance Notes

- **First request**: May take 10-15 seconds (cold start)
- **Subsequent requests**: 2-5 seconds  
- **Job search limit**: Recommend 25-50 jobs max
- **AI scoring**: Adds 5-10 seconds per job (when enabled)

### 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app/)
- [Railway Environment Variables](https://docs.railway.app/guides/variables)
- [Railway Dockerfile Guide](https://docs.railway.app/guides/dockerfiles)