@echo off
echo ==========================================
echo Faculty Trivia Buzzer - ONE COMMAND DOCKER
echo Runs the frontend + backend + redis in one container
echo Single URL: http://localhost:8000
echo QR will use LAN IP (not localhost) so phones can join
echo ==========================================
echo Detecting LAN IP for QR (skips virtual adapters, survives IP change on re-run)...
set LAN_IP=
for /f "usebackq delims=" %%i in (`powershell -noprofile -command "Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.InterfaceAlias -notmatch 'vEthernet|WSL|Docker|Hyper-V|VirtualBox|VMware|Bluetooth|Loopback|vBox|Virtual' } | Sort-Object { if ($_.IPAddress -like '192.168.137.*') {0} elseif ($_.IPAddress -like '192.168.*') {1} elseif ($_.IPAddress -like '10.*') {2} else {3} } | Select-Object -First 1 -ExpandProperty IPAddress" 2^>nul`) do set LAN_IP=%%i
if "%LAN_IP%"=="" (
  echo PowerShell detect failed, falling back to ipconfig...
  for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    for /f "tokens=1" %%i in ("%%a") do (
      set LAN_IP=%%i
      goto :found_ip
    )
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
    echo Starting all services with the detected IP...
    docker-compose up -d --force-recreate
    goto :done
  )
)
echo Starting all services with the detected IP...
docker compose up -d --force-recreate
:done
if %errorlevel% neq 0 (
  echo Build/Start failed. Check errors above.
  pause
  exit /b 1
)
echo.
echo ==========================================
echo SUCCESS! Frontend, backend, and Redis running in one container
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
