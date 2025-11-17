# System Logger

A comprehensive system monitoring application that tracks CPU, RAM, and GPU usage in real-time with a beautiful web dashboard.

## Features

- 📊 **Real-time Monitoring**: Track CPU, RAM, and GPU usage with live charts
- 🎨 **Modern Dashboard**: Beautiful, responsive Next.js frontend with Tailwind CSS
- 🔄 **Dual Data Sources**: Switch between local logs and GitHub Gist storage
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 🔒 **Production Ready**: Configured for production deployment with Gunicorn
- 📝 **Automatic Logging**: Configurable logging intervals and retention
- 🚀 **Health Checks**: Built-in health check endpoints for monitoring

## Architecture

- **Backend**: Python Flask API with system monitoring capabilities
- **Frontend**: Next.js 16 with React 19 and TypeScript
- **Data Storage**: Local file system or GitHub Gist (optional)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker (optional, for containerized deployment)

### Development Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd Sys_Logger
   ```

2. **Backend Setup:**

   ```bash
   cd backend
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your configuration
   python sys_logger.py
   ```

3. **Frontend Setup:**

   ```bash
   cd frontend
   npm install
   cp env.example .env.local
   # Edit .env.local with your backend URL
   npm run dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed deployment instructions.

## Project Structure

```
Sys_Logger/
├── backend/              # Python Flask backend
│   ├── sys_logger.py     # Main application
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile        # Backend container
│   └── env.example       # Environment variables template
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js app directory
│   │   └── components/   # React components
│   ├── Dockerfile        # Frontend container
│   └── env.example       # Environment variables template
├── docker-compose.yml    # Docker Compose configuration
└── DEPLOYMENT.md         # Deployment guide
```

## Configuration

### Backend Environment Variables

- `FLASK_ENV`: Environment (development/production)
- `PORT`: Server port (default: 5000)
- `HOST`: Server host (default: 0.0.0.0)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `GITHUB_TOKEN`: GitHub token for Gist integration (optional)
- `LOG_FOLDER`: Directory for log files
- `LOG_RETENTION_DAYS`: Days to keep logs (default: 2)
- `LOG_INTERVAL`: Logging interval in seconds (default: 4)

### Frontend Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NODE_ENV`: Node environment (development/production)

## API Endpoints

- `GET /api/usage` - Get current system usage
- `GET /api/logs` - Get local log files
- `GET /api/gist-logs` - Get logs from GitHub Gist
- `GET /api/health` - Health check endpoint

## Development

### Backend Development

```bash
cd backend
python sys_logger.py
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

**Backend:**

```bash
cd backend
gunicorn --config gunicorn_config.py sys_logger:app
```

**Frontend:**

```bash
cd frontend
npm run build
npm start
```

## Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

### Quick Deploy Options

- **Docker Compose**: `docker-compose up -d`
- **Vercel** (Frontend):
  - Connect GitHub repo to Vercel
  - Set `NEXT_PUBLIC_API_URL` environment variable to your backend URL
  - Deployed at: https://sys-logger.vercel.app
- **Render** (Backend):
  - Connect GitHub repo to Render
  - Use `render.yaml` for configuration
  - Set environment variables in Render dashboard
  - See [DEPLOYMENT.md](./DEPLOYMENT.md) for details
- **Manual**: Follow deployment guide

## Platform Support

- **Windows**: Full support including GPU monitoring
- **Linux**: CPU/RAM monitoring (GPU may require additional setup)
- **macOS**: CPU/RAM monitoring (GPU support limited)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:

- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment help
- Review backend and frontend README files
- Open an issue on GitHub
