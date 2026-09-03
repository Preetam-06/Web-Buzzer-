@echo off
echo ==========================================
echo Faculty Trivia Buzzer - ONE COMMAND DOCKER
echo Builds frontend + backend + redis
echo Single URL: http://localhost:8000
echo QR will use LAN IP (not localhost) so phones can join
echo ==========================================
echo Detecting LAN IP for QR...
set LAN_IP=
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
  for /f "tokens=1" %%i in ("%%a") do (
    set LAN_IP=%%i
    goto :found_ip
  )
)
:found_ip
set LAN_IP=%LAN_IP: =%
if "%LAN_IP%"=="" set LAN_IP=localhost
echo LAN IP detected: %LAN_IP%
set HOST_LAN_IP=%LAN_IP%
echo.
echo Checking Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Docker not found.
  echo Install Docker Desktop: https://www.docker.com/products/docker-desktop
  echo After install, restart PC and open Docker Desktop once (wait for green Running).
  pause
  exit /b 1
)
docker compose version >nul 2>&1
if %errorlevel% neq 0 (
  echo Trying docker-compose...
  docker-compose --version >nul 2>&1
  if %errorlevel% neq 0 (
    echo ERROR: docker compose not found.
    pause
    exit /b 1
  ) else (
    echo Using docker-compose...
    echo Starting all services (frontend build happens inside Docker)...
    docker-compose up --build -d
    goto :done
  )
)
echo Starting all services (frontend build happens inside Docker)...
docker compose up --build -d
:done
if %errorlevel% neq 0 (
  echo Build/Start failed. Check errors above.
  pause
  exit /b 1
)
echo.
echo ==========================================
echo SUCCESS! All running in Docker
echo ==========================================
echo Admin:    http://localhost:8000/admin  (admin / admin123)
echo Admin via LAN IP: http://%LAN_IP%:8000/admin  (use this for correct QR)
echo Display:  http://%LAN_IP%:8000/display/FACULTY26
echo Join:     http://%LAN_IP%:8000/join/FACULTY26  ^<-- share this / QR uses this
echo Health:   http://localhost:8000/api/health  (check Redis)
echo Network:  http://localhost:8000/api/network-info  (verify LAN IP)
echo.
echo View logs:   docker compose logs -f
echo Stop all:    docker compose down
echo.
echo For phones on same Wi-Fi, scan QR or open: http://%LAN_IP%:8000/join/FACULTY26
echo If QR shows localhost, open Admin via http://%LAN_IP%:8000/admin instead of localhost
echo.
timeout /t 3 >nul
start http://%LAN_IP%:8000/admin
pause
