# Prerequisites for All Users (Server & Client)
---
## System Requirements:

### Windows 10/11, Linux, or macOS
4GB RAM minimum, 8GB recommended
2GB free disk space
Internet connection for initial setup
Automatic Prerequisite Installation:
The setup scripts will automatically check and install required software:

### For Server Deployment:

**Docker Desktop (latest version)** - Container platform
**Python 3.8+** - Runtime for setup scripts
**Node.js 18+ (handled by Docker)** - For frontend building

### For Client Deployment:
**Python 3.6+** - Runtime for monitoring
**psutil** - System monitoring library
**requests** - HTTP communication
**GPUtil (optional)** - NVIDIA GPU monitoring

--- 

## Distribution Package Contents

Core Files to Ship:

`server_setup.py              # Automated server setup
unit_client.py               # Client monitoring script
docker-compose.yml           # Docker orchestration
backend/                     # Flask API server
frontend/                    # React dashboard
installation/                # GUI installer & management tools
README.md                    # Documentation
DEPLOYMENT.md                # Deployment guide
QUICK_START.md               # Quick start guide`

---

## Deployment Options

### Option 1: Localhost Deployment (Recommended for Testing)

**Server Setup:**

1. Ensure Docker Desktop is installed and running
2. Run: `python server_setup.py`

Services start on:
`
Backend API: http://localhost:5000
Frontend Dashboard: http://localhost:3000
Database: SQLite in data/sys_logger.db
`
**Client Setup:**

1. Install Python dependencies: pip install psutil requests
2. Run: `python unit_client.py`
Enter server URL: `http://localhost:5000`

Client auto-registers and starts monitoring

## Option 2: Domain/Public Access Deployment

**Server Setup:**

1. Complete localhost setup first
2. Configure domain/reverse proxy (nginx, Apache, or cloud load balancer)
3. Update **CORS** settings in `backend/.env`:
`CORS_ORIGINS=https://yourdomain.com,http://yourdomain.com`

4. For **HTTPS**, configure **SSL certificate**
5. Update `frontend/.env.local`:
`NEXT_PUBLIC_API_URL=https://yourdomain.com`

**Network Configuration:**

1. Open ports **80/443** (HTTP/HTTPS) and **5000** (API)
2. Configure firewall rules
3. Set up DNS records for domain

**Client Connection:**

1. Use full domain URL: https://yourdomain.com
2. Clients connect securely over HTTPS
3. No additional firewall configuration needed

**GUI Applications**

* Web Dashboard (Frontend)
* **Framework:** Next.js 16 with React 19
* **Styling:** Tailwind CSS for responsive design
* **Components:** Interactive charts, real-time updates
* **Responsive:** Mobile and desktop optimized

**Features:**

* Real-time system monitoring graphs
* Unit management interface
* Alert dashboard
* Responsive grid layout for all screen sizes
* Desktop Management Applications
* **Server Manager:** `server_manager.py` - GUI for client management
* **Server Installer:** `server_installer.py` - Professional installation wizard

---
## Installation
### Run the installer executable (when built)

`SysLogger_Server_Installer.exe`

### Manual setup

`python server_setup.py`

**Or use systemd services**

`sudo cp unit_client.service /etc/systemd/system/
sudo systemctl enable unit_client
sudo systemctl start unit_client`

### Client Distribution Methods

**Method 1: Direct Python Script**

1. Ship `unit_client.py` only
2. Users run: python unit_client.py
3. Script prompts for server URL
4. Auto-installs dependencies if missing

**Method 2: Packaged Executable (PyInstaller)**

1. Build standalone executable: pyinstaller --onefile unit_client.py
2. No Python installation required on client machines
3. Self-contained with all dependencies

**Method 3: Automated Installer Script**

1. Use setup.py for automated client installation
2. Creates directories, installs services, configures startup
3. Verification and Testing

---

## Server Health Check:

### Check services
`docker-compose ps`

### Test API
curl http://localhost:5000/api/health

### Test frontend
curl http://localhost:3000

---

## Client Testing:

# Run in foreground for testing
`python unit_client.py --foreground`

# Check logs
`python unit_client.py --status`

**Security Considerations**
1. Default database uses SQLite (no external access)
2. API endpoints require no authentication for basic monitoring
3. *For production:* implement authentication, HTTPS, firewall rules
4. Client-server communication uses HTTP (upgrade to HTTPS for security)

**Troubleshooting Distribution**

*Common Issues:*

1. **Docker not running:** Start Docker Desktop
2. **Port conflicts:** Check ports 3000, 5000 availability
3. **Permission errors:** Run as administrator/sudo
4. **Network issues:** Verify firewall settings

*Logs Location:*

1. **Server logs:** `docker-compose logs -f`
2. **Client logs:** unit_client.log (created automatically)
3. **Setup logs:** Console output during installation


This distribution package provides flexible deployment options for both localhost development and production domain hosting, with responsive web interfaces and user-friendly desktop applications.
