FROM python:3.9-slim-buster\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY app.py .\nEXPOSE 8081\nCMD ["python", "app.py"]
