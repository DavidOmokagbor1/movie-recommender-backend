# ML API - Python 3.9 for NumPy/SciPy compatibility
FROM python:3.9-slim

WORKDIR /app

# Install build deps and upgrade pip/setuptools/wheel first
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run sets PORT (default 8080)
ENV PORT=8080
EXPOSE 8080

# Run gunicorn (same as Procfile)
CMD gunicorn api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
