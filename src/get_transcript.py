#!/usr/bin/env python3
import json
import os
import requests
import argparse
from typing import Dict, Any
from dotenv import load_dotenv
from datetime import datetime

def get_transcript(api_key: str, bot_id: str) -> Dict[str, Any]:
    """
    Get the transcript from a bot
    
    Args:
        api_key (str): Recall.ai API key
        bot_id (str): The ID of the bot to get transcript from
        
    Returns:
        Dict[str, Any]: Transcript data
    """
    url = f"https://us-west-2.recall.ai/api/v1/bot/{bot_id}/transcript/"
    headers = {
        "Authorization": f"Token {api_key}",
        "accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def save_transcript(transcript: Dict[str, Any], output_dir: str = "transcripts") -> str:
    """
    Save the transcript to a JSON file
    
    Args:
        transcript (Dict[str, Any]): The transcript data
        output_dir (str): Directory to save the output file
        
    Returns:
        str: Path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transcript_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(transcript, f, indent=2)
    
    return filepath

def main():
    parser = argparse.ArgumentParser(description='Get transcript from a Recall.ai bot')
    parser.add_argument('bot_id', help='The bot ID to get transcript from')
    parser.add_argument('--output-dir', '-o', default='transcripts',
                      help='Directory to save the transcript (default: transcripts)')
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
        # Get transcript
        print(f"Getting transcript for bot ID: {args.bot_id}")
        transcript = get_transcript(api_key, args.bot_id)
        
        # Save transcript
        output_file = save_transcript(transcript, args.output_dir)
        print(f"\nTranscript saved to: {output_file}")
        
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
