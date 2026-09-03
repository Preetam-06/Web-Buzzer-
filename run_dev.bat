@echo off
echo ==========================================
echo Faculty Trivia Buzzer - DEV MODE
echo Backend: http://localhost:8000  Frontend: http://localhost:5173
echo Redis REQUIRED for 50+ players
echo ==========================================
echo Checking Redis...
python -c "import redis; r=redis.Redis(host='localhost',port=6379, socket_connect_timeout=1); r.ping()" >nul 2>&1
if errorlevel 1 goto redis_warning
echo [OK] Redis running - safe for 50+ concurrent buzz
goto redis_done
:redis_warning
echo [WARNING] Redis NOT running at localhost:6379
echo For 50+ players, start Redis first:
echo   Option A: docker compose up -d redis
echo   Option B: docker run -d -p 6379:6379 redis:7-alpine
echo   Option C: double-click run_redis.bat
echo Continuing with in-memory fallback (OK for testing)...
:redis_done
echo.
echo Starting backend and frontend...
start cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
start cmd /k "cd frontend && npm run dev"
echo.
echo Open http://localhost:5173/admin  (admin/admin123)
echo Check Redis: http://localhost:8000/api/health
