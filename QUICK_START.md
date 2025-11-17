# Quick Start Guide

Get the System Logger up and running in minutes!

## Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate
git clone <repository-url>
cd Sys_Logger

# 2. Configure environment (optional, defaults work for local dev)
cp backend/env.example backend/.env
cp frontend/env.example frontend/.env.local

# 3. Start everything
docker-compose up -d

# 4. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000/api/health
```

## Option 2: Manual Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
cp env.example .env
python sys_logger.py
```

### Frontend (New Terminal)

```bash
cd frontend
npm install
cp env.example .env.local
npm run dev
```

## Option 3: Production Deployment

### Backend with Gunicorn

```bash
cd backend
pip install -r requirements.txt
cp env.example .env
# Edit .env for production settings
gunicorn --config gunicorn_config.py sys_logger:app
```

### Frontend Build

```bash
cd frontend
npm install
cp env.example .env.local
# Set NEXT_PUBLIC_API_URL to your backend URL
npm run build
npm start
```

## Environment Variables Quick Reference

### Backend (.env)
```bash
PORT=5000
CORS_ORIGINS=http://localhost:3000
GITHUB_TOKEN=your_token_here  # Optional
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Troubleshooting

**Backend won't start:**
- Check if port 5000 is available
- Verify Python dependencies: `pip install -r requirements.txt`

**Frontend can't connect:**
- Verify backend is running: `curl http://localhost:5000/api/health`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Docker issues:**
- Check logs: `docker-compose logs`
- Rebuild: `docker-compose up -d --build`

## Next Steps

- See [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment
- See [README.md](./README.md) for full documentation

