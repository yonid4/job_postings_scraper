"""
Google Sheets integration for the AI Job Qualification Screening System.

This module provides functionality to write job qualification analysis data to Google Sheets
for tracking and monitoring purposes.
"""

from dotenv import load_dotenv
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import QualificationResult, JobListing, QualificationStatus, UserDecision

import logging

# Configure logging to output to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

class GoogleSheetsManager:
    """
    Manages Google Sheets integration for qualification analysis tracking.
    
    This class handles writing job qualification analysis data to Google Sheets,
    including job listings, qualification results, and user decisions.
    """
    
    # Google Sheets API scopes
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Default column headers for the qualified jobs sheet
    QUALIFIED_JOBS_HEADERS = [
        'Job Title',
        'Company Name',
        'Job URL',
        'Qualification Score',
        'AI Reasoning',
        'Required Experience',
        'Education Requirements',
        'Key Skills Mentioned',
        'Analysis Date',
        'User Decision',
        'User Notes',
        'Manual Override Reason',
        'AI Model Used',
        'Analysis Duration',
        'Created Date',
        'Last Updated'
    ]
    
    # Default column headers for the job listings sheet
    JOB_LISTING_HEADERS = [
        'Date Scraped',
        'Job Title',
        'Company',
        'Location',
        'Job URL',
        'Job Site',
        'Description',
        'Requirements',
        'Responsibilities',
        'Benefits',
        'Salary Min',
        'Salary Max',
        'Salary Currency',
        'Job Type',
        'Experience Level',
        'Remote Type',
        'Application URL',
        'Application Deadline',
        'Application Requirements',
        'Posted Date',
        'Is Duplicate',
        'Duplicate Of',
        'Notes'
    ]
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        qualified_jobs_worksheet: str = "Qualified Jobs",
        job_listings_worksheet: str = "Job Listings"
    ) -> None:
        """
        Initialize the Google Sheets manager.
        
        Args:
            credentials_path: Path to Google Sheets API credentials JSON file
            spreadsheet_id: Google Sheets spreadsheet ID
            qualified_jobs_worksheet: Name of worksheet for qualified jobs
            job_listings_worksheet: Name of worksheet for job listings
        """
        self.credentials_path = credentials_path or os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH', '')
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')
        self.qualified_jobs_worksheet = qualified_jobs_worksheet
        self.job_listings_worksheet = job_listings_worksheet
        
        if not self.credentials_path:
            raise ValueError("Google Sheets credentials path not provided")
        
        if not self.spreadsheet_id:
            raise ValueError("Google Sheets spreadsheet ID not provided")
        
        self.service = None
        self._initialize_service()
        self._initialize_worksheets()
    
    def _initialize_service(self) -> None:
        """Initialize the Google Sheets API service."""
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=self.SCOPES
            )
            self.service = build('sheets', 'v4', credentials=credentials)
            logging.info("Google Sheets API service initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize Google Sheets service: {e}")
            raise
    
    def _initialize_worksheets(self) -> None:
        """Initialize the worksheets with proper headers."""
        try:
            # Ensure qualified jobs worksheet exists with headers
            self._ensure_worksheet_headers(
                self.qualified_jobs_worksheet, 
                self.QUALIFIED_JOBS_HEADERS
            )
            
            # Ensure job listings worksheet exists with headers
            self._ensure_worksheet_headers(
                self.job_listings_worksheet, 
                self.JOB_LISTING_HEADERS
            )
            
            logging.info("Worksheets initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize worksheets: {e}")
            raise
    
    def _ensure_worksheet_headers(self, worksheet_name: str, headers: List[str]) -> None:
        """Ensure worksheet exists and has proper headers."""
        try:
            # Check if worksheet exists
            try:
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{worksheet_name}!A1:Z1"  # Google Sheets API handles spaces automatically
                ).execute()
                
                existing_headers = result.get('values', [[]])[0] if result.get('values') else []
                
                # If worksheet exists but headers don't match, update them
                if existing_headers != headers:
                    self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{worksheet_name}!A1",  # Google Sheets API handles spaces automatically
                        valueInputOption='RAW',
                        body={'values': [headers]}
                    ).execute()
                    logging.info(f"Updated headers for worksheet: {worksheet_name}")
                
            except HttpError as e:
                if e.resp.status == 404:
                    # Worksheet doesn't exist, create it
                    self._create_worksheet(worksheet_name, headers)
                else:
                    raise
                    
        except Exception as e:
            logging.error(f"Error ensuring worksheet headers: {e}")
            raise
    
    def _create_worksheet(self, worksheet_name: str, headers: List[str]) -> None:
        """Create a new worksheet with headers."""
        try:
            # Add new worksheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': worksheet_name
                    }
                }
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            # Add headers
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{worksheet_name}!A1",  # Google Sheets API handles spaces automatically
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            
            logging.info(f"Created new worksheet: {worksheet_name}")
            
        except Exception as e:
            logging.error(f"Failed to create worksheet {worksheet_name}: {e}")
            raise
    
    def _normalize_linkedin_url(self, url: str) -> str:
        """
        Normalize LinkedIn URL for comparison.
        
        Args:
            url: LinkedIn URL to normalize
            
        Returns:
            Normalized URL string
        """
        if not url:
            return ""
        
        url = url.strip().lower()
        
        # Remove common LinkedIn URL variations
        # Convert to basic format: linkedin.com/jobs/view/...
        if "linkedin.com/jobs/view/" in url:
            # Extract the job ID
            parts = url.split("linkedin.com/jobs/view/")
            if len(parts) > 1:
                job_id = parts[1].split("?")[0].split("/")[0]  # Remove query params and trailing slashes
                return f"linkedin.com/jobs/view/{job_id}"
        
        # Handle other LinkedIn job URL formats
        if "linkedin.com/jobs/collections/" in url:
            # Extract the job ID from collection URLs
            parts = url.split("linkedin.com/jobs/collections/")
            if len(parts) > 1:
                job_id = parts[1].split("?")[0].split("/")[0]
                return f"linkedin.com/jobs/view/{job_id}"
        
        return url
    
    def is_job_duplicate(self, job_title: str, company: str, job_url: str = None) -> bool:
        """
        Check if a job already exists in the spreadsheet by LinkedIn URL only.
        
        Args:
            job_title: Job title (for logging purposes only)
            company: Company name (for logging purposes only)
            job_url: Job URL to check (LinkedIn or application URL)
            
        Returns:
            True if job already exists, False otherwise
        """
        try:
            # Get existing qualification results
            existing_results = self.get_qualification_results()
            
            if not existing_results:
                return False
            
            # Normalize the input URL
            input_url = self._normalize_linkedin_url(job_url) if job_url else ""
            
            if not input_url:
                logging.warning(f"No URL provided for job '{job_title}' at '{company}' - cannot check for duplicates")
                return False
            
            # Check for URL match only
            for result in existing_results:
                existing_url = self._normalize_linkedin_url(result.get('Job URL', ''))
                
                if existing_url and input_url == existing_url:
                    logging.info(f"Duplicate found by normalized URL: {input_url}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking for duplicate job: {e}")
            return False  # If we can't check, assume it's not a duplicate
    
    def is_job_duplicate_by_application_url(self, application_url: str) -> bool:
        """
        Check if a job with the same application URL already exists.
        
        Args:
            application_url: Application URL to check
            
        Returns:
            True if job already exists, False otherwise
        """
        if not application_url:
            return False
        
        try:
            existing_results = self.get_qualification_results()
            
            if not existing_results:
                return False
            
            # Normalize the application URL
            normalized_app_url = application_url.strip().lower()
            
            for result in existing_results:
                # Check if there's an application URL stored in the job data
                # This would need to be added to the QualificationResult model in the future
                existing_app_url = result.get('Application URL', '').strip().lower()
                
                if existing_app_url and normalized_app_url == existing_app_url:
                    logging.info(f"Duplicate found by application URL: {normalized_app_url}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking for duplicate by application URL: {e}")
            return False
    
    def write_qualification_result(self, qualification_result: QualificationResult) -> bool:
        """
        Write a qualification result to Google Sheets.
        
        Args:
            qualification_result: QualificationResult object to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check for duplicate before writing
            if self.is_job_duplicate(qualification_result.job_title, qualification_result.company, qualification_result.job_url):
                logging.info(f"Skipping duplicate job: {qualification_result.job_title} at {qualification_result.company}")
                return False
            
            # Convert to row format
            row_data = self._qualification_result_to_row(qualification_result)
            
            # Append to worksheet
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.qualified_jobs_worksheet}!A:Z",  # Google Sheets API handles spaces automatically
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            
            logging.info(f"Successfully wrote qualification result for {qualification_result.job_title}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to write qualification result: {e}")
            return False
    
    def write_job_listing(self, job_listing: JobListing) -> bool:
        """
        Write a job listing to Google Sheets.
        
        Args:
            job_listing: The job listing to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            row_data = self._job_listing_to_row(job_listing)
            
            # Append to the job listings worksheet
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.job_listings_worksheet}!A:A",  # Google Sheets API handles spaces automatically
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [row_data]}
            ).execute()
            
            logging.info(f"Job listing written: {job_listing.title}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to write job listing: {e}")
            return False
    
    def update_qualification_decision(self, job_id: str, user_decision: UserDecision, notes: str = "") -> bool:
        """
        Update user decision for a qualification result.
        
        Args:
            job_id: The job ID to update
            user_decision: The user's decision
            notes: Optional notes from the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all qualification results to find the row
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.qualified_jobs_worksheet}!A:Z"  # Google Sheets API handles spaces automatically
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logging.warning("No qualification results found in sheet")
                return False
            
            # Find the row with matching job ID (assuming job ID is in column A)
            row_index = None
            for i, row in enumerate(values[1:], start=2):  # Skip header row
                if row and row[0] == job_id:
                    row_index = i
                    break
            
            if row_index is None:
                logging.warning(f"Job ID {job_id} not found in sheet")
                return False
            
            # Update the user decision and notes
            range_name = f"{self.qualified_jobs_worksheet}!J{row_index}:K{row_index}"  # User Decision and User Notes columns
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [[user_decision.value, notes]]}
            ).execute()
            
            logging.info(f"Updated user decision for job {job_id}: {user_decision.value}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to update qualification decision: {e}")
            return False
    
    def get_qualification_results(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get qualification results from Google Sheets.
        
        Args:
            limit: Maximum number of results to return (optional)
            
        Returns:
            List of qualification result dictionaries
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.qualified_jobs_worksheet}!A:Z"  # Google Sheets API handles spaces automatically
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            # Convert to list of dictionaries
            headers = values[0]
            results = []
            
            for row in values[1:]:  # Skip header row
                if limit and len(results) >= limit:
                    break
                
                # Pad row to match headers length
                row_data = row + [''] * (len(headers) - len(row))
                result_dict = dict(zip(headers, row_data))
                results.append(result_dict)
            
            return results
            
        except Exception as e:
            logging.error(f"Failed to get qualification results: {e}")
            return []
    
    def _qualification_result_to_row(self, qualification_result: QualificationResult) -> List[str]:
        """Convert a qualification result to a row for Google Sheets."""
        return [
            qualification_result.job_title,
            qualification_result.company,
            qualification_result.job_url,
            str(qualification_result.qualification_score),
            qualification_result.ai_reasoning,
            qualification_result.required_experience,
            qualification_result.education_requirements,
            ', '.join(qualification_result.key_skills_mentioned),
            qualification_result.analysis_date.strftime('%Y-%m-%d %H:%M:%S'),
            qualification_result.user_decision.value,
            qualification_result.user_notes,
            qualification_result.manual_override_reason,
            qualification_result.ai_model_used,
            str(qualification_result.analysis_duration) if qualification_result.analysis_duration else '',
            qualification_result.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            qualification_result.last_updated.strftime('%Y-%m-%d %H:%M:%S')
        ]
    
    def _job_listing_to_row(self, job_listing: JobListing) -> List[str]:
        """Convert a job listing to a row for Google Sheets."""
        return [
            job_listing.scraped_date.strftime('%Y-%m-%d %H:%M:%S'),
            job_listing.title,
            job_listing.company,
            job_listing.location,
            job_listing.job_url,
            job_listing.job_site,
            job_listing.description,
            ', '.join(job_listing.requirements),
            ', '.join(job_listing.responsibilities),
            ', '.join(job_listing.benefits),
            str(job_listing.salary_min) if job_listing.salary_min else '',
            str(job_listing.salary_max) if job_listing.salary_max else '',
            job_listing.salary_currency,
            job_listing.job_type.value if job_listing.job_type else '',
            job_listing.experience_level.value if job_listing.experience_level else '',
            job_listing.remote_type.value if job_listing.remote_type else '',
            job_listing.application_url or '',
            job_listing.application_deadline.strftime('%Y-%m-%d') if job_listing.application_deadline else '',
            ', '.join(job_listing.application_requirements),
            job_listing.posted_date.strftime('%Y-%m-%d') if job_listing.posted_date else '',
            'Yes' if job_listing.is_duplicate else 'No',
            job_listing.duplicate_of or '',
            job_listing.notes
        ]
    
    def test_connection(self) -> bool:
        """
        Test the connection to Google Sheets.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to read the first row of the qualified jobs worksheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.qualified_jobs_worksheet}!A1:Z1"  # Google Sheets API handles spaces automatically
            ).execute()
            
            logging.info("Google Sheets connection test successful")
            return True
            
        except Exception as e:
            logging.error(f"Google Sheets connection test failed: {e}")
            return False 