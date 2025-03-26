import streamlit as st
import json
import os
import requests
from dotenv import load_dotenv
from typing import Optional, Generator, Union, List, Dict

# Load environment variables
load_dotenv()

# Set page config
st.set_page_config(
    page_title="Recall.ai Transcript Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .transcript-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        transform: translateY(-1px);
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        padding: 10px;
    }
    h1 {
        color: #1E1E1E;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    h2 {
        color: #1E1E1E;
        font-size: 1.8em;
        margin-bottom: 0.5em;
    }
    </style>
""", unsafe_allow_html=True)

def load_mock_data() -> List[Dict]:
    """Load mock transcript data from test_output.json"""
    mock_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tests', 'test_output.json')
    with open(mock_file_path, 'r') as f:
        return json.load(f)

def recall_api(meeting_url: str) -> Optional[requests.Response]:
    """Make the API call to Recall.ai"""
    api_key = os.getenv('RECALL_API_KEY')
    if not api_key:
        st.error("RECALL_API_KEY not found in environment variables")
        return None

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "meeting_url": meeting_url,
        "recording_config": {
            "transcript": {
                "provider": {
                    "meeting_captions": {}
                }
            }
        }
    }

    try:
        response = requests.post(
            "https://us-west-2.recall.ai/api/v1/bot",
            headers=headers,
            json=data,
            stream=True
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        st.error(f"API call failed: {str(e)}")
        return None

def process_stream(response: Union[requests.Response, List[Dict]]) -> Generator[Dict, None, None]:
    """Process the streaming response from the API or mock data"""
    if isinstance(response, list):
        # Handle mock data
        for item in response:
            yield item
    else:
        # Handle real API response
        for line in response.iter_lines():
            if line:
                try:
                    yield json.loads(line.decode('utf-8'))
                except json.JSONDecodeError:
                    continue

def format_transcript(json_data: list[dict]) -> str:
    """Format the transcript from JSON data"""
    transcript = []
    for segment in json_data:
        speaker = segment['speaker']
        text = segment['words'][0]['text']
        # Ensure consistent markdown formatting with double asterisks
        transcript.append(f"**{speaker}**: {text}")
    # Use double newlines for consistent spacing
    return "\n\n".join(transcript)

def main():
    # Header with logo and title
    st.title("🎙️ Recall.ai Transcript Generator")
    
    st.markdown("---")
    
    # Description
    st.header("Instructions")
    st.markdown("""
        Transform your Google Meet recordings into text transcripts with speaker identification.
        Simply paste your meeting URL below and click 'Generate Transcript'.
    """, unsafe_allow_html=True)
    
    # URL input with better styling
    meeting_url = st.text_input(
        "Meeting URL",
        placeholder="https://meet.google.com/xxx-xxxx-xxx",
        help="Enter the Google Meet URL you want to transcribe"
    )
    
    # Generate button
    if st.button("Generate Transcript", type="primary"):
        if not meeting_url:
            st.warning("Please enter a meeting URL")
            return

        # Create a placeholder for the transcript
        transcript_placeholder = st.empty()
        transcript_data = []
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("Generating transcript..."):
            # Use mock data for now
            response = load_mock_data()
            # Make the API call
            #response = recall_api(meeting_url)
            
            if response:
                # Process the streaming response
                for i, segment in enumerate(process_stream(response)):
                    transcript_data.append(segment)
                    # Update the transcript in real-time
                    transcript_placeholder.markdown(
                        f"""
                        <div class="transcript-container">
                            {format_transcript(transcript_data)}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    # Update progress
                    progress = min((i + 1) / len(response), 1.0)  # Use actual length of mock data
                    progress_bar.progress(progress)
                    status_text.text(f"Processing segment {i + 1} of {len(response)}...")
                
                # Final status
                status_text.text("Transcript generation complete!")
                progress_bar.progress(1.0)
            else:
                st.error("Failed to connect to the API")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            Built with ❤️ using Recall.ai API
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 