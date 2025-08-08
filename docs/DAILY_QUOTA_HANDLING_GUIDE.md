# Daily Quota Handling Guide

## Overview

The Job Application Automation System now properly handles Gemini API daily quota exhaustion, especially for free tier users who are limited to 200 requests per day.

## The Problem

When using the free tier of Gemini API, you're limited to:
- **200 requests per day** for the free tier
- Once exhausted, the API returns a 429 error with message:
  ```
  GenerateRequestsPerDayPerProjectPerModel-FreeTier
  quota_value: 200
  ```

## The Solution

### 1. **Early Detection**
The system now:
- Detects daily quota exhaustion errors specifically
- Stops retrying immediately (no point retrying when daily limit is hit)
- Provides clear error messages to users

### 2. **Graceful Handling**
When daily quota is exhausted:
- The system throws a `DailyQuotaExhaustedException`
- Job evaluation stops immediately
- Remaining jobs are saved but not evaluated
- Users get a clear message about the quota limit

### 3. **Proactive Checking**
Before evaluating each job:
- The system checks if quota is available
- If daily limit is reached, evaluation stops
- Already scraped jobs are still saved to the database

## Error Messages

### When Quota is Exhausted
```
🛑 Daily quota exhausted for free tier (200 requests/day). Cannot process more jobs today.
Daily free tier limit (200 requests) reached. Please wait until tomorrow or upgrade your plan.
```

### In the UI
```
Daily AI analysis limit reached (200 requests for free tier). Please wait until tomorrow or upgrade your Gemini API plan.
AI evaluation stopped due to quota limits.
```

## Configuration

### Environment Variables
```bash
# Rate limiting is enabled by default
GEMINI_ENABLE_RATE_LIMITING=true

# Daily limit for free tier (automatically detected)
GEMINI_RPD_LIMIT=200
```

## How It Works

### Detection Flow
1. API returns 429 error with `GenerateRequestsPerDayPerProjectPerModel-FreeTier`
2. System recognizes this as daily quota exhaustion
3. Sets quota exceeded period until midnight
4. Stops all further API calls

### Processing Flow
```python
for job in scraped_jobs:
    # Save job to database (always works)
    save_job(job)
    
    # Check quota before evaluation
    if not quota_available:
        log("Stopping evaluations - daily quota reached")
        break
    
    # Evaluate job (only if quota available)
    evaluate_job(job)
```

## User Experience

### What Users See
1. Jobs are still scraped and saved
2. AI evaluation stops when quota is hit
3. Clear message about quota limits
4. Suggestion to wait or upgrade

### What Still Works
- Job scraping continues
- Jobs are saved to database
- Manual job review is available
- All non-AI features work normally

## Recommendations

### For Free Tier Users
1. **Limit searches**: Each job evaluation uses 1 API request
2. **Prioritize**: Search for most relevant jobs first
3. **Time wisely**: Quota resets at midnight (your local time)
4. **Consider upgrading**: If you need more than 200 evaluations/day

### For Development
1. **Test with limits**: Set `GEMINI_RPD_LIMIT=5` for testing
2. **Monitor usage**: Check `get_rate_limit_status()` for current usage
3. **Handle gracefully**: Always check `is_quota_available()` before API calls

## Upgrading from Free Tier

To get more requests:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Upgrade to a paid plan
3. Update your API key in `.env`
4. Enjoy higher limits!

## Technical Details

### Key Components

1. **DailyQuotaExhaustedException**
   - Custom exception for daily quota exhaustion
   - Prevents unnecessary retries
   - Provides clear error context

2. **is_quota_available()**
   - Checks current quota status
   - Returns human-readable messages
   - Distinguishes between temporary and daily limits

3. **Quota Status Tracking**
   - Tracks when quota will reset
   - Identifies daily vs minute-based limits
   - Provides remaining time estimates

### Implementation Files
- `src/ai/qualification_analyzer.py`: Core quota handling
- `frontend/app_supabase.py`: Frontend integration
- `tests/test_rate_limiting_enhanced.py`: Comprehensive tests

## Troubleshooting

### "Still getting errors after waiting"
- Check if it's past midnight in your timezone
- Verify your API key is correct
- Ensure you haven't hit other limits (RPM/TPM)

### "Jobs not being evaluated"
- Check quota status in logs
- Look for "🛑 Stopping job evaluations" messages
- Verify AI settings are configured

### "Want to reset quota manually"
```python
# In code (for testing only)
analyzer.quota_manager.reset_quota_status()
```

## Future Improvements

1. **Quota Dashboard**: Visual display of current usage
2. **Smart Scheduling**: Automatically resume when quota resets
3. **Multi-key Support**: Rotate between multiple API keys
4. **Usage Predictions**: Warn before hitting limits
