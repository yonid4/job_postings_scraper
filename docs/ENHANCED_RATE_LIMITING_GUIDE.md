# Enhanced Rate Limiting Guide

## Overview

The Job Application Automation System now includes comprehensive rate limiting for the Gemini API that handles all quota types:
- **RPM** (Requests Per Minute)
- **TPM** (Tokens Per Minute)  
- **RPD** (Requests Per Day)

This ensures your application respects all API limits and automatically handles quota errors with intelligent retry logic.

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable rate limiting (recommended)
GEMINI_ENABLE_RATE_LIMITING=true

# Minute-based limits
GEMINI_RPM_LIMIT=20          # Requests per minute
GEMINI_TPM_LIMIT=2000000     # Tokens per minute (2M default)

# Daily limits
GEMINI_RPD_LIMIT=1500        # Requests per day
```

### Default Values

If not specified, the system uses these conservative defaults:
- RPM: 20 requests/minute
- TPM: 2,000,000 tokens/minute
- RPD: 1,500 requests/day

## How It Works

### 1. Proactive Rate Limiting

Before making any API call, the system:
- Checks current usage against all limits
- Waits if necessary to avoid hitting limits
- Tracks both minute-based and daily usage

### 2. Quota Error Handling

When a quota error occurs:
- Extracts the `retry_delay` from the error message
- Adds a buffer time (10 seconds by default)
- Pauses ALL requests globally until the quota resets

### 3. Retry Delay Extraction

The system can extract retry delays from various formats:

```
# Standard Gemini format
retry_delay {
  seconds: 86400
}

# JSON format
{"error": "quota exceeded", "retry_delay": 86400}

# Human-readable format
"Retry after 24 hours"
"Please retry after 1440 minutes"
```

### 4. Daily Reset

Daily counters automatically reset at midnight (local time).

## Error Messages

### Minute-based Limits
```
🚦 Rate limiting: Waiting 45.2s due to RPM limit
🚦 Rate limiting: Waiting 30.5s due to TPM limit
```

### Daily Limits
```
🚦 Daily rate limit reached: Waiting until tomorrow (18.5 hours) due to RPD limit
```

### Quota Errors
```
🚫 Gemini quota exceeded! Pausing ALL requests for 86410 seconds
   API retry_delay: 86400s, buffer: 10s
   Requests will resume at: 00:00:15
```

## Status Monitoring

You can check current rate limit status programmatically:

```python
status = quota_manager.get_rate_limit_status()
print(f"Requests today: {status['current_rpd']}/{status['rpd_limit']}")
print(f"Available requests: {status['rpd_available']}")
```

## Best Practices

### 1. Set Conservative Limits
Start with lower limits than your actual quota to avoid hitting hard limits:
```bash
# If your actual limit is 2000 RPD, set:
GEMINI_RPD_LIMIT=1800
```

### 2. Monitor Daily Usage
Keep track of your daily usage patterns:
- Peak hours may require lower minute-based limits
- Batch processing should be spread throughout the day

### 3. Handle Long Waits
For daily limit errors, the system may wait up to 24 hours. Consider:
- Implementing notification systems
- Scheduling jobs to run during off-peak hours
- Using multiple API keys with load balancing

### 4. Token Estimation
The system estimates tokens before requests:
- Job descriptions: ~500-2000 tokens
- Analysis responses: ~500-1000 tokens
- Adjust `GEMINI_TPM_LIMIT` based on your average token usage

## Troubleshooting

### 1. Frequent Rate Limiting
If you're hitting limits too often:
- Reduce `MAX_JOBS_PER_SESSION`
- Increase delays between requests
- Lower your rate limits in `.env`

### 2. Daily Limits Hit Early
If daily limits are reached too early:
- Spread job processing throughout the day
- Implement job prioritization
- Consider upgrading your API quota

### 3. Token Estimation Issues
If token estimates are inaccurate:
- Monitor actual vs estimated tokens
- Adjust the estimation multiplier in code
- Set more conservative TPM limits

## Testing

Run the enhanced rate limiting tests:

```bash
python tests/test_rate_limiting_enhanced.py
```

This verifies:
- All limit types are enforced
- Retry delays are extracted correctly
- Daily resets work properly
- Combined limits are handled correctly

## Implementation Details

The rate limiting is implemented in `GeminiQuotaManager`:
- Singleton pattern ensures global rate limiting
- Thread-safe for concurrent operations
- Automatic daily counter reset
- Comprehensive error detection
- Flexible retry delay extraction

## Future Enhancements

Potential improvements:
1. Persistent usage tracking across restarts
2. Rate limit visualization dashboard
3. Automatic limit adjustment based on patterns
4. Multi-key rotation for higher throughput
5. Webhook notifications for limit warnings
