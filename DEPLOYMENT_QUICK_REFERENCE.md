# Quick Deployment Reference

## Frontend (Vercel) - https://sys-logger.vercel.app

### Environment Variables in Vercel Dashboard:
```
NEXT_PUBLIC_API_URL=https://your-render-backend-url.onrender.com
```

**Note:** Replace `your-render-backend-url` with your actual Render backend service URL.

---

## Backend (Render)

### Environment Variables in Render Dashboard:
```
HOST=0.0.0.0
PORT=5000
FLASK_ENV=production
FLASK_DEBUG=False
CORS_ORIGINS=https://sys-logger.vercel.app,https://sys-logger-git-main.vercel.app
LOG_FOLDER=/tmp/usage_logs
LOG_RETENTION_DAYS=2
LOG_INTERVAL=4
GITHUB_TOKEN=your_github_token_here  # Optional
GUNICORN_WORKERS=2
LOG_LEVEL=info
```

### Render Configuration:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn -c gunicorn_config.py sys_logger:app`
- **Root Directory:** `backend`

---

## Local Development

### Backend (.env):
- Port: `5001` (to avoid conflicts with AirPlay on macOS)
- CORS: Includes localhost ports for development
- LOG_FOLDER: Use Windows path (`C://Usage_Logs`) or Linux path (`/tmp/usage_logs`)

### Frontend (.env.local):
- NEXT_PUBLIC_API_URL: `http://localhost:5001` or `http://localhost:5000`

---

## Files Updated

✅ `backend/.env` - Updated with Vercel CORS origins and Linux paths
✅ `frontend/.env.local` - Updated with production notes
✅ `backend/env.example` - Updated with production examples
✅ `frontend/env.example` - Updated with Render URL format
✅ `docker-compose.yml` - Updated CORS origins
✅ `render.yaml` - Created Render deployment configuration
✅ `vercel.json` - Created Vercel configuration
✅ `DEPLOYMENT.md` - Updated with Render/Vercel instructions
✅ `README.md` - Updated with deployment links

---

## Next Steps

1. **Deploy Backend to Render:**
   - Connect GitHub repo
   - Use `render.yaml` or manually configure
   - Set environment variables
   - Note the backend URL (e.g., `https://sys-logger-backend.onrender.com`)

2. **Update Frontend in Vercel:**
   - Go to Vercel dashboard → Project Settings → Environment Variables
   - Set `NEXT_PUBLIC_API_URL` to your Render backend URL
   - Redeploy if needed

3. **Test Connection:**
   - Visit https://sys-logger.vercel.app
   - Check browser console for any CORS errors
   - Verify data is loading from backend

