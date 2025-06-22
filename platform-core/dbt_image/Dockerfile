# Use a specific Python version that is compatible with dbt-spark
FROM python:3.10-slim

# Set the working directory
WORKDIR /usr/app

# Copy the requirements file
COPY requirements.txt .

# Install dbt-spark and its dependencies
RUN pip install --no-cache-dir -r requirements.txt