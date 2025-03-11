"""
Models for appointment data
"""

import uuid
import datetime
from typing import Dict, Any, Optional

class Appointment:
    """Model for an appointment"""
    
    def __init__(
        self,
        patient_name: str,
        consultation_type: str,
        reason: str,
        date: str,
        time: str,
        phone: str,
        email: str,
        status: str = "Pending",
        calendly_event_id: Optional[str] = None,
        id: Optional[str] = None
    ):
        """
        Initialize an appointment
        
        Args:
            patient_name: Patient's name
            consultation_type: Type of consultation
            reason: Reason for visit
            date: Appointment date
            time: Appointment time
            phone: Patient's phone number
            email: Patient's email address
            status: Appointment status (default: "Pending")
            calendly_event_id: Calendly event ID (default: None)
            id: Appointment ID (default: auto-generated)
        """
        self.id = id or f"appt-{uuid.uuid4().hex[:8]}"
        self.patient_name = patient_name
        self.consultation_type = consultation_type
        self.reason = reason
        self.date = date
        self.time = time
        self.phone = phone
        self.email = email
        self.status = status
        self.calendly_event_id = calendly_event_id
        self.created_at = datetime.datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert appointment to dictionary
        
        Returns:
            Dictionary representation of appointment
        """
        return {
            "id": self.id,
            "patient_name": self.patient_name,
            "consultation_type": self.consultation_type,
            "reason": self.reason,
            "date": self.date,
            "time": self.time,
            "phone": self.phone,
            "email": self.email,
            "status": self.status,
            "calendly_event_id": self.calendly_event_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Appointment':
        """
        Create appointment from dictionary
        
        Args:
            data: Dictionary with appointment data
        
        Returns:
            Appointment instance
        """
        return cls(
            id=data.get("id"),
            patient_name=data.get("patient_name", ""),
            consultation_type=data.get("consultation_type", ""),
            reason=data.get("reason", ""),
            date=data.get("date", ""),
            time=data.get("time", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            status=data.get("status", "Pending"),
            calendly_event_id=data.get("calendly_event_id")
        )