# Development
# here goes your poject directory not mine 
cd D:\Project\mcc_evnt
python -m pip install -r requirements.txt
cd frontend
npm install
cd D:\Project\mcc_evnt
.\run_dev.bat

---------------------------------------------------------------------------------------------------
# 1. Open PowerShell as Administrator.
# 2. Run:
New-NetFirewallRule -DisplayName "Trivia Buzzer 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private

# Production
cd D:\Project\mcc_evnt
docker compose down
docker compose up --build -d