#!/bin/bash

docker build -t recall-app .
docker run -it --rm -p 8501:8501 -v $(pwd)/.env:/app/.env recall-app
    -p 8501:8501 \
    -v $(pwd)/.env:/app/.env \
    recall-app 