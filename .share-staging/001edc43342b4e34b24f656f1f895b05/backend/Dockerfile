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

# Install backend deps
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and data
COPY backend/ ./backend/
COPY data/ ./data/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Ensure data dir exists and is writable
RUN mkdir -p /app/data

WORKDIR /app/backend
EXPOSE 8000
ENV REDIS_URL=redis://redis:6379/0
ENV DATA_DIR=/app/data
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
