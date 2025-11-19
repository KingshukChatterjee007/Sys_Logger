#!/usr/bin/env python3
"""
Server Setup Script for Sys_Logger
This script automatically sets up the Sys_Logger server environment including:
- Docker setup and verification
- Database initialization with schema
- Environment configuration
- Service startup
"""

import os
import sys
import platform
import subprocess
import shutil
import json
import sqlite3
from pathlib import Path
import requests
import time

def run_command(command, shell=False, cwd=None):
    """Run a command and return success status"""
    try:
        print(f"Running: {' '.join(command) if isinstance(command, list) else command}")
        result = subprocess.run(
            command,
            shell=shell,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def check_prerequisites():
    """Check if required software is installed"""
    print("Checking prerequisites...")

    # Check Docker
    success, output = run_command(['docker', '--version'])
    if not success:
        print("ERROR: Docker is not installed or not accessible.")
        print("Please install Docker from https://docs.docker.com/get-docker/")
        return False
    else:
        print(f"✓ Docker found: {output.strip()}")

    # Check Docker Compose
    success, output = run_command(['docker-compose', '--version'])
    if not success:
        # Try docker compose (newer versions)
        success, output = run_command(['docker', 'compose', 'version'])
        if not success:
            print("ERROR: Docker Compose is not installed or not accessible.")
            print("Please install Docker Compose from https://docs.docker.com/compose/install/")
            return False
        else:
            print(f"✓ Docker Compose found: {output.strip()}")
    else:
        print(f"✓ Docker Compose found: {output.strip()}")

    # Check Python
    if sys.version_info < (3, 6):
        print("ERROR: Python 3.6 or higher is required")
        return False
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} found")

    return True

def check_docker_running():
    """Check if Docker daemon is running"""
    success, output = run_command(['docker', 'info'])
    if not success:
        print("ERROR: Docker daemon is not running.")
        print("Please start Docker and try again.")
        return False
    return True

def setup_database():
    """Initialize the database with schema"""
    print("Setting up database...")

    # Database file path
    db_path = Path('data/sys_logger.db')

    # Create data directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables based on schema
    tables = [
        """
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id TEXT UNIQUE NOT NULL,
            hostname TEXT NOT NULL,
            os_info TEXT NOT NULL,
            cpu_info TEXT,
            ram_total REAL,
            gpu_info TEXT,
            network_interfaces TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS usage_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            timestamp DATETIME NOT NULL,
            cpu_usage REAL,
            ram_usage REAL,
            gpu_usage REAL,
            temperature REAL,
            network_rx REAL,
            network_tx REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (unit_id) REFERENCES units (id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (unit_id) REFERENCES units (id) ON DELETE CASCADE
        );
        """
    ]

    # Execute table creation
    for table_sql in tables:
        cursor.execute(table_sql)

    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_units_system_id ON units(system_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_data_unit_id_timestamp ON usage_data(unit_id, timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_usage_data_timestamp ON usage_data(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_unit_id_timestamp ON alerts(unit_id, timestamp);"
    ]

    for index_sql in indexes:
        cursor.execute(index_sql)

    # Commit and close
    conn.commit()
    conn.close()

    print(f"✓ Database initialized at {db_path}")
    return True

def setup_environment():
    """Setup environment files"""
    print("Setting up environment configuration...")

    # Backend environment
    backend_env = Path('backend/.env')
    if not backend_env.exists():
        env_content = """FLASK_ENV=production
PORT=5000
HOST=0.0.0.0
CORS_ORIGINS=https://sys-logger.vercel.app,http://localhost:3000,http://localhost:3001
LOG_FOLDER=/app/logs
LOG_RETENTION_DAYS=2
LOG_INTERVAL=4
"""
        with open(backend_env, 'w') as f:
            f.write(env_content)
        print("✓ Created backend/.env")

    # Frontend environment
    frontend_env = Path('frontend/.env.local')
    if not frontend_env.exists():
        env_content = """NODE_ENV=production
NEXT_PUBLIC_API_URL=http://localhost:5000
"""
        with open(frontend_env, 'w') as f:
            f.write(env_content)
        print("✓ Created frontend/.env.local")

    return True

def build_and_start_services():
    """Build and start Docker services"""
    print("Building and starting services...")

    # Change to project root directory
    project_root = Path(__file__).parent

    # Stop any existing services
    print("Stopping existing services...")
    run_command(['docker-compose', 'down'], cwd=project_root)

    # Build services
    print("Building services...")
    success, output = run_command(['docker-compose', 'build'], cwd=project_root)
    if not success:
        print("ERROR: Failed to build services")
        return False

    # Start services
    print("Starting services...")
    success, output = run_command(['docker-compose', 'up', '-d'], cwd=project_root)
    if not success:
        print("ERROR: Failed to start services")
        return False

    print("✓ Services started successfully")
    return True

def wait_for_services(timeout=60):
    """Wait for services to be ready"""
    print("Waiting for services to be ready...")

    backend_url = "http://localhost:5000/api/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(backend_url, timeout=5)
            if response.status_code == 200:
                print("✓ Backend service is ready")
                return True
        except requests.RequestException:
            pass

        print("Waiting for backend service...")
        time.sleep(2)

    print("ERROR: Services failed to start within timeout period")
    return False

def test_installation():
    """Test that the installation is working"""
    print("Testing installation...")

    # Test backend health
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=10)
        if response.status_code == 200:
            print("✓ Backend health check passed")
        else:
            print(f"⚠ Backend health check returned status {response.status_code}")
    except Exception as e:
        print(f"ERROR: Backend health check failed: {e}")
        return False

    # Test frontend accessibility
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✓ Frontend is accessible")
        else:
            print(f"⚠ Frontend returned status {response.status_code}")
    except Exception as e:
        print(f"⚠ Frontend not accessible (may be building): {e}")

    return True

def main():
    print("Sys_Logger Server Setup")
    print("=" * 40)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Check Docker is running
    if not check_docker_running():
        sys.exit(1)

    # Setup database
    if not setup_database():
        sys.exit(1)

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Build and start services
    if not build_and_start_services():
        sys.exit(1)

    # Wait for services
    if not wait_for_services():
        sys.exit(1)

    # Test installation
    test_installation()

    print("\n" + "=" * 40)
    print("Server setup completed successfully!")
    print("=" * 40)
    print("Services are running:")
    print("• Backend API: http://localhost:5000")
    print("• Frontend: http://localhost:3000")
    print("• Database: SQLite (data/sys_logger.db)")
    print("\nTo check service status:")
    print("  docker-compose ps")
    print("\nTo view logs:")
    print("  docker-compose logs -f")
    print("\nTo stop services:")
    print("  docker-compose down")

if __name__ == "__main__":
    main()