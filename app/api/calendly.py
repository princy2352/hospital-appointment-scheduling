"""
Calendly API integration for the Hospital Appointment System
"""

import os
import logging
import requests
import datetime
from typing import Dict, List, Any, Optional, Tuple

from config.settings import CALENDLY_BASE_URL, get_calendly_headers, SPECIALTY_EVENT_TYPES

logger = logging.getLogger(__name__)

class CalendlyAPI:
    """Calendly API client for managing appointments"""
    
    def __init__(self):
        """Initialize the Calendly API client"""
        self.base_url = CALENDLY_BASE_URL
        self.headers = get_calendly_headers()
        self.user_uri = os.getenv('CALENDLY_USER_URI')
    
    def get_event_types(self) -> List[Dict[str, Any]]:
        """
        Get all available event types from Calendly
        
        Returns:
            List of event types
        """
        try:
            url = f"{self.base_url}/event_types"
            params = {
                "user": self.user_uri,
                "active": True
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting event types: {str(e)}")
            return []
    
    def get_specialty_event_type(self, specialty: str) -> str:
        """
        Get the event type ID for a specific medical specialty
        
        Args:
            specialty: Medical specialty name
        
        Returns:
            Event type ID
        """
        # Default to general medicine if specialty is not found
        return SPECIALTY_EVENT_TYPES.get(specialty, SPECIALTY_EVENT_TYPES["General Medicine"])
    
    def get_available_times(self, event_type_id: str, date_str: str) -> List[Dict[str, Any]]:
        """
        Get available times from Calendly for a specific event type on a specific date
        
        Args:
            event_type_id: The Calendly event type ID
            date_str: Date string in YYYY-MM-DD format
        
        Returns:
            List of available time slots
        """
        try:
            # Convert the date string to datetime
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
            # Define the start and end times for the query (full day)
            start_time = date_obj.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
            end_time = date_obj.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
            
            # Query Calendly API for available times
            url = f"{self.base_url}/event_type_available_times"
            params = {
                "event_type": f"{self.base_url}/event_types/{event_type_id}",
                "start_time": start_time,
                "end_time": end_time
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("data", [])
        
        except Exception as e:
            logger.error(f"Error getting available times: {str(e)}")
            return []
    
    def check_time_availability(self, specialty: str, date_str: str, time_str: str) -> Tuple[bool, List[str]]:
        """
        Check if a specific time is available for a specialty
        
        Args:
            specialty: Medical specialty
            date_str: Date string in YYYY-MM-DD format
            time_str: Time string in various formats (will be parsed)
        
        Returns:
            Tuple of (is_available, alternative_times)
        """
        try:
            # Parse the time string
            time_formats = [
                "%H:%M",         # 13:00
                "%I:%M %p",      # 1:00 PM
                "%I %p",         # 1 PM
                "%I:%M%p",       # 1:00PM
                "%I%p"           # 1PM
            ]
            
            parsed_time = None
            for fmt in time_formats:
                try:
                    parsed_time = datetime.datetime.strptime(time_str, fmt).time()
                    break
                except ValueError:
                    continue
            
            if not parsed_time:
                logger.warning(f"Could not parse time string: {time_str}")
                return False, []
            
            # Get event type ID for the specialty
            event_type_id = self.get_specialty_event_type(specialty)
            
            # Get available times for the date
            available_times = self.get_available_times(event_type_id, date_str)
            
            # Convert parsed time to ISO format for comparison
            parsed_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            requested_datetime = datetime.datetime.combine(parsed_date, parsed_time)
            requested_iso = requested_datetime.isoformat() + 'Z'
            
            # Check if requested time is available
            is_available = any(slot['start_time'] == requested_iso for slot in available_times)
            
            # Get alternative times if requested time is not available
            alternative_times = []
            if not is_available and available_times:
                for slot in available_times[:3]:  # Get up to 3 alternatives
                    slot_time = datetime.datetime.fromisoformat(slot['start_time'].replace('Z', '+00:00'))
                    alternative_times.append(slot_time.strftime("%I:%M %p"))
            
            return is_available, alternative_times
        
        except Exception as e:
            logger.error(f"Error checking time availability: {str(e)}")
            return False, []
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new event in Calendly
        
        Args:
            event_data: Dictionary with event details
        
        Returns:
            Dictionary with event result (success and data/error)
        """
        try:
            # Get event type ID
            event_type_id = self.get_specialty_event_type(event_data.get('consultation_type', 'General Medicine'))
            
            # Format the date and time
            date_str = event_data.get('date')
            time_str = event_data.get('time')
            
            # Parse the date and time
            date_formats = [
                "%Y-%m-%d",       # 2025-03-10
                "%B %d, %Y",      # March 10, 2025
                "%b %d, %Y",      # Mar 10, 2025
                "%d/%m/%Y",       # 10/03/2025
                "%m/%d/%Y",       # 03/10/2025
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.datetime.strptime(date_str, fmt).date()
                    break
                except (ValueError, TypeError):
                    continue
            
            if not parsed_date:
                return {"success": False, "error": f"Could not parse date string: {date_str}"}
            
            # Parse time
            time_formats = [
                "%H:%M",         # 13:00
                "%I:%M %p",      # 1:00 PM
                "%I %p",         # 1 PM
                "%I:%M%p",       # 1:00PM
                "%I%p"           # 1PM
            ]
            
            parsed_time = None
            for fmt in time_formats:
                try:
                    parsed_time = datetime.datetime.strptime(time_str, fmt).time()
                    break
                except (ValueError, TypeError):
                    continue
            
            if not parsed_time:
                return {"success": False, "error": f"Could not parse time string: {time_str}"}
            
            # Combine date and time
            start_datetime = datetime.datetime.combine(parsed_date, parsed_time)
            start_iso = start_datetime.isoformat() + 'Z'
            
            # Create the event in Calendly
            url = f"{self.base_url}/scheduled_events"
            payload = {
                "event_type_uuid": event_type_id,
                "start_time": start_iso,
                "invitee": {
                    "name": event_data.get('name', ''),
                    "email": event_data.get('email', ''),
                    "phone_number": event_data.get('phone', '')
                },
                "custom_questions": [
                    {
                        "question": "Reason for Visit",
                        "answer": event_data.get('reason', 'Medical consultation')
                    },
                    {
                        "question": "Consultation Type",
                        "answer": event_data.get('consultation_type', 'General Medicine')
                    }
                ]
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            return {"success": True, "data": data.get("data", {})}
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating Calendly event: {str(e)}")
            return {"success": False, "error": f"HTTP error: {str(e)}"}
        
        except Exception as e:
            logger.error(f"Error creating Calendly event: {str(e)}")
            return {"success": False, "error": str(e)}