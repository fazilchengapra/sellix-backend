# Base Python image
FROM python:3.14-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Print logs immediately
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose application port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "sellix_backend.asgi:application", "--host", "0.0.0.0", "--port", "8000"]