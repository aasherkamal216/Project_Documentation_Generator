FROM ollama/ollama

WORKDIR /app

# Use the correct path for model storage
VOLUME /root/.ollama

COPY pull-llama3.sh /home/
RUN chmod +x /home/pull-llama3.sh
