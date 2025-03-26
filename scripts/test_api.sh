#!/bin/bash

source .env
if [ -z "$1" ]; then
    echo "Error: Please provide a meeting URL"
    exit 1
fi

MEETING_URL="$1"

curl -X POST https://us-west-2.recall.ai/api/v1/bot \
    -H "Authorization: Token $RECALL_API_KEY" \
    -H "Content-Type: application/json" \
    --data-raw "{\"meeting_url\":\"$MEETING_URL\",\"recording_config\":{\"transcript\":{\"provider\":{\"meeting_captions\":{}}}}}"
