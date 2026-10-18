from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
import io, qrcode, socket, subprocess, re
from config.settings import settings
from storage import json_store

router = APIRouter(tags=["qr"])

def _ip_from_ipconfig() -> str | None:
    """Parse ipconfig (Windows) offline — works even without internet, as long as adapter has IP.
    Skips virtual adapters (WSL/Docker/Hyper-V/VirtualBox/Bluetooth) so the real
    Wi-Fi / hotspot / Ethernet IP wins even when the IP changes (DHCP)."""
    try:
        # ipconfig works offline, shows 192.168.0.x even without internet
        out = subprocess.check_output("ipconfig", text=True, encoding="utf-8", errors="ignore")
    except Exception:
        try:
            out = subprocess.check_output("ipconfig", text=True, errors="ignore")
        except Exception:
            return None
    virtual_markers = ("virtual", "vbox", "wsl", "docker", "hyper-v", "hyperv",
                       "vethernet", "vmware", "bluetooth", "pseudo", "loopback", "tap-", "tun")
    # Split into per-adapter blocks; the adapter title is the first line of each block.
    blocks = re.split(r"\r?\n\s*\r?\n", out)
    candidates = []
    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if not lines:
            continue
        title = lines[0].lower()
        if any(m in title for m in virtual_markers):
            continue
        if "media disconnected" in block.lower():
            continue
        ips = re.findall(r"(\d+\.\d+\.\d+\.\d+)", block)
        for ip in ips:
            if ip.startswith("127.") or ip == "0.0.0.0" or ip.startswith("255."):
                continue
            if ip.startswith("169.254."):
                continue  # link-local, no DHCP — not routable for phones
            # WSL 172.23.* etc — deprioritize
            if ip.startswith("172.23.") or ip.startswith("172.29."):
                candidates.append((3, ip))
            elif ip.startswith("192.168.137."):
                candidates.append((-1, ip))  # Windows hotspot host IP — top priority
            elif ip.startswith("192.168."):
                # Docker Desktop VM lives at 192.168.65.* — skip it
                if ip.startswith("192.168.65."):
                    continue
                candidates.append((0, ip))
            elif ip.startswith("10."):
                candidates.append((1, ip))
            elif ip.startswith("172."):
                # 172.16-31
                try:
                    second = int(ip.split(".")[1])
                    if 16 <= second <= 31:
                        candidates.append((2, ip))
                    else:
                        candidates.append((4, ip))
                except:
                    candidates.append((4, ip))
            else:
                candidates.append((5, ip))
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    return None

def get_lan_ip() -> str:
    """Return LAN IP (e.g., 192.168.0.110) so phones on same router can join via QR — works even offline."""
    # 1) Env (Docker: HOST_LAN_IP from run_docker.bat) — most reliable for Docker
    try:
        from config.settings import settings as _s
        if _s.HOST_LAN_IP and not _s.HOST_LAN_IP.startswith("127."):
            return _s.HOST_LAN_IP.strip()
    except Exception:
        pass
    # 2) ipconfig offline parsing — works even without internet, gives 192.168.0.x
    ip = _ip_from_ipconfig()
    if ip:
        return ip
    # 3) UDP trick (needs internet) — fallback
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            if ip.startswith("172."):
                return "localhost"  # Docker container, not useful
            return ip
    except Exception:
        pass
    try:
        hostname = socket.gethostname()
        # gethostbyname_ex gives all IPs
        _, _, iplist = socket.gethostbyname_ex(hostname)
        for ip in iplist:
            if ip.startswith("192.168.") or ip.startswith("10."):
                return ip
        for ip in iplist:
            if not ip.startswith("127.") and not ip.startswith("172."):
                return ip
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127.") and not ip.startswith("172."):
            return ip
    except Exception:
        pass
    return "localhost"

def build_join_url(request: Request, code: str, base_url: str | None = None) -> str:
    """Build http://<LAN_IP>:<port>/join/<code> so QR works for all devices, not just localhost."""
    # An explicitly configured public URL must win over the browser-provided
    # URL so QR codes remain usable when the app is behind port forwarding or
    # a reverse proxy.
    if settings.PUBLIC_APP_URL:
        configured_url = settings.PUBLIC_APP_URL.strip().rstrip("/")
        if configured_url.startswith(("http://", "https://")):
            return f"{configured_url}/join/{code}"
    # In Vite development the API is proxied through port 8000, while clients
    # must open the frontend on port 5173. The frontend supplies that origin.
    if base_url:
        base_url = base_url.strip().rstrip("/")
        if base_url.startswith(("http://", "https://")):
            return f"{base_url}/join/{code}"
    # Use request Host to keep same port (5173 for vite dev, 8000 for prod/Docker)
    host_header = request.headers.get("host", "") if request else ""
    # host_header like "localhost:5173" or "192.168.1.10:8000" or "localhost:8000"
    port = "8000"
    is_localhost = True
    if host_header:
        if ":" in host_header:
            h, p = host_header.rsplit(":", 1)
            port = p
            is_localhost = h in ("localhost", "127.0.0.1", "::1")
        else:
            is_localhost = host_header in ("localhost", "127.0.0.1")
    # If request was via localhost, replace with LAN IP so phones can join
    if is_localhost or not host_header:
        lan = get_lan_ip()
        host = f"{lan}:{port}"
    else:
        host = host_header
    # Always http for local network (no TLS)
    return f"http://{host}/join/{code}"

@router.get("/api/events/{event_id}/qr")
def get_qr(event_id: str, request: Request, base_url: str | None = Query(None)):
    events = json_store.load("events", {})
    ev = None
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            ev = v
            break
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    url = build_join_url(request, ev['code'], base_url)
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@router.get("/api/events/{event_id}/qr-url")
def qr_url(event_id: str, request: Request, base_url: str | None = Query(None)):
    events = json_store.load("events", {})
    for v in events.values():
        if v["id"] == event_id or v["code"] == event_id:
            url = build_join_url(request, v['code'], base_url)
            return {"url": url, "code": v["code"], "lan_ip": get_lan_ip()}
    raise HTTPException(status_code=404, detail="Event not found")

@router.get("/api/network-info")
def network_info(request: Request):
    host_header = request.headers.get("host", "") if request else ""
    host = host_header.rsplit(":", 1)[0] if ":" in host_header else host_header
    host = host.strip().strip("[]")
    port = "8000"
    if host_header and ":" in host_header:
        port = host_header.rsplit(":", 1)[1]
    # Most truthful answer: the address this very request arrived on.
    # Survives DHCP/IP change with zero config — no env var needed.
    if host and host not in ("localhost", "127.0.0.1", "::1") and not host.startswith("172."):
        lan = host
    else:
        lan = get_lan_ip()
    return {
        "lan_ip": lan,
        "host_header": host_header,
        "join_base": f"http://{lan}:{port}",
        "port": port
    }
