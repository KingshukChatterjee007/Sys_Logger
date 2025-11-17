# Deployment Guide

This guide covers deploying the System Logger application to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Platform-Specific Deployment](#platform-specific-deployment)
- [Production Checklist](#production-checklist)

## Prerequisites

- Python 3.11+ (for backend)
- Node.js 20+ (for frontend)
- Docker and Docker Compose (for containerized deployment)
- Git

## Environment Variables

### Backend Environment Variables

Copy `backend/env.example` to `backend/.env` and configure:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0

# CORS Configuration (comma-separated origins)
# For production, specify your frontend domain(s)
CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com

# GitHub Gist Integration (Optional)
GITHUB_TOKEN=your_github_token_here

# Logging Configuration
LOG_FOLDER=/app/logs  # Use absolute path
LOG_RETENTION_DAYS=7  # Keep logs for 7 days
LOG_INTERVAL=4        # Log every 4 seconds
```

### Frontend Environment Variables

Copy `frontend/env.example` to `frontend/.env.local` and configure:

```bash
# Backend API URL
# For production, use your backend domain
NEXT_PUBLIC_API_URL=https://api.your-domain.com

# Environment
NODE_ENV=production
```

## Docker Deployment

### Quick Start with Docker Compose

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Sys_Logger
   ```

2. **Configure environment variables:**

   - Copy `backend/env.example` to `backend/.env`
   - Copy `frontend/env.example` to `frontend/.env.local`
   - Update the values for your production environment

3. **Update docker-compose.yml:**

   - Set `NEXT_PUBLIC_API_URL` in the frontend build args
   - Update `CORS_ORIGINS` in backend environment
   - Configure volume paths for logs

4. **Build and start:**

   ```bash
   docker-compose up -d --build
   ```

5. **Check logs:**

   ```bash
   docker-compose logs -f
   ```

6. **Stop services:**
   ```bash
   docker-compose down
   ```

### Individual Docker Containers

#### Backend

```bash
cd backend
docker build -t sys-logger-backend .
docker run -d \
  --name sys-logger-backend \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -e FLASK_ENV=production \
  -e CORS_ORIGINS=https://your-frontend.com \
  -e GITHUB_TOKEN=your_token \
  sys-logger-backend
```

#### Frontend

```bash
cd frontend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.your-domain.com \
  -t sys-logger-frontend .
docker run -d \
  --name sys-logger-frontend \
  -p 3000:3000 \
  sys-logger-frontend
```

## Manual Deployment

### Backend Deployment

#### Using Gunicorn (Recommended for Production)

1. **Install dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Run with Gunicorn:**

   ```bash
   gunicorn --config gunicorn_config.py sys_logger:app
   ```

   Or with custom settings:

   ```bash
   gunicorn --bind 0.0.0.0:5000 \
     --workers 4 \
     --threads 2 \
     --timeout 120 \
     sys_logger:app
   ```

#### Using Systemd (Linux)

1. **Create service file** `/etc/systemd/system/sys-logger.service`:

   ```ini
   [Unit]
   Description=System Logger Backend
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/sys-logger/backend
   Environment="PATH=/opt/sys-logger/backend/venv/bin"
   ExecStart=/opt/sys-logger/backend/venv/bin/gunicorn --config gunicorn_config.py sys_logger:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start:**
   ```bash
   sudo systemctl enable sys-logger
   sudo systemctl start sys-logger
   sudo systemctl status sys-logger
   ```

### Frontend Deployment

#### Build and Deploy

1. **Install dependencies:**

   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment:**

   ```bash
   cp env.example .env.local
   # Edit .env.local with your backend URL
   ```

3. **Build for production:**

   ```bash
   npm run build
   ```

4. **Start production server:**
   ```bash
   npm start
   ```

#### Deploy to Vercel

1. **Install Vercel CLI:**

   ```bash
   npm i -g vercel
   ```

2. **Deploy:**

   ```bash
   cd frontend
   vercel
   ```

3. **Set environment variables in Vercel dashboard:**
   - `NEXT_PUBLIC_API_URL`: Your backend API URL

#### Deploy to Other Platforms

- **Netlify:** Use `netlify deploy --prod`
- **AWS Amplify:** Connect your Git repository
- **Railway:** Connect your Git repository
- **Render:** Connect your Git repository

## Platform-Specific Deployment

### Windows Service

For Windows deployment, use the provided PowerShell script:

```powershell
# Run as Administrator
cd backend
.\create_service.ps1
```

### Nginx Reverse Proxy

Example Nginx configuration:

```nginx
# Backend API
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS Setup

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d your-domain.com -d api.your-domain.com
```

## Production Checklist

### Security

- [ ] Set `FLASK_DEBUG=False` in production
- [ ] Configure proper CORS origins (not `*`)
- [ ] Use HTTPS for all connections
- [ ] Secure environment variables (use secrets management)
- [ ] Enable firewall rules
- [ ] Regular security updates

### Performance

- [ ] Configure appropriate Gunicorn workers
- [ ] Set up log rotation
- [ ] Configure log retention
- [ ] Enable caching (if applicable)
- [ ] Monitor resource usage

### Monitoring

- [ ] Set up health check monitoring
- [ ] Configure log aggregation
- [ ] Set up error tracking (Sentry, etc.)
- [ ] Monitor API response times
- [ ] Set up uptime monitoring

### Backup

- [ ] Configure log backups
- [ ] Set up database backups (if applicable)
- [ ] Test restore procedures

## Troubleshooting

### Backend Issues

**Port already in use:**

```bash
# Find process using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill process or change PORT in .env
```

**CORS errors:**

- Verify `CORS_ORIGINS` includes your frontend URL
- Check that frontend is using correct `NEXT_PUBLIC_API_URL`

**GPU monitoring not working:**

- On Linux, GPU monitoring may require additional setup
- Consider running backend on Windows for full GPU support
- Or modify GPU detection for Linux containers

### Frontend Issues

**API connection failed:**

- Verify `NEXT_PUBLIC_API_URL` is correct
- Check backend is running and accessible
- Verify CORS configuration

**Build errors:**

- Clear `.next` folder: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

## Support

For issues and questions, please check:

- Backend README: `backend/README.md`
- Frontend README: `frontend/README.md`
- GitHub Issues (if applicable)
