#!/usr/bin/env python3
"""
Search Strategy Manager

This module provides intelligent decision-making for job search strategies,
determining whether to use API-only or WebDriver-based approaches based on
the complexity of search filters applied.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class SearchMethod(Enum):
    """Enumeration of available search methods."""
    API_ONLY = "api_only"
    WEBDRIVER = "webdriver"


@dataclass
class SearchParameters:
    """Container for search parameters to determine search strategy."""
    keywords: List[str]
    location: str
    distance: Optional[str] = None
    date_posted_days: Optional[int] = None
    work_arrangement: Optional[str] = None
    experience_level: Optional[str] = None
    job_type: Optional[str] = None
    salary_range: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    remote_options: Optional[List[str]] = None


class SearchStrategyManager:
    """
    Manages search strategy decisions based on filter complexity.
    
    This class determines whether to use API-only or WebDriver-based search
    based on the complexity of filters applied. Basic searches (keywords + location)
    can use API-only approaches for better performance, while advanced filters
    require WebDriver for proper handling.
    """
    
    def __init__(self):
        """Initialize the search strategy manager."""
        self.logger = logging.getLogger(__name__)
        
        # Define basic filters that can be handled via API
        self.basic_filters = {
            'keywords', 'location', 'distance'
        }
        
        # Define advanced filters that require WebDriver
        self.advanced_filters = {
            'date_posted_days', 'work_arrangement', 'experience_level',
            'job_type', 'salary_range', 'company_size', 'industry',
            'remote_options'
        }
    
    def should_use_webdriver(self, search_params: SearchParameters) -> bool:
        """
        Determine if WebDriver is needed based on applied filters.
        
        Args:
            search_params: Search parameters to analyze
            
        Returns:
            True if WebDriver is needed, False for API-only approach
        """
        # Check if any advanced filters are applied
        applied_advanced_filters = []
        
        if search_params.date_posted_days is not None:
            applied_advanced_filters.append('date_posted_days')
        
        if search_params.work_arrangement is not None:
            applied_advanced_filters.append('work_arrangement')
        
        if search_params.experience_level is not None:
            applied_advanced_filters.append('experience_level')
        
        if search_params.job_type is not None:
            applied_advanced_filters.append('job_type')
        
        if search_params.salary_range is not None:
            applied_advanced_filters.append('salary_range')
        
        if search_params.company_size is not None:
            applied_advanced_filters.append('company_size')
        
        if search_params.industry is not None:
            applied_advanced_filters.append('industry')
        
        if search_params.remote_options is not None:
            applied_advanced_filters.append('remote_options')
        
        # Use WebDriver if any advanced filters are applied
        if applied_advanced_filters:
            self.logger.info(f"Advanced filters detected: {applied_advanced_filters}. Using WebDriver.")
            return True
        
        # Check if we have basic search parameters
        has_basic_params = bool(search_params.keywords and search_params.location)
        
        if has_basic_params:
            # Use API-only for basic searches (keywords + location only)
            self.logger.info("Basic search parameters only (keywords + location). Using API-only for fast execution.")
            return False
        else:
            # If no parameters, default to WebDriver for safety
            self.logger.warning("No search parameters provided. Defaulting to WebDriver.")
            return True
    
    def get_search_method(self, search_params: SearchParameters) -> SearchMethod:
        """
        Get the recommended search method for the given parameters.
        
        Args:
            search_params: Search parameters to analyze
            
        Returns:
            Recommended search method
        """
        if self.should_use_webdriver(search_params):
            return SearchMethod.WEBDRIVER
        else:
            return SearchMethod.API_ONLY
    
    def get_search_strategy_info(self, search_params: SearchParameters) -> Dict[str, Any]:
        """
        Get detailed information about the search strategy decision.
        
        Args:
            search_params: Search parameters to analyze
            
        Returns:
            Dictionary with strategy information
        """
        method = self.get_search_method(search_params)
        
        # Identify which filters are being used
        applied_filters = []
        if search_params.date_posted_days is not None:
            applied_filters.append(f"date_posted_days={search_params.date_posted_days}")
        if search_params.work_arrangement is not None:
            applied_filters.append(f"work_arrangement={search_params.work_arrangement}")
        if search_params.experience_level is not None:
            applied_filters.append(f"experience_level={search_params.experience_level}")
        if search_params.job_type is not None:
            applied_filters.append(f"job_type={search_params.job_type}")
        if search_params.salary_range is not None:
            applied_filters.append(f"salary_range={search_params.salary_range}")
        if search_params.company_size is not None:
            applied_filters.append(f"company_size={search_params.company_size}")
        if search_params.industry is not None:
            applied_filters.append(f"industry={search_params.industry}")
        if search_params.remote_options is not None:
            applied_filters.append(f"remote_options={search_params.remote_options}")
        
        return {
            'method': method.value,
            'reason': self._get_strategy_reason(search_params),
            'applied_filters': applied_filters,
            'performance_impact': self._get_performance_impact(method),
            'estimated_time': self._get_estimated_time(method, search_params)
        }
    
    def _get_strategy_reason(self, search_params: SearchParameters) -> str:
        """Get the reason for the chosen strategy."""
        if self.should_use_webdriver(search_params):
            advanced_filters = []
            if search_params.date_posted_days is not None:
                advanced_filters.append("date filtering")
            if search_params.work_arrangement is not None:
                advanced_filters.append("work arrangement filtering")
            if search_params.experience_level is not None:
                advanced_filters.append("experience level filtering")
            if search_params.job_type is not None:
                advanced_filters.append("job type filtering")
            if search_params.salary_range is not None:
                advanced_filters.append("salary filtering")
            if search_params.company_size is not None:
                advanced_filters.append("company size filtering")
            if search_params.industry is not None:
                advanced_filters.append("industry filtering")
            if search_params.remote_options is not None:
                advanced_filters.append("remote options filtering")
            
            return f"WebDriver required for advanced filters: {', '.join(advanced_filters)}"
        else:
            return "API-only approach for basic search (keywords + location only) - fast execution"
    
    def _get_performance_impact(self, method: SearchMethod) -> str:
        """Get performance impact description."""
        if method == SearchMethod.API_ONLY:
            return "Fast execution (2-5 seconds)"
        else:
            return "Slower execution (10-30 seconds) due to browser automation"
    
    def _get_estimated_time(self, method: SearchMethod, search_params: SearchParameters) -> str:
        """Get estimated execution time."""
        if method == SearchMethod.API_ONLY:
            return "2-5 seconds"
        else:
            # Estimate based on number of advanced filters
            advanced_filter_count = sum([
                1 if search_params.date_posted_days is not None else 0,
                1 if search_params.work_arrangement is not None else 0,
                1 if search_params.experience_level is not None else 0,
                1 if search_params.job_type is not None else 0,
                1 if search_params.salary_range is not None else 0,
                1 if search_params.company_size is not None else 0,
                1 if search_params.industry is not None else 0,
                1 if search_params.remote_options is not None else 0
            ])
            
            base_time = 15  # Base time for WebDriver setup
            filter_time = advanced_filter_count * 3  # Additional time per filter
            
            return f"{base_time + filter_time}-{base_time + filter_time + 10} seconds"
    
    def create_search_parameters_from_dict(self, params_dict: Dict[str, Any]) -> SearchParameters:
        """
        Create SearchParameters from a dictionary.
        
        Args:
            params_dict: Dictionary containing search parameters
            
        Returns:
            SearchParameters object
        """
        return SearchParameters(
            keywords=params_dict.get('keywords', []),
            location=params_dict.get('location', ''),
            distance=params_dict.get('distance'),
            date_posted_days=params_dict.get('date_posted_days'),
            work_arrangement=params_dict.get('work_arrangement'),
            experience_level=params_dict.get('experience_level'),
            job_type=params_dict.get('job_type'),
            salary_range=params_dict.get('salary_range'),
            company_size=params_dict.get('company_size'),
            industry=params_dict.get('industry'),
            remote_options=params_dict.get('remote_options')
        )


# Global instance for easy access
search_strategy_manager = SearchStrategyManager() 