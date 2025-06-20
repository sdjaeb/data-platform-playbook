# webhook_listener_app/Dockerfile
# This Dockerfile builds an image for the simple Flask-based MinIO webhook listener.

# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask application code into the container
COPY app.py .

# Expose the port that the Flask app will listen on
EXPOSE 8081

# Command to run the Flask application using Gunicorn
# Using 0.0.0.0 to bind to all available network interfaces
# --workers 4: Recommended for production (adjust based on CPU cores)
# --bind 0.0.0.0:8081: Binds to the exposed port
CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8081", "app:app"]
