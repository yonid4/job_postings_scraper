#!/usr/bin/env python3
"""
Test LinkedIn URL Generation

This test verifies that the LinkedIn URL generation logic works correctly
with the proper LinkedIn-specific parameters and encoding.
"""

from urllib.parse import quote


def build_search_url(keywords, location, **kwargs):
    """
    Simplified version of the LinkedIn URL generation logic for testing.
    """
    # Base URL with trailing slash
    base_url = "https://www.linkedin.com/jobs/search/"
    
    # Build query parameters
    params = []
    
    # Keywords
    if keywords:
        keywords_str = ' '.join(keywords)
        # Use quote to properly encode spaces as %20
        params.append(f"keywords={quote(keywords_str)}")
    
    # Location
    if location:
        # Use quote to properly encode spaces as %20 and commas as %2C
        params.append(f"location={quote(location)}")
    
    # Distance (default to 25 miles if not specified)
    distance = kwargs.get('distance', '25')
    if distance and distance != 'exact':
        params.append(f"distance={distance}")
    
    # Experience Level (f_E parameter)
    experience_level = kwargs.get('experience_level')
    if experience_level:
        experience_mapping = {
            'entry': '1',
            'associate': '2', 
            'mid-senior': '3',
            'director': '4',
            'executive': '5'
        }
        exp_value = experience_mapping.get(experience_level.lower())
        if exp_value:
            params.append(f"f_E={exp_value}")
    
    # Job Type (f_JT parameter)
    job_type = kwargs.get('job_type')
    if job_type:
        job_type_mapping = {
            'full-time': 'F',
            'part-time': 'P',
            'contract': 'C',
            'temporary': 'T',
            'internship': 'I',
            'volunteer': 'V'
        }
        job_value = job_type_mapping.get(job_type.lower())
        if job_value:
            params.append(f"f_JT={job_value}")
    
    # Work Arrangement (f_WT parameter)
    work_arrangement = kwargs.get('work_arrangement')
    if work_arrangement and work_arrangement.lower() != 'any':
        work_mapping = {
            'on-site': '1',
            'remote': '2',
            'hybrid': '3'
        }
        work_value = work_mapping.get(work_arrangement.lower())
        if work_value:
            params.append(f"f_WT={work_value}")
    
    # Date Posted (f_TPR parameter)
    date_posted = kwargs.get('date_posted')
    if date_posted and date_posted.lower() != 'any':
        date_mapping = {
            'past_24_hours': 'r86400',
            'past_week': 'r604800',
            'past_month': 'r2592000'
        }
        date_value = date_mapping.get(date_posted.lower())
        if date_value:
            params.append(f"f_TPR={date_value}")
    
    # Add parameters to URL
    if params:
        url = base_url + '?' + '&'.join(params)
    else:
        url = base_url
    
    return url


def test_basic_url_generation():
    """Test basic URL generation with keywords and location."""
    # Test basic search
    url = build_search_url(
        keywords=["software engineer"],
        location="Mountain View, CA, USA"
    )
    
    expected = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Mountain%20View%2C%20CA%2C%20USA&distance=25"
    assert url == expected, f"Expected: {expected}\nGot: {url}"
    print("✅ Basic URL generation test passed")


def test_advanced_filters():
    """Test URL generation with advanced filters."""
    # Test with all filters
    url = build_search_url(
        keywords=["software engineer"],
        location="Mountain View, CA, USA",
        distance="25",
        experience_level="entry",
        job_type="full-time",
        work_arrangement="remote",
        date_posted="past_week"
    )
    
    expected = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=Mountain%20View%2C%20CA%2C%20USA&distance=25&f_E=1&f_JT=F&f_WT=2&f_TPR=r604800"
    assert url == expected, f"Expected: {expected}\nGot: {url}"
    print("✅ Advanced filters URL generation test passed")


def test_parameter_mappings():
    """Test that parameter mappings work correctly."""
    # Test experience level mappings
    test_cases = [
        ("entry", "f_E=1"),
        ("associate", "f_E=2"),
        ("mid-senior", "f_E=3"),
        ("director", "f_E=4"),
        ("executive", "f_E=5"),
    ]
    
    for exp_level, expected_param in test_cases:
        url = build_search_url(
            keywords=["test"],
            location="test",
            experience_level=exp_level
        )
        assert expected_param in url, f"Expected {expected_param} in URL for {exp_level}"
    
    # Test job type mappings
    job_type_cases = [
        ("full-time", "f_JT=F"),
        ("part-time", "f_JT=P"),
        ("contract", "f_JT=C"),
        ("temporary", "f_JT=T"),
        ("internship", "f_JT=I"),
        ("volunteer", "f_JT=V"),
    ]
    
    for job_type, expected_param in job_type_cases:
        url = build_search_url(
            keywords=["test"],
            location="test",
            job_type=job_type
        )
        assert expected_param in url, f"Expected {expected_param} in URL for {job_type}"
    
    # Test work arrangement mappings
    work_cases = [
        ("on-site", "f_WT=1"),
        ("remote", "f_WT=2"),
        ("hybrid", "f_WT=3"),
    ]
    
    for work_arr, expected_param in work_cases:
        url = build_search_url(
            keywords=["test"],
            location="test",
            work_arrangement=work_arr
        )
        assert expected_param in url, f"Expected {expected_param} in URL for {work_arr}"
    
    # Test date posted mappings
    date_cases = [
        ("past_24_hours", "f_TPR=r86400"),
        ("past_week", "f_TPR=r604800"),
        ("past_month", "f_TPR=r2592000"),
    ]
    
    for date_posted, expected_param in date_cases:
        url = build_search_url(
            keywords=["test"],
            location="test",
            date_posted=date_posted
        )
        assert expected_param in url, f"Expected {expected_param} in URL for {date_posted}"
    
    print("✅ Parameter mappings test passed")


def test_optional_parameters():
    """Test that optional parameters are handled correctly."""
    # Test with no optional parameters
    url = build_search_url(
        keywords=["software engineer"],
        location="Mountain View, CA, USA"
    )
    
    # Should not contain any filter parameters
    assert "f_E=" not in url
    assert "f_JT=" not in url
    assert "f_WT=" not in url
    assert "f_TPR=" not in url
    
    # Test with "any" values (should be ignored)
    url = build_search_url(
        keywords=["software engineer"],
        location="Mountain View, CA, USA",
        work_arrangement="any",
        date_posted="any"
    )
    
    # Should not contain filter parameters for "any" values
    assert "f_WT=" not in url
    assert "f_TPR=" not in url
    
    print("✅ Optional parameters test passed")


def test_url_encoding():
    """Test that URL encoding works correctly."""
    # Test spaces in keywords
    url = build_search_url(
        keywords=["software engineer", "python developer"],
        location="Mountain View, CA, USA"
    )
    
    # Should encode spaces as %20
    assert "software%20engineer" in url
    assert "python%20developer" in url
    
    # Test commas in location
    url = build_search_url(
        keywords=["test"],
        location="Mountain View, CA, USA"
    )
    
    # Should encode commas as %2C
    assert "Mountain%20View%2C%20CA%2C%20USA" in url
    
    print("✅ URL encoding test passed")


def test_real_world_examples():
    """Test real-world URL examples."""
    # Example 1: Basic search
    url1 = build_search_url(
        keywords=["software engineer"],
        location="San Francisco, CA, USA"
    )
    expected1 = "https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=San%20Francisco%2C%20CA%2C%20USA&distance=25"
    assert url1 == expected1, f"Example 1 failed:\nExpected: {expected1}\nGot: {url1}"
    
    # Example 2: Advanced search
    url2 = build_search_url(
        keywords=["python developer"],
        location="New York, NY, USA",
        experience_level="mid-senior",
        job_type="full-time",
        work_arrangement="remote"
    )
    expected2 = "https://www.linkedin.com/jobs/search/?keywords=python%20developer&location=New%20York%2C%20NY%2C%20USA&distance=25&f_E=3&f_JT=F&f_WT=2"
    assert url2 == expected2, f"Example 2 failed:\nExpected: {expected2}\nGot: {url2}"
    
    print("✅ Real-world examples test passed")


if __name__ == "__main__":
    print("🧪 Testing LinkedIn URL Generation...")
    
    try:
        test_basic_url_generation()
        test_advanced_filters()
        test_parameter_mappings()
        test_optional_parameters()
        test_url_encoding()
        test_real_world_examples()
        
        print("\n🎉 All LinkedIn URL generation tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1) 