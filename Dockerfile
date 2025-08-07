# Use the official Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 main:app