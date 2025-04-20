#!/bin/bash

# Start ollama server
/bin/ollama serve &
SERVER_PID=$!

# Wait for server to be ready
sleep 5

# Check if model already exists
if ! ollama list | grep -q "llama3.1"; then
    echo "Pulling Llama 3.1 Model"
    ollama pull llama3.1
    echo "Pulled Llama 3.1 Model Successfully"
else
    echo "Llama 3.1 Model already exists, skipping download"
fi

# Keep the container running by waiting on the server process
wait $SERVER_PID
