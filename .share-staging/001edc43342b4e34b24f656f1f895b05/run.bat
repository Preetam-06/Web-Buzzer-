@echo off
echo ==========================================
echo Faculty Trivia Buzzer - PRODUCTION MODE
echo Single port: http://localhost:8000
echo Redis REQUIRED for 50+ players
echo ==========================================
echo Checking Redis...
python -c "import redis; r=redis.Redis(host='localhost',port=6379, socket_connect_timeout=1); r.ping()" >nul 2>&1
if errorlevel 1 goto redis_warning
echo [OK] Redis running
goto redis_done
:redis_warning
echo [WARNING] Redis NOT running at localhost:6379
echo Start Redis: docker compose up -d redis  OR  run_redis.bat
echo Continuing with fallback (OK for testing, NOT for 50+ live)...
:redis_done
echo.
echo Building frontend...
cd frontend
call npm run build
if %errorlevel% neq 0 (
  echo Build failed! Check npm errors above.
  pause
  exit /b 1
)
cd ..
echo.
echo Starting backend on http://localhost:8000
echo Admin: http://localhost:8000/admin
echo Display: http://localhost:8000/display/FACULTY26
echo Join: http://localhost:8000/join/FACULTY26
echo Health: http://localhost:8000/api/health  (check Redis status)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
