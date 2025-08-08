# Gemini Quota Handling Implementation

## Overview

This document describes the implementation of intelligent quota handling for the Gemini API that respects the `retry_delay` field returned in quota exceeded errors. The system automatically pauses all requests when quota limits are reached and resumes after the appropriate delay period.

## Problem Statement

When the Gemini API returns a quota exceeded error (HTTP 429), it includes a `retry_delay` field that specifies exactly how long to wait before making new requests. The previous implementation used generic exponential backoff, which could result in unnecessary delays or insufficient waiting periods.

Example error from user:
```
429 You exceeded your current quota, please check your plan and billing details.
retry_delay {
  seconds: 44
}
```

## Solution Architecture

### 1. Global Quota Manager (Singleton)

**Class:** `GeminiQuotaManager`

A thread-safe singleton that manages quota state globally across all Gemini API instances in the application.

**Key Features:**
- **Singleton Pattern:** Ensures all analyzer instances share the same quota state
- **Thread Safety:** Uses locks to handle concurrent access safely
- **Intelligent Parsing:** Extracts `retry_delay` from complex error messages
- **Buffer Time:** Adds configurable buffer time to API-provided delays
- **Minimum Wait Time:** Ensures a minimum wait even when `retry_delay` is missing

### 2. Enhanced QualificationAnalyzer

**Updated Methods:**
- `_call_gemini_api_with_retry()`: Now quota-aware
- `_call_gemini_api()`: Legacy method with quota support
- `batch_analyze_jobs_with_retry()`: Respects quota during batch processing

**New Methods:**
- `_is_quota_exceeded_error()`: Detects various quota error formats
- `get_quota_status()`: Returns current quota information
- `reset_quota_status()`: Manual quota reset for testing/emergency

## Implementation Details

### Error Detection

The system detects quota errors using multiple indicators:
```python
quota_indicators = [
    "429",
    "exceeded your current quota", 
    "quota exceeded",
    "quota limit",
    "rate limit",
    "too many requests",
    "retry_delay"
]
```

### Retry Delay Extraction

Uses regex to extract the retry delay from complex error messages:
```python
retry_delay_match = re.search(r'retry_delay\s*\{[^}]*seconds:\s*(\d+)', error_message, re.DOTALL)
```

Handles various formats:
- `retry_delay { seconds: 44 }`
- `retry_delay {\n  seconds: 120\n}`
- Mixed formatting with other text

### Wait Time Calculation

```python
total_wait_seconds = max(retry_delay + buffer_seconds, min_wait_time)
```

**Default Configuration:**
- `buffer_seconds`: 10 seconds (extra safety margin)
- `min_wait_time`: 5 seconds (minimum even without retry_delay)

### Global Pause Mechanism

When quota is exceeded:
1. **Parse Error:** Extract `retry_delay` from the error message
2. **Calculate Wait Time:** Add buffer time to retry_delay
3. **Set Global State:** Mark quota as exceeded until calculated time
4. **Block All Requests:** Any new API calls wait for quota reset
5. **Automatic Resume:** Quota automatically resets after wait period

## Usage Examples

### Basic Usage

```python
from src.ai.qualification_analyzer import QualificationAnalyzer
from src.config.config_manager import AISettings

# Initialize analyzer (quota manager is automatically created)
ai_settings = AISettings(api_key="your_key", model="gemini-2.0-flash-lite")
analyzer = QualificationAnalyzer(ai_settings)

# All API calls now automatically respect quota limits
result = analyzer.analyze_job_qualification_with_retry(request)
```

### Monitoring Quota Status

```python
# Check current quota status
status = analyzer.get_quota_status()
print(f"Quota exceeded: {status['quota_exceeded']}")
print(f"Remaining time: {status['remaining_time']} seconds")
print(f"Reset time: {status['reset_time']}")

# Manual reset for testing
analyzer.reset_quota_status()
```

### Batch Processing

```python
# Batch processing automatically pauses between jobs if quota exceeded
successful_results, all_results = analyzer.batch_analyze_jobs_with_retry(
    jobs=job_list,
    user_profile=user_profile,
    max_retries=2
)
```

## Configuration Options

### GeminiQuotaManager Settings

```python
quota_manager = GeminiQuotaManager()

# Customize timing (not recommended to change defaults)
quota_manager._buffer_seconds = 10      # Buffer time added to retry_delay
quota_manager._min_wait_time = 5        # Minimum wait time
```

### QualificationAnalyzer Integration

The quota manager is automatically initialized and used by all QualificationAnalyzer instances. No additional configuration required.

## Error Handling Flow

### 1. API Call Flow
```
API Call → Check Quota Status → Wait if Exceeded → Make Request → Handle Response
```

### 2. Quota Exceeded Flow
```
429 Error → Parse retry_delay → Set Global Pause → Log Wait Time → Block Future Requests
```

### 3. Resume Flow
```
Wait Period Expires → Reset Quota Status → Resume Normal Operations → Log Resume
```

## Benefits

### 1. **Optimal Wait Times**
- Uses exact delay times from Gemini API
- No unnecessary waiting or insufficient delays
- Respects Google's rate limiting guidance

### 2. **Global Coordination**
- All analyzer instances share quota state
- Prevents multiple simultaneous retry attempts
- Efficient resource utilization

### 3. **Robust Error Handling**
- Handles various quota error formats
- Graceful degradation when retry_delay missing
- Thread-safe operation

### 4. **Operational Monitoring**
- Clear logging of quota events
- Status monitoring capabilities
- Manual intervention options

## Logging Output

### Quota Exceeded
```
🚫 Gemini quota exceeded! Pausing ALL requests for 54 seconds
   API retry_delay: 44s, buffer: 10s
   Requests will resume at: 14:23:45
```

### During Wait Period
```
⏸️ Quota exceeded, waiting before API call for job: Software Engineer
⏳ Waiting 12.3 seconds for quota reset...
```

### Resume
```
📈 Gemini quota period has expired, resuming requests
```

## Testing

### Comprehensive Test Suite

The implementation includes extensive tests covering:

- **Singleton behavior**
- **Retry delay extraction** from various error formats
- **Thread safety** under concurrent access
- **Integration** with QualificationAnalyzer
- **Real error scenario** simulation

**Run Tests:**
```bash
PYTHONPATH=/path/to/project python3 -m pytest tests/test_quota_handling.py -v
```

### Example Test Results
```
✅ Quota system working correctly!
   Extracted retry_delay: 44 seconds
   Total wait time: 54 seconds (44 + 10 buffer)
   Status: {'quota_exceeded': True, 'remaining_time': 53.9, 'reset_time': '2025-08-07T12:28:07'}
```

## Migration Impact

### Backward Compatibility
- All existing methods continue to work unchanged
- Legacy API calls automatically gain quota awareness
- No breaking changes to existing code

### Performance Impact
- Minimal overhead when quota not exceeded
- Prevents unnecessary API calls during quota periods
- Better overall system efficiency

## Future Enhancements

### Potential Improvements
1. **Per-Model Quotas:** Track quotas separately for different Gemini models
2. **Usage Analytics:** Collect metrics on quota utilization
3. **Predictive Throttling:** Slow down requests approaching quota limits
4. **Configuration Management:** Runtime configuration updates

## Troubleshooting

### Common Issues

**1. Quota Never Resets**
- Check system clock synchronization
- Verify error message parsing with debug logs
- Manual reset: `analyzer.reset_quota_status()`

**2. Unexpected Wait Times**
- Check buffer_seconds configuration
- Verify retry_delay extraction in logs
- Consider minimum wait time settings

**3. Threading Issues**
- Ensure proper singleton initialization
- Check for deadlocks in concurrent scenarios
- Review thread safety logs

### Debug Mode
```python
import logging
logging.getLogger("src.ai.qualification_analyzer").setLevel(logging.DEBUG)
```

## Conclusion

The Gemini quota handling implementation provides a robust, efficient solution for managing API quota limits. By respecting the exact retry delays provided by the Gemini API and coordinating globally across all instances, the system ensures optimal resource utilization while maintaining high reliability.

The implementation is thoroughly tested, backward compatible, and provides clear operational visibility through comprehensive logging and monitoring capabilities.
