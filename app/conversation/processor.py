"""
Processor for extracting information from conversation history
"""

import re
import logging
from typing import List, Dict, Any, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConversationProcessor:
    """Processor for extracting appointment information from conversations"""
    
    def __init__(self):
        """Initialize the conversation processor"""
        # Patterns for extracting appointment data
        self.patterns = {
            'name': [
                r'\bPatient Name:\s*(.*)',
                r'\bname is\s+([^.,]+)',
                r'\bmy name is\s+([^.,]+)',
                r'\bcall me\s+([^.,]+)'
            ],
            'consultation_type': [
                r'\bConsultation Type:\s*(.*)',
                r'\bspecialty(?:\s+is|\s+needed|\s+required)?:\s*([^.,]+)',
                r'\b(?:I need|I want|I would like|I require|need) (?:a|an)?\s+([^.,]+)(?:\s+consultation|\s+appointment)',
                r'\bsee (?:a|an)\s+([^.,]+)(?:\s+doctor|\s+specialist)',
                r'(?:General Medicine|Cardiology|Orthopedics|Pediatrics|Neurology|Dermatology|Ophthalmology)'
            ],
            'reason': [
                r'\bReason for Visit:\s*(.*)',
                r'\bthe reason is\s+([^.]+)',
                r'\bvisit reason(?:\s+is)?:\s*([^.]+)',
                r'\bvisiting for\s+([^.]+)',
                r'\bI have (?:a|an)\s+([^.]+)',
                r'\bI am having\s+([^.]+)',
                r'\bI\'m having\s+([^.]+)',
                r'\bsuffering from\s+([^.]+)'
            ],
            'date': [
                r'\bPreferred Date:\s*(.*)',
                r'\bdate(?:\s+is|\s+would be)?\s*:\s*([^.,]+)',
                r'\b(?:on|for)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)',
                r'\b(?:on|for)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'\b(?:next|this)\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',
                r'\b(tomorrow|today|day after tomorrow)',
                r'\b(in \d+ days)'
            ],
            'time': [
                r'\bPreferred Time:\s*(.*)',
                r'\btime(?:\s+is|\s+would be)?\s*:\s*([^.,]+)',
                r'\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))',
                r'\bat\s+(\d{1,2}(?::\d{2})?)'
            ],
            'phone': [
                r'\bPhone Number:\s*(.*)',
                r'\bphone(?:\s+is|\s+number is)?\s*:\s*([^.,]+)',
                r'\bcall me at\s+([^.,]+)',
                r'\breached at\s+([^.,]+)',
                r'\bmy number is\s+([^.,]+)',
                r'\b(\+?1?\s*\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})'
            ],
            'email': [
                r'\bEmail Address:\s*(.*)',
                r'\bemail(?:\s+is|address is)?\s*:\s*([^.,]+)',
                r'\bemailing\s+([^.,]+)',
                r'\bcontact me at\s+([^.,]+\@[^.,]+)',
                r'\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
            ]
        }
    
    def extract_appointment_data(self, conversation: List[str]) -> Dict[str, str]:
        """
        Extract appointment data from the conversation
        
        Args:
            conversation: List of conversation messages
        
        Returns:
            Dictionary with extracted appointment data
        """
        appointment_data = {}
        
        # Check for formatted appointment data first
        appointment_info_pattern = re.compile(
            r'Patient Name:\s*(.*?)\s*\n'
            r'Consultation Type:\s*(.*?)\s*\n'
            r'Reason for Visit:\s*(.*?)\s*\n'
            r'Preferred Date:\s*(.*?)\s*\n'
            r'Preferred Time:\s*(.*?)\s*\n'
            r'Phone Number:\s*(.*?)\s*\n'
            r'Email Address:\s*(.*?)(?:\s*\n|$)',
            re.DOTALL
        )
        
        for message in conversation:
            match = appointment_info_pattern.search(message)
            if match:
                appointment_data['name'] = match.group(1).strip()
                appointment_data['consultation_type'] = match.group(2).strip()
                appointment_data['reason'] = match.group(3).strip()
                appointment_data['date'] = match.group(4).strip()
                appointment_data['time'] = match.group(5).strip()
                appointment_data['phone'] = match.group(6).strip()
                appointment_data['email'] = match.group(7).strip()
                return appointment_data
        
        # If formatted info not found, extract piece by piece
        full_text = ' '.join(conversation)
        
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    # Use the last match (most recent)
                    extracted_value = matches[-1].strip()
                    
                    # Special handling for consultation type
                    if field == 'consultation_type':
                        # Map to one of the valid specialties
                        specialties = [
                            'General Medicine', 'Cardiology', 'Orthopedics',
                            'Pediatrics', 'Neurology', 'Dermatology', 'Ophthalmology'
                        ]
                        
                        for specialty in specialties:
                            if specialty.lower() in extracted_value.lower():
                                extracted_value = specialty
                                break
                    
                    appointment_data[field] = extracted_value
                    break
        
        return appointment_data
    
    def extract_information(self, conversation: List[str], pattern: str) -> Optional[str]:
        """
        Extract information from conversation using a pattern
        
        Args:
            conversation: List of conversation messages
            pattern: Regex pattern to match
        
        Returns:
            Extracted information or None if not found
        """
        for line in conversation:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def has_time_availability_response(self, message: str) -> bool:
        """
        Check if a message contains a time availability response
        
        Args:
            message: Message to check
        
        Returns:
            True if the message is about time availability, False otherwise
        """
        patterns = [
            r'not available',
            r'no availability',
            r'next available slots',
            r'alternative times?',
            r'choose (?:a|another) time'
        ]
        
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        
        return False
    
    def extract_alternative_times(self, message: str) -> List[str]:
        """
        Extract alternative time slots from a message
        
        Args:
            message: Message containing time slots
        
        Returns:
            List of time slot strings
        """
        # Look for patterns like "available slots: 10:00 AM, 11:30 AM, 2:00 PM"
        time_pattern = r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))'
        
        matches = re.findall(time_pattern, message)
        if matches:
            return [time.strip() for time in matches]
        
        return []