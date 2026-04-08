#!/bin/bash
# ============================================================
# VPS FIX SCRIPT - Run these commands on the Hostinger VPS
# SSH: ssh root@187.127.142.58
# ============================================================

# ---- STEP 1: Install Nginx ----
apt update && apt install -y nginx

# ---- STEP 2: Create Nginx reverse proxy config ----
cat > /etc/nginx/sites-available/sys-logger << 'EOF'
server {
    listen 80;
    server_name 187.127.142.58 lab-monitoring.nielitbhubaneswar.in;

    # Increase timeouts for long-running requests
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    # Increase upload limit for installer ZIPs
    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# ---- STEP 3: Enable the site ----
ln -sf /etc/nginx/sites-available/sys-logger /etc/nginx/sites-enabled/sys-logger
rm -f /etc/nginx/sites-enabled/default

# ---- STEP 4: Test and reload Nginx ----
nginx -t && systemctl restart nginx && systemctl enable nginx

# ---- STEP 5: Verify ----
echo "=== Nginx Status ==="
systemctl is-active nginx
echo "=== Listening Ports ==="
ss -tlnp | grep -E "80|5010"
echo "=== Quick API Test ==="
curl -s http://127.0.0.1:5010/api/health | head -c 200
echo ""
curl -s http://127.0.0.1:80/api/health | head -c 200
