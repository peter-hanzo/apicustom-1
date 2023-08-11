# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# FFmpeg installation
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container to /app
WORKDIR /app

# Add current directory files to /app in container
ADD . /app

# Install necessary packages, Flask and ffmpeg-python
RUN pip install --no-cache-dir flask ffmpeg-python requests gunicorn psycopg2-binary pytube joblib pydub moviepy youtube_transcript_api

# Make port 5000 available to the world outside this container
# EXPOSE 5000

# Run app.py (Flask server) when the container launches
CMD gunicorn --bind 0.0.0.0:$PORT app:app
