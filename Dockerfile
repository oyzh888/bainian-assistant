FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
# Note: .env and config.json are NOT copied (gitignored)
# Pass OPENROUTER_API_KEY as an environment variable at runtime

EXPOSE 3005
CMD ["python", "app.py"]
