# Hospital Appointment Scheduling System

A conversational AI system for scheduling hospital appointments with Calendly integration.

## Overview

This Hospital Appointment Scheduling System is designed to help healthcare facilities streamline their appointment booking process. The system uses a conversational AI approach to collect patient information and integrates with Calendly to manage appointment scheduling and availability.

## Features

- **Natural language conversation** to collect patient appointment information
- **Calendly integration** for real-time appointment scheduling and availability checking
- **Email confirmations** sent automatically to patients
- **Support for multiple medical specialties**
- **Appointment data storage** for backup and record-keeping
- **Time availability checking** with suggestions for alternative times
- **Robust date and time parsing** to handle various input formats

## System Requirements

- Python 3.8+
- Calendly Professional account with API access
- Email account for sending confirmations

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/princy2352/hospital-appointment-system.git
   cd hospital-appointment-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys and credentials:
     ```
     OPENAI_API_KEY=your_openai_api_key
     CALENDLY_API_KEY=your_calendly_api_key
     CALENDLY_USER_URI=your_calendly_user_uri
     EMAIL_USERNAME=your_email_username
     EMAIL_PASSWORD=your_email_password
     EMAIL_SMTP_SERVER=smtp.your-email-provider.com
     EMAIL_SMTP_PORT=587
     ```

4. Configure Calendly event types:
   - Update the `SPECIALTY_EVENT_TYPES` mapping in `config/settings.py` with your actual Calendly event type IDs.

## Usage

1. Start the application:
   ```
   python main.py
   ```

2. Interact with the system:
   - The system will guide the user through the appointment scheduling process
   - It will collect all necessary patient information
   - It will check appointment availability in real-time
   - It will schedule the appointment and send a confirmation email

## Project Structure

```
hospital_appointment_system/
├── README.md                       # Project documentation
├── requirements.txt                # Project dependencies
├── .env.example                    # Example environment variables
├── main.py                         # Application entry point
├── config/                         # Configuration settings
├── app/
│   ├── agent/                      # LLM agent components
│   ├── api/                        # External API integrations
│   ├── conversation/               # Conversation management
│   ├── models/                     # Data models
│   └── utils/                      # Utility functions
├── data/                           # Local data storage
└── logs/                           # Application logs
```

## Customization for Hospitals

This system can be customized for individual hospital needs:

1. **Medical specialties**: Update the list of available specialties in the system prompt
2. **Clinic hours**: Modify the clinic operating hours in the settings
3. **Email templates**: Customize the email confirmation templates
4. **Integration with hospital systems**: The code structure allows for easy integration with existing hospital management systems

