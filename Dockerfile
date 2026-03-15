FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y ffmpeg nodejs npm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY src/ .  

EXPOSE 8080

CMD ["python", "main.py"]  