"""
Conversation engine for managing the appointment scheduling flow
"""

import os
import logging
import datetime
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate

from app.agent.prompts import get_system_prompt
from app.agent.tools import create_scheduling_tool
from app.conversation.processor import ConversationProcessor
from app.api.calendly import CalendlyAPI
from app.api.email_service import EmailService
from app.models.appointment import Appointment
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ConversationEngine:
    """Engine for managing the conversation flow for appointment scheduling"""
    
    def __init__(self):
        """Initialize the conversation engine"""
        self.llm = ChatOpenAI(
            model=os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
            temperature=float(os.getenv('TEMPERATURE', 0.7))
        )
        
        self.calendly_api = CalendlyAPI()
        self.email_service = EmailService()
        self.processor = ConversationProcessor()
        
        # Initialize the conversation history
        self.messages = [SystemMessage(content=get_system_prompt())]
        self.conversation_history = []
        
        # Initialize the agent executor
        self._setup_agent()
    
    def _setup_agent(self):
        """Set up the LangChain agent for appointment scheduling"""
        # Create the scheduling tool
        scheduling_tool = create_scheduling_tool(
            calendly_api=self.calendly_api,
            email_service=self.email_service
        )
        
        # Agent template
        agent_template = """
        You are an assistant tasked with scheduling hospital appointments.
        Use the following tools to schedule an appointment based on the information provided:

        {tools}

        Use the following format:
        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question

        Begin!

        Question: {input}
        {agent_scratchpad}
        """
        
        # Create agent prompt
        agent_prompt = ChatPromptTemplate.from_template(agent_template)
        
        # Create agent
        agent = create_react_agent(self.llm, [scheduling_tool], agent_prompt)
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=[scheduling_tool],
            verbose=bool(os.getenv('AGENT_VERBOSE', 'True').lower() == 'true')
        )
    
    def start(self):
        """Start the conversation loop"""
        print("Hospital Clinic Appointment System (Type 'bye' to exit)")
        print("--------------------------------------------------------")
        
        while True:
            # Get user input
            user_input = input("Human: ")
            self.conversation_history.append(f"User: {user_input}")
            
            # Check for exit command
            if user_input.lower() in ['bye', 'exit', 'quit']:
                print("Assistant: Goodbye! Thank you for using our appointment system.")
                break
            
            # Add user message to conversation history
            self.messages.append(HumanMessage(content=user_input))
            
            # Process the conversation and get response
            response = self._process_conversation(user_input)
            
            # Print the response
            print(f"Assistant: {response}")
            self.conversation_history.append(f"Bot: {response}")
            
            # Check if we have all the required information to schedule the appointment
            appointment_data = self.processor.extract_appointment_data(self.conversation_history)
            
            if self._is_appointment_data_complete(appointment_data):
                # Format the appointment data for the agent
                appointment_info = self._format_appointment_info(appointment_data)
                
                print(f"\nAssistant: Processing appointment with the following details:\n{appointment_info}")
                
                # Use agent executor to schedule the appointment
                try:
                    result = self.agent_executor.invoke({
                        "input": f"Schedule this hospital appointment: {appointment_info}"
                    })
                    
                    agent_response = result['output']
                    print(f"Assistant: {agent_response}")
                    self.conversation_history.append(f"Bot: {agent_response}")
                    
                    # Check if the appointment was scheduled successfully
                    if "not available" in agent_response.lower():
                        # Time not available, continue the conversation
                        self.messages.append(HumanMessage(
                            content="I see that time is not available. Let me choose a different time."
                        ))
                        continue
                    
                    # Save the appointment data
                    self._save_appointment(appointment_data, agent_response)
                    
                    # End the conversation if the appointment was scheduled successfully
                    break
                
                except Exception as e:
                    error_msg = f"Error scheduling appointment: {str(e)}"
                    logger.error(error_msg)
                    print(f"Assistant: {error_msg}")
                    self.conversation_history.append(f"Bot: {error_msg}")
                    # Continue the conversation
    
    def _process_conversation(self, user_input: str) -> str:
        """
        Process a user message and generate a response
        
        Args:
            user_input: User's message
        
        Returns:
            Assistant's response
        """
        try:
            # Generate a response using the LLM
            response = self.llm.invoke(self.messages)
            
            # Add the assistant's response to conversation history
            self.messages.append(response)
            
            return response.content
        
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return "I'm sorry, I encountered an error while processing your request. Please try again."
    
    def _is_appointment_data_complete(self, appointment_data: Dict[str, str]) -> bool:
        """
        Check if all required appointment data is available
        
        Args:
            appointment_data: Dictionary with appointment data
        
        Returns:
            True if all required data is available, False otherwise
        """
        required_fields = ['name', 'consultation_type', 'reason', 'date', 'time', 'phone', 'email']
        return all(appointment_data.get(field) for field in required_fields)
    
    def _format_appointment_info(self, appointment_data: Dict[str, str]) -> str:
        """
        Format appointment data for display and agent input
        
        Args:
            appointment_data: Dictionary with appointment data
        
        Returns:
            Formatted appointment information
        """
        return (
            f"Patient Name: {appointment_data.get('name', '')}\n"
            f"Consultation Type: {appointment_data.get('consultation_type', '')}\n"
            f"Reason for Visit: {appointment_data.get('reason', '')}\n"
            f"Preferred Date: {appointment_data.get('date', '')}\n"
            f"Preferred Time: {appointment_data.get('time', '')}\n"
            f"Phone Number: {appointment_data.get('phone', '')}\n"
            f"Email Address: {appointment_data.get('email', '')}\n"
        )
    
    def _save_appointment(self, appointment_data: Dict[str, str], agent_response: str) -> None:
        """
        Save appointment data to a file
        
        Args:
            appointment_data: Dictionary with appointment data
            agent_response: Response from the agent
        """
        try:
            # Create an Appointment object
            appointment = Appointment(
                patient_name=appointment_data.get('name', ''),
                consultation_type=appointment_data.get('consultation_type', ''),
                reason=appointment_data.get('reason', ''),
                date=appointment_data.get('date', ''),
                time=appointment_data.get('time', ''),
                phone=appointment_data.get('phone', ''),
                email=appointment_data.get('email', ''),
                status="Confirmed" if "confirmed" in agent_response.lower() else "Pending",
                calendly_event_id=self._extract_event_id(agent_response)
            )
            
            # Save to a file
            data_dir = os.getenv('DATA_DIR')
            appointments_dir = os.path.join(data_dir, 'appointments')
            
            # Ensure the directory exists
            os.makedirs(appointments_dir, exist_ok=True)
            
            # Generate a filename based on patient name and date
            safe_name = "".join(c if c.isalnum() else "_" for c in appointment_data.get('name', 'unknown'))
            filename = f"{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join(appointments_dir, filename)
            
            # Save the appointment to the file
            with open(file_path, 'w') as f:
                json.dump(appointment.to_dict(), f, indent=2)
            
            logger.info(f"Appointment saved to {file_path}")
            
            # Save conversation history
            self._save_conversation()
        
        except Exception as e:
            logger.error(f"Error saving appointment: {str(e)}")
    
    def _extract_event_id(self, text: str) -> Optional[str]:
        """
        Extract the Calendly event ID from the agent response
        
        Args:
            text: Agent response text
        
        Returns:
            Event ID or None if not found
        """
        import re
        # Look for patterns like "confirmation number: ABC123" or similar
        patterns = [
            r'confirmation number[:\s]+([A-Za-z0-9\-_]+)',
            r'confirmation[:\s]+([A-Za-z0-9\-_]+)',
            r'appointment ID[:\s]+([A-Za-z0-9\-_]+)',
            r'ID[:\s]+([A-Za-z0-9\-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _save_conversation(self) -> None:
        """Save the conversation history to a file"""
        try:
            # Save to logs directory
            logs_dir = os.path.join(os.getenv('BASE_DIR', '.'), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            filename = f"conversation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = os.path.join(logs_dir, filename)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(self.conversation_history))
            
            logger.info(f"Conversation saved to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")