# Python Implementation for Recall.ai Google Meet API

This project provides a simple Python implementation for interacting with the Recall.ai API to transcribe Google Meet meetings. The implementation is split into two scripts: `src/create_bot.py` to create the Google Meet bot, and `src/get_transcript.py` to get the transcript once the meeting is finished.

## Requirements

- Python 3.8 or higher
- Recall.ai API key
- Google Meet meeting URL

## Setup

1. Clone the repository:
```bash
git clone
cd recall
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install requests python-dotenv
```

4. Create a `.env` file in the project root:
```bash
RECALL_API_KEY=your_recall_api_key_here
```

## Project Structure

```
recall/
├── .env                    # API key configuration
├── src/
│   ├── create_bot.py      # Script to create a bot
│   └── get_transcript.py  # Script to get transcript
├── bot_ids/               # Directory for storing bot IDs
└── transcripts/           # Directory for storing transcripts
```

## Usage

### 1. Create a Bot

First, create a bot to join your Google Meet meeting:

```bash
python src/create_bot.py "https://meet.google.com/xxx-xxxx-xxx"
```

Options:
- `--output-dir` or `-o`: Directory to save the bot ID (default: "bot_ids")
- `--debug` or `-d`: Enable debug mode with verbose output

Example with options:
```bash
python src/create_bot.py "https://meet.google.com/xxx-xxxx-xxx" --debug --output-dir ./my_bot_ids
```

The script will:
1. Create a bot to join the meeting
2. Save the bot ID to a JSON file in the specified directory
3. Display the bot ID and file location

### 2. Get the Transcript

After the bot has joined and recorded the meeting, get the transcript:

```bash
python src/get_transcript.py "your_bot_id_here"
```

Options:
- `--output-dir` or `-o`: Directory to save the transcript (default: "transcripts")
- `--debug` or `-d`: Enable debug mode with verbose output

Example with options:
```bash
python src/get_transcript.py "your_bot_id_here" --debug --output-dir ./my_transcripts
```

The script will:
1. Fetch the transcript from the bot
2. Save it as a JSON file in the specified directory
3. Display the file location

## Complete Workflow Example

```bash
# 1. Create a bot and get its ID
python src/create_bot.py "https://meet.google.com/xxx-xxxx-xxx" --debug

# Wait for the bot to join and record the meeting...

# 2. Get the transcript using the bot ID
python src/get_transcript.py "bot_id_from_previous_step" --debug
```

## Output Files

### Bot ID File (JSON)
```json
{
  "bot_id": "your_bot_id_here",
  "created_at": "20240321_123456"
}
```

### Transcript File (JSON)
The transcript file contains the meeting transcription data in JSON format.

## Error Handling

Both scripts include error handling for:
- Missing or invalid API key
- Invalid meeting URL
- API request failures
- File system errors

## Debug Mode

Use the `--debug` flag to get detailed information about:
- API requests and responses
- File operations
- Bot creation and transcript retrieval process

## Notes

- The bot needs time to join the meeting and start recording
- Transcripts are only available after the bot has successfully joined and recorded

## Troubleshooting

1. **API Key Issues**
   - Verify your API key in the `.env` file
   - Check if you have sufficient API credits

2. **Bot Creation Issues**
   - Verify the meeting URL is correct
   - Ensure the meeting is active
   - Check if the bot has permission to join

3. **Transcript Issues**
   - Wait for the bot to join and start recording
   - Verify the bot ID is correct
   - Check if the meeting has ended

## Contributing

Feel free to submit issues and enhancement requests!
