FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONPATH=/app/src:/app

# Make startup script executable
RUN chmod +x /app/start.sh

EXPOSE 7860 8000

CMD ["/app/start.sh"]
