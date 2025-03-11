"""
Tools for the appointment scheduling agent
"""

import logging
import json
from typing import Dict, Any, Callable

from langchain_core.tools import StructuredTool

from app.utils.logger import get_logger
from app.api.calendly import CalendlyAPI
from app.api.email_service import EmailService

logger = get_logger(__name__)

def create_scheduling_tool(calendly_api: CalendlyAPI, email_service: EmailService) -> StructuredTool:
    """
    Create a structured tool for scheduling appointments
    
    Args:
        calendly_api: CalendlyAPI instance
        email_service: EmailService instance
    
    Returns:
        StructuredTool for scheduling appointments
    """
    def schedule_appointment(appointment_info: str) -> str:
        """
        Schedule a hospital appointment using Calendly with the provided information.
        
        Args:
            appointment_info: String containing appointment details in the format:
                Patient Name: <name>
                Consultation Type: <type>
                Reason for Visit: <reason>
                Preferred Date: <date>
                Preferred Time: <time>
                Phone Number: <phone>
                Email Address: <email>
        
        Returns:
            Confirmation message or error
        """
        try:
            # Parse the appointment info
            import re
            
            # Extract fields using regular expressions
            name_match = re.search(r'Patient Name:\s*(.*?)$', appointment_info, re.MULTILINE)
            consultation_match = re.search(r'Consultation Type:\s*(.*?)$', appointment_info, re.MULTILINE)
            reason_match = re.search(r'Reason for Visit:\s*(.*?)$', appointment_info, re.MULTILINE)
            date_match = re.search(r'Preferred Date:\s*(.*?)$', appointment_info, re.MULTILINE)
            time_match = re.search(r'Preferred Time:\s*(.*?)$', appointment_info, re.MULTILINE)
            phone_match = re.search(r'Phone Number:\s*(.*?)$', appointment_info, re.MULTILINE)
            email_match = re.search(r'Email Address:\s*(.*?)$', appointment_info, re.MULTILINE)
            
            # Extract the information
            name = name_match.group(1) if name_match else ""
            consultation = consultation_match.group(1) if consultation_match else ""
            reason = reason_match.group(1) if reason_match else ""
            date_str = date_match.group(1) if date_match else ""
            time_str = time_match.group(1) if time_match else ""
            phone = phone_match.group(1) if phone_match else ""
            email = email_match.group(1) if email_match else ""
            
            # Validate required fields
            if not all([name, consultation, reason, date_str, time_str, phone, email]):
                missing_fields = []
                if not name: missing_fields.append("Patient Name")
                if not consultation: missing_fields.append("Consultation Type")
                if not reason: missing_fields.append("Reason for Visit")
                if not date_str: missing_fields.append("Preferred Date")
                if not time_str: missing_fields.append("Preferred Time")
                if not phone: missing_fields.append("Phone Number")
                if not email: missing_fields.append("Email Address")
                
                return f"Missing required information: {', '.join(missing_fields)}. Please provide all required details."
            
            # Check if the time is available
            is_available, alternative_times = calendly_api.check_time_availability(
                specialty=consultation,
                date_str=date_str,
                time_str=time_str
            )
            
            if not is_available:
                # Return alternative times if available
                if alternative_times:
                    times_str = ", ".join(alternative_times)
                    return f"The requested time is not available. Here are the next available slots on {date_str}: {times_str}. Please choose a new time."
                else:
                    return f"No availability on {date_str}. Please choose another date."
            
            # Create the appointment in Calendly
            event_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "consultation_type": consultation,
                "reason": reason,
                "date": date_str,
                "time": time_str
            }
            
            event_result = calendly_api.create_event(event_data)
            
            if not event_result["success"]:
                return f"There was an error scheduling your appointment: {event_result.get('error', 'Unknown error')}. Please try again later."
            
            # Send confirmation email
            email_result = email_service.send_confirmation_email(event_data)
            
            if not email_result:
                logger.warning(f"Failed to send confirmation email to {email}")
            
            # Return success message
            confirmation_id = event_result["data"].get("id", f"APPT-{hash(name + date_str + time_str) % 100000}")
            
            return (
                f"Your appointment for {consultation} has been confirmed for {date_str} at {time_str}. "
                f"Your confirmation number is {confirmation_id}. "
                f"A confirmation email has been sent to {email}. "
                f"Please arrive 15 minutes before your scheduled time."
            )
        
        except Exception as e:
            error_msg = f"Error scheduling appointment: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    # Create and return the tool
    return StructuredTool.from_function(
        func=schedule_appointment,
        name="schedule_hospital_appointment",
        description="Schedule a hospital appointment using Calendly with the provided patient information"
    )