"""
Hospital Appointment System
Main entry point for the appointment scheduling application
"""

import argparse
import sys
from app.conversation.engine import ConversationEngine
from app.utils.logger import setup_logging
from config.settings import load_environment_variables

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Hospital Appointment Scheduling System')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--log-file', type=str, default='logs/app.log', help='Log file path')
    return parser.parse_args()

def main():
    """Main application function"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(debug=args.debug, log_file=args.log_file)
    
    # Load environment variables
    if not load_environment_variables():
        print("Error: Failed to load environment variables. Please check your .env file.")
        sys.exit(1)
    
    try:
        # Initialize the conversation engine
        engine = ConversationEngine()
        
        # Start the conversation loop
        engine.start()
    except KeyboardInterrupt:
        print("\nExiting application...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()