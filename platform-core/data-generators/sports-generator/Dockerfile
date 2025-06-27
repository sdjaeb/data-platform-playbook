FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .

# Use pip to install packages
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
CMD ["python", "main.py"]