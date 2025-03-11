"""
Email service for sending appointment confirmations and reminders
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Any, Optional

from config.settings import EMAIL_TEMPLATES

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending appointment confirmations and reminders"""
    
    def __init__(self):
        """Initialize the email service"""
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
        self.username = os.getenv('EMAIL_USERNAME')
        self.password = os.getenv('EMAIL_PASSWORD')
        self.sender_name = os.getenv('EMAIL_SENDER_NAME', 'Hospital Appointment System')
    
    def _create_message(self, recipient: str, subject: str, body: str, is_html: bool = True) -> MIMEMultipart:
        """
        Create an email message
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML (default: True)
        
        Returns:
            Email message object
        """
        msg = MIMEMultipart()
        msg['From'] = f"{self.sender_name} <{self.username}>"
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Attach the body
        content_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, content_type))
        
        return msg
    
    def _load_template(self, template_path: str) -> Optional[str]:
        """
        Load an email template from file
        
        Args:
            template_path: Path to the template file
        
        Returns:
            Template content or None if loading fails
        """
        try:
            template_path = Path(template_path)
            if not template_path.exists():
                logger.error(f"Template file not found: {template_path}")
                return None
            
            with open(template_path, 'r') as file:
                return file.read()
        
        except Exception as e:
            logger.error(f"Error loading email template: {str(e)}")
            return None
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with context variables
        
        Args:
            template: Template string
            context: Dictionary of context variables
        
        Returns:
            Rendered template
        """
        # Simple template rendering - replace placeholders with values
        rendered = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def send_email(self, recipient: str, subject: str, body: str, is_html: bool = True) -> bool:
        """
        Send an email
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether the body is HTML (default: True)
        
        Returns:
            Success status
        """
        try:
            # Create the message
            msg = self._create_message(recipient, subject, body, is_html)
            
            # Connect to the SMTP server and send the email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False
    
    def send_confirmation_email(self, appointment_data: Dict[str, Any]) -> bool:
        """
        Send a confirmation email for an appointment
        
        Args:
            appointment_data: Dictionary with appointment details
        
        Returns:
            Success status
        """
        try:
            # Get the recipient email
            recipient = appointment_data.get('email')
            if not recipient:
                logger.error("No recipient email provided for confirmation email")
                return False
            
            # Get the template configuration
            template_config = EMAIL_TEMPLATES.get('confirmation')
            if not template_config:
                logger.error("Confirmation email template configuration not found")
                return False
            
            # Load the template
            template_path = template_config.get('template_path')
            template = self._load_template(template_path)
            
            if not template:
                # Fallback to a basic template if the template file is not found
                template = """
                <html>
                <body>
                    <h2>Hospital Appointment Confirmation</h2>
                    <p>Dear {{name}},</p>
                    <p>Your appointment has been confirmed with the following details:</p>
                    <ul>
                        <li><strong>Consultation Type:</strong> {{consultation_type}}</li>
                        <li><strong>Reason for Visit:</strong> {{reason}}</li>
                        <li><strong>Date:</strong> {{date}}</li>
                        <li><strong>Time:</strong> {{time}}</li>
                        <li><strong>Location:</strong> Hospital Clinic, Medical Center</li>
                    </ul>
                    <p>Please arrive 15 minutes before your scheduled appointment time.</p>
                    <p>If you need to reschedule or cancel your appointment, please contact us at least 24 hours in advance.</p>
                    <p>Thank you,<br>Hospital Clinic Team</p>
                </body>
                </html>
                """
            
            # Render the template
            rendered_body = self._render_template(template, appointment_data)
            
            # Send the email
            subject = template_config.get('subject', 'Hospital Appointment Confirmation')
            return self.send_email(recipient, subject, rendered_body, is_html=True)
        
        except Exception as e:
            logger.error(f"Error sending confirmation email: {str(e)}")
            return False
    
    def send_reminder_email(self, appointment_data: Dict[str, Any]) -> bool:
        """
        Send a reminder email for an upcoming appointment
        
        Args:
            appointment_data: Dictionary with appointment details
        
        Returns:
            Success status
        """
        try:
            # Get the recipient email
            recipient = appointment_data.get('email')
            if not recipient:
                logger.error("No recipient email provided for reminder email")
                return False
            
            # Get the template configuration
            template_config = EMAIL_TEMPLATES.get('reminder')
            if not template_config:
                logger.error("Reminder email template configuration not found")
                return False
            
            # Load the template
            template_path = template_config.get('template_path')
            template = self._load_template(template_path)
            
            if not template:
                # Fallback to a basic template if the template file is not found
                template = """
                <html>
                <body>
                    <h2>Reminder: Your Upcoming Hospital Appointment</h2>
                    <p>Dear {{name}},</p>
                    <p>This is a friendly reminder about your upcoming appointment:</p>
                    <ul>
                        <li><strong>Consultation Type:</strong> {{consultation_type}}</li>
                        <li><strong>Date:</strong> {{date}}</li>
                        <li><strong>Time:</strong> {{time}}</li>
                        <li><strong>Location:</strong> Hospital Clinic, Medical Center</li>
                    </ul>
                    <p>Please arrive 15 minutes before your scheduled appointment time.</p>
                    <p>If you need to reschedule or cancel your appointment, please contact us as soon as possible.</p>
                    <p>Thank you,<br>Hospital Clinic Team</p>
                </body>
                </html>
                """
            
            # Render the template
            rendered_body = self._render_template(template, appointment_data)
            
            # Send the email
            subject = template_config.get('subject', 'Reminder: Your Upcoming Hospital Appointment')
            return self.send_email(recipient, subject, rendered_body, is_html=True)
        
        except Exception as e:
            logger.error(f"Error sending reminder email: {str(e)}")
            return False