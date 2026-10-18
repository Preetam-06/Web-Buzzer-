# Faculty Trivia Buzzer

The production Docker image contains the Vue frontend, FastAPI backend,
WebSockets, and Redis in **one container**. The complete application is
available on port `8000`. You do not need a separate frontend container, Redis
container, Node.js installation, or frontend start command.

`run_docker.bat` starts one container named `trivia_backend`.

## Run with Docker (Windows)

### First setup or after code/dependency changes

Open Docker Desktop, then run these commands in PowerShell:

```powershell
cd D:\Project\mcc_evnt
docker compose down --remove-orphans
docker compose build
.\run_docker.bat
docker compose ps
curl http://localhost:8000/api/health
```

Open the admin page:

```powershell
start http://localhost:8000/admin
```

### Normal startup

After the image has been built, run only:

```powershell
cd D:\Project\mcc_evnt
.\run_docker.bat
```

Run this command again whenever the computer changes networks or its IP address
changes. It refreshes the current IP without rebuilding the image.

### Logs and stop commands

```powershell
cd D:\Project\mcc_evnt
docker compose logs -f
```

In another PowerShell window, stop the app with:

```powershell
cd D:\Project\mcc_evnt
docker compose down
```

## Open it from another device on the same network

The backend and Docker port are already bound to all host interfaces
(`0.0.0.0:8000:8000`). Do not use `localhost` on the phone or another PC;
`localhost` always means that device itself.

1. Find the Windows host IPv4 address with `ipconfig` (for example,
   `192.168.1.25`).
2. Allow the port in **PowerShell opened as Administrator**:

   ```powershell
   New-NetFirewallRule -DisplayName "Trivia Buzzer 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
   ```

3. On the other device, open:
   `http://192.168.1.25:8000/admin`

Use the same LAN URL when displaying or generating the QR code. QR links use
the request host automatically when the admin page is opened through the LAN
address. Both HTTP API calls and WebSockets use the same origin, so no extra
frontend port is needed.

If the device cannot connect, ensure it is on the same Wi-Fi/VLAN, Windows
network discovery/firewall allows private-network traffic, and Docker Desktop
is running.

## Publish it on the internet

Docker cannot make a private machine publicly reachable by itself. For internet
access, use a public DNS name or public IP and forward TCP port 8000 on the
router/firewall to the Windows host. Allow the port in the Windows firewall as
above, then open the forwarded URL, for example
`http://quiz.example.com:8000/admin`.

For a stable QR URL (recommended when using port forwarding or a reverse
proxy), create a `.env` file beside `docker-compose.yml`:

```dotenv
PUBLIC_APP_URL=https://quiz.example.com
```

Then recreate the backend so it reads the setting:

```powershell
docker compose up --build -d --force-recreate
```

`PUBLIC_APP_URL` is used for generated join QR codes. If it is empty, the app
uses the URL through which the admin page was opened. Use HTTPS through a
reverse proxy for internet deployments, change the default admin password and
secret key, and do not expose Redis (port 6379) to the internet.

## Development mode

For local development only:

```powershell
cd D:\Project\mcc_evnt
python -m pip install -r requirements.txt
cd frontend
npm install
cd D:\Project\mcc_evnt
.\run_dev.bat
```