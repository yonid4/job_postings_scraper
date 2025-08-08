"""
Tests for enhanced rate limiting with RPM, TPM, and RPD support.
"""

import os
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from src.ai.qualification_analyzer import GeminiQuotaManager, QualificationAnalyzer
from src.config.config_manager import AISettings


class TestEnhancedRateLimiting:
    """Test enhanced rate limiting with daily limits."""
    
    def setup_method(self):
        """Set up test environment."""
        # Force reset singleton for testing
        GeminiQuotaManager._instance = None
        
        # Set test environment variables
        os.environ['GEMINI_ENABLE_RATE_LIMITING'] = 'true'
        os.environ['GEMINI_RPM_LIMIT'] = '10'
        os.environ['GEMINI_TPM_LIMIT'] = '1000'
        os.environ['GEMINI_RPD_LIMIT'] = '100'
        
        self.quota_manager = GeminiQuotaManager()
    
    def teardown_method(self):
        """Clean up after tests."""
        # Reset environment variables
        for key in ['GEMINI_ENABLE_RATE_LIMITING', 'GEMINI_RPM_LIMIT', 
                   'GEMINI_TPM_LIMIT', 'GEMINI_RPD_LIMIT']:
            if key in os.environ:
                del os.environ[key]
    
    def test_daily_limit_detection(self):
        """Test detection of daily limit errors."""
        # Create a QualificationAnalyzer to test error detection
        ai_settings = AISettings(
            api_key=os.getenv('GEMINI_API_KEY'),
            model="gemini-2.0-flash-lite",
            qualification_threshold=70,
            max_tokens=2000,
            temperature=0.1,
            analysis_timeout=60,
            retry_attempts=3
        )
        
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'):
            analyzer = QualificationAnalyzer(ai_settings)
        
        test_errors = [
            "Error 429: You have exceeded your daily quota",
            "Quota exceeded: RPD limit reached",
            "You've used 1500 requests per day",
            "Tokens per day limit reached"
        ]
        
        for error in test_errors:
            assert analyzer._is_quota_exceeded_error(error)
    
    def test_retry_delay_extraction_daily(self):
        """Test retry_delay extraction for daily limits."""
        # Test various formats
        test_cases = [
            # Standard format with 24 hours
            ('retry_delay { seconds: 86400 }', 86400),
            # JSON format
            ('{"error": "quota exceeded", "retry_delay": 86400}', 86400),
            # Retry after format
            ('Error: Daily limit reached. Retry after 24 hours', 86400),
            ('Please retry after 1440 minutes', 86400),
            # Daily limit without specific time
            ('Error 429: Daily quota (RPD) exceeded', 86400)
        ]
        
        for error_msg, expected_seconds in test_cases:
            result = self.quota_manager._extract_retry_delay(error_msg)
            assert result == expected_seconds, f"Failed for: {error_msg}"
    
    def test_rpm_limit_enforcement(self):
        """Test RPM limit enforcement."""
        # Record requests up to the limit
        for i in range(10):  # RPM limit is 10
            self.quota_manager.record_request(token_count=50)
        
        # Check status
        status = self.quota_manager.get_rate_limit_status()
        assert status['current_rpm'] == 10
        assert status['rpm_available'] == 0
        
        # Next request should wait
        with patch('time.sleep') as mock_sleep:
            self.quota_manager.check_rate_limits_and_wait(estimated_tokens=50)
            mock_sleep.assert_called_once()
            wait_time = mock_sleep.call_args[0][0]
            assert wait_time > 0 and wait_time <= 60
    
    def test_tpm_limit_enforcement(self):
        """Test TPM limit enforcement."""
        # Use up most of the token limit
        self.quota_manager.record_request(token_count=900)
        
        # Check status
        status = self.quota_manager.get_rate_limit_status()
        assert status['current_tpm'] == 900
        assert status['tpm_available'] == 100
        
        # Request exceeding limit should wait
        with patch('time.sleep') as mock_sleep:
            self.quota_manager.check_rate_limits_and_wait(estimated_tokens=200)
            mock_sleep.assert_called_once()
    
    def test_rpd_limit_enforcement(self):
        """Test RPD limit enforcement."""
        # Record requests up to daily limit
        for i in range(100):  # RPD limit is 100
            self.quota_manager.record_request(token_count=50)
        
        # Check status
        status = self.quota_manager.get_rate_limit_status()
        assert status['current_rpd'] == 100
        assert status['rpd_available'] == 0
        
        # Next request should wait until tomorrow
        with patch('time.sleep') as mock_sleep:
            self.quota_manager.check_rate_limits_and_wait(estimated_tokens=50)
            mock_sleep.assert_called_once()
            wait_time = mock_sleep.call_args[0][0]
            # Should wait until midnight
            assert wait_time > 0 and wait_time <= 86400
    
    def test_daily_reset(self):
        """Test daily counter reset."""
        # Record some requests
        for i in range(50):
            self.quota_manager.record_request(token_count=100)
        
        # Check current status
        status = self.quota_manager.get_rate_limit_status()
        assert status['current_rpd'] == 50
        
        # Simulate next day by manually setting the last reset date to yesterday
        yesterday = datetime.now().date() - timedelta(days=1)
        self.quota_manager._last_daily_reset = yesterday
        
        # Trigger reset by checking status (this will call _check_daily_reset internally)
        status = self.quota_manager.get_rate_limit_status()
        
        # Verify counters were reset
        assert status['current_rpd'] == 0
    
    def test_combined_limits(self):
        """Test handling of multiple limits being reached."""
        # Set up a scenario where both minute and daily limits are close
        os.environ['GEMINI_RPM_LIMIT'] = '5'
        os.environ['GEMINI_RPD_LIMIT'] = '10'
        
        # Re-initialize with new limits
        GeminiQuotaManager._instance = None
        quota_manager = GeminiQuotaManager()
        
        # Add 10 requests total (hits both RPM and RPD limits)
        for i in range(10):
            quota_manager.record_request(token_count=100)
        
        status = quota_manager.get_rate_limit_status()
        # RPM tracks only the last minute, so we might see fewer than 10
        # but RPD tracks all requests for the day
        assert status['current_rpd'] == 10
        assert status['rpd_available'] == 0
        
        # Test that we hit daily limit
        assert status['current_rpd'] >= status['rpd_limit']
    
    def test_quota_error_handling_with_daily_limits(self):
        """Test quota error handling for daily limit errors."""
        error_msg = "Error 429: Daily quota exceeded. retry_delay { seconds: 86400 }"
        
        wait_time = self.quota_manager.handle_quota_error(error_msg)
        
        # Should wait 24 hours + buffer
        assert wait_time == 86410  # 86400 + 10 second buffer
        assert self.quota_manager.is_quota_exceeded()
        
        # Check quota status
        status = self.quota_manager.get_quota_status()
        assert status['quota_exceeded'] is True
        assert status['remaining_time'] > 86400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
