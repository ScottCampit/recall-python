#!/usr/bin/env python3
import json
import os
import requests
import argparse
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import queue
import re

def is_valid_google_meet_url(url: str) -> bool:
    """
    Check if the URL is a valid Google Meet URL
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if it's a valid Google Meet URL
    """
    patterns = [
        r'https://meet\.google\.com/[a-z-]+',  # Standard Google Meet URL
        r'https://meet\.google\.com/[a-z-]+/[a-z-]+'  # Google Meet URL with room code
    ]
    return any(re.match(pattern, url) for pattern in patterns)

class WebhookHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.callback_queue = kwargs.pop('callback_queue')
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Add the webhook data to the queue
        self.callback_queue.put(data)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received"}).encode())

class RecallAPI:
    def __init__(self, api_key: str, region: str = "us-west-2"):
        self.api_key = api_key
        self.base_url = f"https://api.recall.ai/api/v1"
        self.headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_bot(self, meeting_url: str, bot_name: str = "GoogleMeetBot", webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a bot to join the Google Meet
        
        Args:
            meeting_url (str): The Google Meet URL to transcribe
            bot_name (str): Name of the bot (default: "GoogleMeetBot")
            webhook_url (Optional[str]): URL to receive webhook notifications
            
        Returns:
            Dict[str, Any]: Bot creation response including bot ID
        """
        if not is_valid_google_meet_url(meeting_url):
            raise ValueError("Invalid Google Meet URL format")

        data = {
            "bot_name": bot_name,
            "meeting_url": meeting_url,
            "transcription_options": {
                "provider": "meeting_captions"
            }
        }
        
        if webhook_url:
            data["webhook_url"] = webhook_url
        
        try:
            response = requests.post(
                f"{self.base_url}/bot",
                headers=self.headers,
                json=data
            )
            
            # Add detailed error handling for authentication issues
            if response.status_code == 403:
                print("Authentication Error: Please check your API key")
                print("Make sure your RECALL_API_KEY environment variable is set correctly")
                print("The API key should start with 'recall_'")
                response.raise_for_status()
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                print(f"API Error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 403:
                    print("\nTroubleshooting steps:")
                    print("1. Verify your API key is correct")
                    print("2. Make sure you have access to the Recall.ai API")
                    print("3. Check if your API key has the necessary permissions")
            raise

    def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        """
        Get the current status of a bot
        
        Args:
            bot_id (str): The ID of the bot to check
            
        Returns:
            Dict[str, Any]: Bot status information
        """
        response = requests.get(
            f"{self.base_url}/bot/{bot_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_transcript(self, bot_id: str) -> Dict[str, Any]:
        """
        Get the transcript from a bot
        
        Args:
            bot_id (str): The ID of the bot to get transcript from
            
        Returns:
            Dict[str, Any]: Transcript data
        """
        response = requests.get(
            f"{self.base_url}/bot/{bot_id}/transcript",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

def wait_for_bot_join(api: RecallAPI, bot_id: str, max_attempts: int = 30) -> bool:
    """
    Wait for the bot to join the meeting
    
    Args:
        api (RecallAPI): The API client
        bot_id (str): The ID of the bot to check
        max_attempts (int): Maximum number of attempts to check status
        
    Returns:
        bool: True if bot joined successfully, False otherwise
    """
    valid_states = ["joined", "recording", "completed"]
    
    for attempt in range(max_attempts):
        try:
            status = api.get_bot_status(bot_id)
            current_status = status.get("status")
            
            if current_status in valid_states:
                print(f"Bot is in state: {current_status}")
                return True
                
            print(f"Waiting for bot to join meeting... (attempt {attempt + 1}/{max_attempts})")
            print(f"Current status: {current_status}")
            time.sleep(2)  # Wait 2 seconds between checks
        except requests.exceptions.RequestException as e:
            print(f"Error checking bot status: {e}")
            return False
    return False

def save_response(response_data: Dict[str, Any], output_dir: str = "test_outputs"):
    """
    Save the API response to a JSON file
    
    Args:
        response_data (Dict[str, Any]): The processed response data
        output_dir (str): Directory to save the output file
    """
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"google_meet_transcript_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(response_data, f, indent=2)
    
    return filepath

def wait_for_webhook(callback_queue: queue.Queue, timeout: int = 300) -> Optional[Dict[str, Any]]:
    """
    Wait for a webhook notification
    
    Args:
        callback_queue (queue.Queue): Queue to receive webhook data
        timeout (int): Maximum time to wait in seconds
        
    Returns:
        Optional[Dict[str, Any]]: Webhook data if received, None if timeout
    """
    try:
        return callback_queue.get(timeout=timeout)
    except queue.Empty:
        return None

def run_webhook_server(port: int, callback_queue: queue.Queue) -> HTTPServer:
    """
    Run a webhook server to receive notifications
    
    Args:
        port (int): Port to listen on
        callback_queue (queue.Queue): Queue to receive webhook data
        
    Returns:
        HTTPServer: The running server
    """
    server = HTTPServer(('localhost', port), lambda *args, **kwargs: WebhookHandler(*args, callback_queue=callback_queue, **kwargs))
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server

def main():
    parser = argparse.ArgumentParser(description='Test the Recall.ai API with Google Meet')
    parser.add_argument('meeting_url', help='The Google Meet URL to transcribe')
    parser.add_argument('--output-dir', '-o', default='test_outputs',
                      help='Directory to save the output file (default: test_outputs)')
    parser.add_argument('--debug', '-d', action='store_true',
                      help='Enable debug mode with verbose output')
    parser.add_argument('--wait-time', '-w', type=int, default=30,
                      help='Maximum time to wait for bot to join (seconds)')
    parser.add_argument('--bot-name', '-n', default='GoogleMeetBot',
                      help='Name of the bot (default: GoogleMeetBot)')
    parser.add_argument('--webhook-port', '-p', type=int, default=8000,
                      help='Port to listen for webhooks (default: 8000)')
    parser.add_argument('--no-webhook', action='store_true',
                      help='Disable webhook and use polling instead')
    args = parser.parse_args()

    # Validate Google Meet URL
    if not is_valid_google_meet_url(args.meeting_url):
        print("Error: Invalid Google Meet URL format")
        print("URL should be in the format: https://meet.google.com/xxx-xxxx-xxx")
        exit(1)

    # Load environment variables
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        print(f"Error: .env file not found at {env_path}")
        print("\nPlease create a .env file with your Recall.ai API key:")
        print("RECALL_API_KEY=recall_your_api_key_here")
        print("\nYou can get your API key from: https://recall.ai/dashboard")
        exit(1)

    load_dotenv(env_path)
    api_key = os.getenv('RECALL_API_KEY')
    
    if not api_key:
        print("Error: RECALL_API_KEY not found in .env file")
        print("\nPlease add your Recall.ai API key to the .env file:")
        print("RECALL_API_KEY=recall_your_api_key_here")
        print("\nYou can get your API key from: https://recall.ai/dashboard")
        exit(1)
        
    if args.debug:
        print(f"Loaded API key: {api_key[:8]}...")
        print(f"Using .env file: {env_path}")

    api = RecallAPI(api_key)
    webhook_url = None
    webhook_server = None
    callback_queue = queue.Queue()

    try:
        if not args.no_webhook:
            # Start webhook server
            webhook_server = run_webhook_server(args.webhook_port, callback_queue)
            webhook_url = f"http://localhost:{args.webhook_port}"
            if args.debug:
                print(f"Webhook server listening on {webhook_url}")

        if args.debug:
            print(f"Creating bot '{args.bot_name}' for Google Meet: {args.meeting_url}")
            print(f"Using API endpoint: {api.base_url}")
            print(f"Using API key: {api_key[:8]}...")
        
        # Step 1: Create bot
        bot_response = api.create_bot(args.meeting_url, bot_name=args.bot_name, webhook_url=webhook_url)
        bot_id = bot_response.get('id')
        
        if not bot_id:
            raise ValueError("No bot ID received from API")
            
        if args.debug:
            print(f"Bot created successfully with ID: {bot_id}")
            print("Waiting for bot to join meeting...")
        
        # Step 2: Wait for bot to join
        if not wait_for_bot_join(api, bot_id, max_attempts=args.wait_time // 2):
            raise TimeoutError("Bot failed to join the meeting within the specified time")
            
        if args.debug:
            print("Bot joined successfully!")
            
        if webhook_url:
            print("Waiting for webhook notification...")
            webhook_data = wait_for_webhook(callback_queue)
            if webhook_data:
                print("Received webhook notification!")
            else:
                print("No webhook received, proceeding with transcript retrieval...")
        
        if args.debug:
            print("Getting transcript...")
        
        # Step 3: Get transcript
        transcript = api.get_transcript(bot_id)
        
        if args.debug:
            print(f"Transcript received with {len(transcript)} segments")
            print("Saving transcript...")
        
        # Save the transcript
        output_file = save_response(transcript, args.output_dir)
        
        print(f"\nTranscript generation completed successfully!")
        print(f"Transcript saved to: {output_file}")
        print(f"Number of segments: {len(transcript)}")
        
    except ValueError as e:
        print(f"Configuration error: {e}")
        exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API call failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Error details: {e.response.text}")
        exit(1)
    except TimeoutError as e:
        print(f"Timeout error: {e}")
        exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        exit(1)
    finally:
        if webhook_server:
            webhook_server.shutdown()
            webhook_server.server_close()

if __name__ == "__main__":
    main()
