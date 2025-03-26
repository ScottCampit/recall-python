#!/usr/bin/env python3
import json
import os
import requests
import argparse
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime

def create_bot(api_key: str, meeting_url: str) -> str:
    """
    Create a bot to join the meeting
    
    Args:
        api_key (str): Recall.ai API key
        meeting_url (str): The meeting URL to transcribe
        
    Returns:
        str: Bot ID
    """
    url = "https://us-west-2.recall.ai/api/v1/bot"
    headers = {
        "Authorization": f"Token {api_key}",
        "accept": "application/json",
        "content-type": "application/json"
    }
    data = {
        "meeting_url": meeting_url,
        "recording_config": {
            "transcript": {
                "provider": {
                    "meeting_captions":{}
                }
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()["id"]

def save_bot_id(bot_id: str, output_dir: str = "bot_ids") -> str:
    """
    Save the bot ID to a JSON file
    
    Args:
        bot_id (str): The bot ID to save
        output_dir (str): Directory to save the output file
        
    Returns:
        str: Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bot_id_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    data = {
        "bot_id": bot_id,
        "created_at": timestamp
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath

def main():
    parser = argparse.ArgumentParser(description='Create a Recall.ai bot')
    parser.add_argument('meeting_url', help='The meeting URL to transcribe')
    parser.add_argument('--output-dir', '-o', default='bot_ids',
                      help='Directory to save the bot ID (default: bot_ids)')
    parser.add_argument('--debug', '-d', action='store_true',
                      help='Enable debug mode with verbose output')
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()
    api_key = os.getenv('RECALL_API_KEY')
    if not api_key:
        print("Error: RECALL_API_KEY not found in environment variables")
        print("\nPlease set your Recall.ai API key in the .env file:")
        print("RECALL_API_KEY=your_api_key_here")
        exit(1)

    try:
        # Create bot
        print(f"Creating bot for meeting: {args.meeting_url}")
        bot_id = create_bot(api_key, args.meeting_url)
        print(f"Bot created successfully with ID: {bot_id}")
        
        # Save bot ID
        output_file = save_bot_id(bot_id, args.output_dir)
        print(f"\nBot ID saved to: {output_file}")
        print("\nUse this bot ID with test_get_transcript.py to get the transcript")
        
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
