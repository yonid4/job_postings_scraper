"""
Test suite for Gemini quota handling implementation.

This module tests the GeminiQuotaManager and quota-aware retry logic
to ensure proper handling of API quota limits and retry delays.
"""

import pytest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.ai.qualification_analyzer import (
    GeminiQuotaManager, 
    QualificationAnalyzer, 
    AnalysisRequest
)
from src.config.config_manager import AISettings


class TestGeminiQuotaManager:
    """Test the global quota manager functionality."""
    
    def setup_method(self):
        """Reset quota manager state for each test."""
        # Get the singleton instance and reset it
        self.quota_manager = GeminiQuotaManager()
        self.quota_manager.reset_quota_status()
    
    def test_quota_manager_singleton(self):
        """Test that GeminiQuotaManager follows singleton pattern."""
        manager1 = GeminiQuotaManager()
        manager2 = GeminiQuotaManager()
        
        assert manager1 is manager2
        assert id(manager1) == id(manager2)
    
    def test_initial_state(self):
        """Test that quota manager starts in non-exceeded state."""
        assert not self.quota_manager.is_quota_exceeded()
        
        status = self.quota_manager.get_quota_status()
        assert status["quota_exceeded"] is False
        assert status["remaining_time"] == 0
        assert status["reset_time"] is None
    
    def test_extract_retry_delay_valid(self):
        """Test extracting retry_delay from valid Gemini error message."""
        error_message = """
        429 You exceeded your current quota, please check your plan and billing details.
        violations {
          quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
          quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
        }
        retry_delay {
          seconds: 44
        }
        """
        
        retry_delay = self.quota_manager._extract_retry_delay(error_message)
        assert retry_delay == 44
    
    def test_extract_retry_delay_different_format(self):
        """Test extracting retry_delay from different format variations."""
        # Test with spaces
        error1 = "retry_delay { seconds: 120 }"
        assert self.quota_manager._extract_retry_delay(error1) == 120
        
        # Test with newlines
        error2 = """retry_delay {
  seconds: 30
}"""
        assert self.quota_manager._extract_retry_delay(error2) == 30
        
        # Test with mixed formatting
        error3 = "Some other text retry_delay{\n  seconds:   77   \n} more text"
        assert self.quota_manager._extract_retry_delay(error3) == 77
    
    def test_extract_retry_delay_missing(self):
        """Test handling of error messages without retry_delay."""
        error_message = "429 You exceeded your current quota, please check your plan"
        
        retry_delay = self.quota_manager._extract_retry_delay(error_message)
        assert retry_delay == 0
    
    def test_extract_retry_delay_invalid_format(self):
        """Test handling of malformed retry_delay."""
        error_message = "retry_delay { seconds: not_a_number }"
        
        retry_delay = self.quota_manager._extract_retry_delay(error_message)
        assert retry_delay == 0
    
    def test_handle_quota_error(self):
        """Test handling of quota exceeded error."""
        error_message = """
        429 You exceeded your current quota
        retry_delay {
          seconds: 30
        }
        """
        
        # Handle the quota error
        total_wait = self.quota_manager.handle_quota_error(error_message)
        
        # Should add buffer time to retry_delay
        expected_wait = 30 + 10  # retry_delay + buffer_seconds
        assert total_wait == expected_wait
        
        # Quota should now be exceeded
        assert self.quota_manager.is_quota_exceeded()
        
        # Status should reflect the exceeded state
        status = self.quota_manager.get_quota_status()
        assert status["quota_exceeded"] is True
        assert status["remaining_time"] > 0
        assert status["reset_time"] is not None
    
    def test_handle_quota_error_minimum_wait(self):
        """Test that minimum wait time is respected."""
        error_message = "429 You exceeded quota"  # No retry_delay
        
        total_wait = self.quota_manager.handle_quota_error(error_message)
        
        # Should use minimum wait time (0 + 10 buffer = 10)
        expected_wait = 10  # 0 retry_delay + 10 buffer_seconds (max with min_wait_time=5)
        assert total_wait == expected_wait
    
    def test_quota_expiry(self):
        """Test that quota status expires after wait time."""
        # Set a short quota period for testing
        self.quota_manager._min_wait_time = 1  # 1 second for testing
        self.quota_manager._buffer_seconds = 1  # 1 second buffer for testing
        
        error_message = "429 You exceeded quota"
        self.quota_manager.handle_quota_error(error_message)
        
        # Should be exceeded initially
        assert self.quota_manager.is_quota_exceeded()
        
        # Wait for expiry (0 retry_delay + 1 buffer = 1 second, max with min_wait=1)
        time.sleep(1.1)  # Slightly longer than total wait time
        
        # Should no longer be exceeded
        assert not self.quota_manager.is_quota_exceeded()
    
    def test_manual_reset(self):
        """Test manual quota status reset."""
        error_message = """
        429 You exceeded your current quota
        retry_delay {
          seconds: 60
        }
        """
        
        self.quota_manager.handle_quota_error(error_message)
        assert self.quota_manager.is_quota_exceeded()
        
        # Manual reset
        self.quota_manager.reset_quota_status()
        assert not self.quota_manager.is_quota_exceeded()
    
    def test_wait_for_quota_reset(self):
        """Test waiting for quota reset."""
        # Set a short wait time for testing
        self.quota_manager._min_wait_time = 1
        self.quota_manager._buffer_seconds = 1  # 1 second buffer for testing
        
        error_message = "429 You exceeded quota"
        start_time = time.time()
        
        self.quota_manager.handle_quota_error(error_message)
        
        # Wait for reset (should block for ~1 second + 1 buffer = 2 seconds max with min_wait)
        self.quota_manager.wait_for_quota_reset()
        
        elapsed_time = time.time() - start_time
        
        # Should have waited approximately the wait time (1 second)
        expected_wait = max(0 + 1, 1)  # max(retry_delay + buffer, min_wait)
        assert elapsed_time >= expected_wait
        assert elapsed_time < expected_wait + 1.0  # Some tolerance
        
        # Should no longer be exceeded
        assert not self.quota_manager.is_quota_exceeded()
    
    def test_thread_safety(self):
        """Test that quota manager is thread-safe."""
        results = []
        error_count = 0
        
        def handle_quota_worker():
            nonlocal error_count
            try:
                error_message = f"429 retry_delay {{ seconds: {threading.current_thread().ident % 10 + 1} }}"
                wait_time = self.quota_manager.handle_quota_error(error_message)
                results.append(wait_time)
            except Exception:
                error_count += 1
        
        # Create multiple threads that handle quota errors simultaneously
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=handle_quota_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should not have any errors
        assert error_count == 0
        
        # Should have results from all threads
        assert len(results) == 5
        
        # Quota should be exceeded
        assert self.quota_manager.is_quota_exceeded()


class TestQualificationAnalyzerQuotaIntegration:
    """Test quota handling integration with QualificationAnalyzer."""
    
    def setup_method(self):
        """Set up analyzer for each test."""
        self.ai_settings = AISettings(
            api_key="test_key",
            model="gemini-2.0-flash-lite",
            temperature=0.7,
            max_tokens=1000
        )
        
        # Create analyzer with mocked model
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model_class:
                self.mock_model = Mock()
                mock_model_class.return_value = self.mock_model
                
                self.analyzer = QualificationAnalyzer(self.ai_settings)
                
                # Reset quota status
                self.analyzer.quota_manager.reset_quota_status()
    
    def test_is_quota_exceeded_error_detection(self):
        """Test detection of various quota exceeded error formats."""
        test_cases = [
            ("429 You exceeded your current quota", True),
            ("Rate limit exceeded", True),
            ("Too many requests", True),
            ("quota limit reached", True),
            ("retry_delay { seconds: 30 }", True),
            ("quota exceeded", True),  # lowercase version
            ("Network timeout error", False),
            ("Invalid API key", False),
            ("Internal server error", False),
        ]
        
        for error_message, expected in test_cases:
            result = self.analyzer._is_quota_exceeded_error(error_message)
            assert result == expected, f"Failed for: {error_message}"
    
    def test_api_call_with_quota_exceeded(self):
        """Test API call behavior when quota is exceeded."""
        # Mock a quota exceeded error
        quota_error = Exception("""
        429 You exceeded your current quota, please check your plan and billing details.
        retry_delay {
          seconds: 5
        }
        """)
        
        self.mock_model.generate_content.side_effect = quota_error
        
        # Create a simple request
        request = AnalysisRequest(
            job_title="Test Job",
            company="Test Company",
            job_description="Test description",
            ai_settings=self.ai_settings
        )
        
        # Should raise quota exceeded error
        with pytest.raises(Exception) as exc_info:
            self.analyzer._call_gemini_api_with_retry(request, attempt=0)
        
        # Should contain quota information
        assert "Quota exceeded" in str(exc_info.value)
        assert "waiting" in str(exc_info.value)
        
        # Quota manager should be in exceeded state
        assert self.analyzer.quota_manager.is_quota_exceeded()
    
    def test_api_call_waits_during_quota_exceeded(self):
        """Test that API calls wait when quota is already exceeded."""
        # Set quota to exceeded state with short wait time
        self.analyzer.quota_manager._min_wait_time = 1
        self.analyzer.quota_manager.handle_quota_error("429 quota exceeded")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Test response"
        self.mock_model.generate_content.return_value = mock_response
        
        request = AnalysisRequest(
            job_title="Test Job",
            company="Test Company", 
            job_description="Test description",
            ai_settings=self.ai_settings
        )
        
        # Measure time for API call
        start_time = time.time()
        
        with patch.object(self.analyzer, '_create_analysis_prompt', return_value="test prompt"):
            result = self.analyzer._call_gemini_api_with_retry(request, attempt=0)
        
        elapsed_time = time.time() - start_time
        
        # Should have waited for quota reset
        assert elapsed_time >= 1.0
        assert result == "Test response"
    
    def test_legacy_api_call_quota_handling(self):
        """Test that legacy API call method also respects quota limits."""
        # Set quota exceeded
        self.analyzer.quota_manager.handle_quota_error("429 quota exceeded")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Legacy response"
        self.mock_model.generate_content.return_value = mock_response
        
        # Should wait before making call
        start_time = time.time()
        result = self.analyzer._call_gemini_api("test prompt")
        elapsed_time = time.time() - start_time
        
        assert elapsed_time >= self.analyzer.quota_manager._min_wait_time
        assert result == "Legacy response"
    
    def test_quota_status_methods(self):
        """Test quota status retrieval and reset methods."""
        # Initial status
        status = self.analyzer.get_quota_status()
        assert status["quota_exceeded"] is False
        
        # Set quota exceeded
        self.analyzer.quota_manager.handle_quota_error("429 retry_delay { seconds: 30 }")
        
        # Status should reflect exceeded state
        status = self.analyzer.get_quota_status()
        assert status["quota_exceeded"] is True
        assert status["remaining_time"] > 0
        
        # Reset quota
        self.analyzer.reset_quota_status()
        
        # Should be back to normal
        status = self.analyzer.get_quota_status()
        assert status["quota_exceeded"] is False


def test_quota_manager_integration_example():
    """
    Example test showing how the quota system works in practice.
    This simulates the actual error scenario described in the user query.
    """
    
    # Initialize quota manager and ensure clean state
    quota_manager = GeminiQuotaManager()
    quota_manager.reset_quota_status()
    
    # Reset buffer and min wait time to default values for this test
    quota_manager._buffer_seconds = 10
    quota_manager._min_wait_time = 5
    
    # Simulate the exact error from the user's example
    error_message = """WARNING:src.ai.qualification_analyzer:⚠️ Gemini analysis attempt 1 failed for job 'Software Engineer, Full-Stack': 429 You exceeded your current quota, please check your plan and billing details. For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits. [violations {
  quota_metric: "generativelanguage.googleapis.com/generate_content_free_tier_requests"
  quota_id: "GenerateRequestsPerDayPerProjectPerModel-FreeTier"
  quota_dimensions {
    key: "model"
    value: "gemini-2.0-flash-lite"
  }
  quota_dimensions {
    key: "location"
    value: "global"
  }
  quota_value: 200
}
, links {
  description: "Learn more about Gemini API quotas"
  url: "https://ai.google.dev/gemini-api/docs/rate-limits"
}
, retry_delay {
  seconds: 44
}"""
    
    # Handle the quota error
    total_wait_time = quota_manager.handle_quota_error(error_message)
    
    # Should extract 44 seconds + 10 second buffer = 54
    assert total_wait_time == 54
    
    # Quota should be exceeded
    assert quota_manager.is_quota_exceeded()
    
    # Status should show the remaining time
    status = quota_manager.get_quota_status()
    assert status["quota_exceeded"] is True
    assert status["remaining_time"] > 50  # Should be close to 54 seconds
    assert status["reset_time"] is not None
    
    print(f"✅ Quota system working correctly!")
    print(f"   Extracted retry_delay: 44 seconds")
    print(f"   Total wait time: {total_wait_time} seconds (44 + 10 buffer)")
    print(f"   Status: {status}")


if __name__ == "__main__":
    # Run the integration example
    test_quota_manager_integration_example()
    
    print("\n🎯 To run all tests:")
    print("pytest tests/test_quota_handling.py -v")
