#!/usr/bin/env python3
"""
Test script to check what imports are failing
"""
import sys
from pathlib import Path

# Add the backend directory to sys.path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

print("🔧 Testing imports...")
print(f"Python path: {sys.path}")
print(f"Backend path: {backend_path}")

# Test each import individually
tests = [
    ("ScrapingConfig", "from src.scrapers.base_scraper import ScrapingConfig"),
    ("LinkedInAPIScraper", "from src.scrapers.linkedin_api_scraper import LinkedInAPIScraper"),
    ("EnhancedLinkedInScraper", "from src.scrapers.linkedin_scraper_enhanced import EnhancedLinkedInScraper"),
    ("JobListing", "from src.data.models import JobListing"),
]

for name, import_statement in tests:
    try:
        exec(import_statement)
        print(f"✅ {name}: SUCCESS")
    except Exception as e:
        print(f"❌ {name}: FAILED - {e}")

print("\n🔍 Checking file structure...")
src_path = backend_path / "src"
if src_path.exists():
    print(f"✅ src directory exists: {src_path}")
    
    scrapers_path = src_path / "scrapers"
    if scrapers_path.exists():
        print(f"✅ scrapers directory exists: {scrapers_path}")
        scraper_files = list(scrapers_path.glob("*.py"))
        print(f"📁 Scraper files: {[f.name for f in scraper_files]}")
    else:
        print(f"❌ scrapers directory missing: {scrapers_path}")
        
    data_path = src_path / "data"
    if data_path.exists():
        print(f"✅ data directory exists: {data_path}")
        data_files = list(data_path.glob("*.py"))
        print(f"📁 Data files: {[f.name for f in data_files]}")
    else:
        print(f"❌ data directory missing: {data_path}")
else:
    print(f"❌ src directory missing: {src_path}")