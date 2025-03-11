"""
Configuration settings for the Hospital Appointment System
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Required environment variables
REQUIRED_ENV_VARS = [
    'OPENAI_API_KEY',
    'CALENDLY_API_KEY',
    'CALENDLY_USER_URI',
    'EMAIL_USERNAME',
    'EMAIL_PASSWORD',
    'EMAIL_SMTP_SERVER',
    'EMAIL_SMTP_PORT',
]

# Optional environment variables with defaults
OPTIONAL_ENV_VARS = {
    'OPENAI_MODEL': 'gpt-3.5-turbo',
    'TEMPERATURE': '0.7',
    'DATA_DIR': os.path.join(BASE_DIR, 'data'),
    'LOG_LEVEL': 'INFO',
}

# Calendly API configuration
CALENDLY_BASE_URL = "https://api.calendly.com"

# Specialty to event type mapping
SPECIALTY_EVENT_TYPES = {
    # Replace these with actual event type IDs from your Calendly account
    'General Medicine': 'your_general_medicine_event_type_id',
    'Cardiology': 'your_cardiology_event_type_id',
    'Orthopedics': 'your_orthopedics_event_type_id',
    'Pediatrics': 'your_pediatrics_event_type_id',
    'Neurology': 'your_neurology_event_type_id',
    'Dermatology': 'your_dermatology_event_type_id',
    'Ophthalmology': 'your_ophthalmology_event_type_id',
}

# Clinic operating hours
CLINIC_HOURS = {
    'Monday': {'start': '09:00', 'end': '17:00'},
    'Tuesday': {'start': '09:00', 'end': '17:00'},
    'Wednesday': {'start': '09:00', 'end': '17:00'},
    'Thursday': {'start': '09:00', 'end': '17:00'},
    'Friday': {'start': '09:00', 'end': '17:00'},
    'Saturday': {'start': '09:00', 'end': '12:00'},
    'Sunday': {'start': None, 'end': None},  # Closed
}

# Email templates
EMAIL_TEMPLATES = {
    'confirmation': {
        'subject': 'Hospital Appointment Confirmation',
        'template_path': os.path.join(BASE_DIR, 'app', 'templates', 'confirmation_email.html'),
    },
    'reminder': {
        'subject': 'Reminder: Your Upcoming Hospital Appointment',
        'template_path': os.path.join(BASE_DIR, 'app', 'templates', 'reminder_email.html'),
    },
}

def load_environment_variables():
    """Load environment variables from .env file"""
    # Load .env file
    dotenv_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    
    # Check for required environment variables
    missing_vars = [var for var in REQUIRED_ENV_VARS if os.getenv(var) is None]
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Set defaults for optional environment variables
    for var, default in OPTIONAL_ENV_VARS.items():
        if os.getenv(var) is None:
            os.environ[var] = default
    
    # Create necessary directories
    data_dir = os.getenv('DATA_DIR')
    appointments_dir = os.path.join(data_dir, 'appointments')
    logs_dir = os.path.join(BASE_DIR, 'logs')
    
    for directory in [data_dir, appointments_dir, logs_dir]:
        os.makedirs(directory, exist_ok=True)
    
    return True

def get_calendly_headers():
    """Get headers for Calendly API requests"""
    return {
        "Authorization": f"Bearer {os.getenv('CALENDLY_API_KEY')}",
        "Content-Type": "application/json"
    }