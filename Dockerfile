# Use slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Cairo stack for WeasyPrint, safe for Debian Bookworm/Trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    libglib2.0-0 libgdk-pixbuf-2.0-0 libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    shared-mime-info fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN sed -i 's/\r$//' requirements.txt && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

CMD ["gunicorn","Bathelicious.wsgi:application","--bind","0.0.0.0:8000"]
