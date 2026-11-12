FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . /app/

# Create directory for persistent SQLite database
RUN mkdir -p /data

EXPOSE 8003

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8003"]
