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

---

## Multi-Tenant Authentication System

### Default Credentials (CHANGE IN PRODUCTION)

| Role  | Username | Password    | Access                     |
|-------|----------|-------------|----------------------------|
| Admin | `admin`  | `admin123`  | `/admin` — full control    |
| Org   | `nielit`  | `nielit123` | `/NIELIT-BBSR` — org only  |

### Environment Variables for Auth

Add to backend `.env`:

```env
JWT_SECRET=your-strong-random-secret-here
JWT_EXPIRATION_HOURS=24
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM=your-email@gmail.com
FRONTEND_URL=https://your-frontend-url.vercel.app
BACKEND_URL=http://your-server-ip:5010
```

### SMTP Setup (Gmail)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate a new app password for "Mail"
5. Use this 16-character password as `SMTP_PASS`

> If SMTP is not configured, password reset links print to the backend console instead.

### Tier System

| Tier       | Default Nodes | Description                              |
|------------|---------------|------------------------------------------|
| Individual | 1             | Single node monitoring                   |
| Business   | 2 (default)   | Multi-node, expandable at additional cost |

- `node_limit` is per-org in the DB — admin can increase beyond tier default
- Switch tier via Billing tab or admin panel

---

## Testing Locally

### Step 1: Start Backend
```bash
cd backend
# Activate venv
.\venv\Scripts\activate     # Windows
source venv/bin/activate    # Linux/Mac

# Install deps (if needed)
pip install -r requirements.txt

# Run server (auto-creates auth tables on start)
python sys_logger.py
```
Backend starts on `http://localhost:5000` (or port in `.env`).

### Step 2: Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend starts on `http://localhost:3000`.

### Step 3: Test Login

1. Open `http://localhost:3000/login`
2. **Admin login:** `admin` / `admin123` → redirects to `/admin`
3. **Org login:** `nielit` / `nielit123` → redirects to `/NIELIT-BBSR`

### Step 4: Test Admin Dashboard

- View orgs, total nodes, server health at `/admin`
- View billing at `/admin/billing`
- Register new org via API:
```bash
curl -X POST http://localhost:5000/api/admin/register-org \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Org","slug":"TEST-ORG","tier":"individual","contact_email":"test@example.com","username":"testuser","password":"test123"}'
```

### Step 5: Test Org Dashboard

1. Login as `nielit` / `nielit123`
2. **Dashboard tab** — same monitoring view, filtered to org's nodes
3. **Nodes tab** — view nodes, click "Add Node", enter a name, download client ZIP
4. **Billing tab** — view current tier, switch tier

### Step 6: Test Client Deploy

1. In Nodes tab, click **"+ Add Node"** → enter node name (e.g. `LAB-PC-01`)
2. Click **"Download Client Installer"** on the node card
3. Extract ZIP → pre-configured `unit_client_config.json` with org_id, comp_id, server_url
4. Run installer on target machine

### Step 7: Test Password Reset

1. Go to `/reset-password`
2. Enter email associated with account
3. If SMTP configured → check email for reset link
4. If SMTP not configured → check backend console for link

---

## API Endpoints Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login with username/password |
| GET | `/api/auth/me` | Get current user info (requires token) |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/reset-password` | Reset password with token |

### Admin (requires admin role)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Global stats, orgs, server health |
| GET | `/api/admin/orgs` | List all organizations |
| POST | `/api/admin/register-org` | Register new org + user |

### Org (requires auth)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/org/dashboard` | Org stats + nodes |
| GET | `/api/org/nodes` | List org's nodes |
| POST | `/api/org/nodes/add` | Add node (checks tier limit) |
| POST | `/api/org/download-client` | Download pre-filled client ZIP |

### Billing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/billing/info` | Billing details |
| POST | `/api/billing/switch-tier` | Switch org tier |

### Frontend Routes
| Route | Access | Description |
|-------|--------|-------------|
| `/login` | Public | Login page |
| `/reset-password` | Public | Forgot/reset password |
| `/admin` | Admin | Admin dashboard |
| `/admin/billing` | Admin | Billing overview |
| `/{orgSlug}` | Org/Admin | Org dashboard with tabs |
| `/fleet` | Admin | Fleet monitoring view |
