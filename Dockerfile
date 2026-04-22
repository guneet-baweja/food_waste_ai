# ─────────────────────────────────────────
# FoodSave AI — Production Dockerfile
# Build: docker build -t foodsave-ai .
# Run:   docker run -p 8080:8080 foodsave-ai
# ─────────────────────────────────────────

FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    libgl1-mesa-glx curl git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn eventlet flask-socketio

# Copy project
COPY . .

# Create required directories
RUN mkdir -p data static/uploads ai/models ai/dataset

# Environment
ENV FLASK_ENV=production
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/stats || exit 1

CMD ["gunicorn", "--worker-class", "eventlet", \
     "-w", "1", "-b", "0.0.0.0:8080", \
     "--timeout", "120", "--access-logfile", "-", \
     "app:app"]