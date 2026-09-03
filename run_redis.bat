@echo off
echo Starting Redis for 50+ players...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
  echo Docker not found. Trying native Redis...
  redis-server --version >nul 2>&1
  if %errorlevel% neq 0 (
    echo ERROR: Neither Docker nor redis-server found.
    echo Install Docker Desktop from https://www.docker.com/products/docker-desktop
    echo OR install Redis for Windows from https://github.com/microsoftarchive/redis/releases
    pause
    exit /b 1
  ) else (
    echo Starting native redis-server...
    start "Redis" redis-server
    goto :check
  )
) else (
  echo Docker found. Starting Redis container...
  docker run -d --name trivia_redis -p 6379:6379 redis:7-alpine >nul 2>&1
  if %errorlevel% neq 0 (
    echo Container may already exist, trying to start existing...
    docker start trivia_redis
  )
  echo Redis container started.
)

:check
timeout /t 2 >nul
echo Checking Redis...
python -c "import redis; r=redis.Redis(host='localhost',port=6379, socket_connect_timeout=2); r.ping(); print('Redis PING OK - ready for 50+ players')"
if %errorlevel% neq 0 (
  echo Redis check failed. Check if port 6379 is free.
) else (
  echo SUCCESS: Redis running at redis://localhost:6379/0
)
pause
