# Stage 1: Build frontend (Vue + Vite)
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend + serve frontend
FROM python:3.11-slim
WORKDIR /app

# Run Redis in the same container as the application for a single-container deployment.
RUN apt-get update \
    && apt-get install -y --no-install-recommends redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install backend deps
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY backend/ ./backend/
COPY data/ ./data/
RUN sed -i 's/\r$//' /app/backend/docker-entrypoint.sh \
    && chmod +x /app/backend/docker-entrypoint.sh

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Ensure data dir exists and is writable
RUN mkdir -p /app/data /app/redis-data

WORKDIR /app/backend
EXPOSE 8000
ENV REDIS_URL=redis://127.0.0.1:6379/0
ENV DATA_DIR=/app/data
CMD ["/bin/sh", "/app/backend/docker-entrypoint.sh"]
