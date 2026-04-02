# Fix VPS Deployment Issues (Mixed Content & 500 Errors)

This plan addresses the critical errors encountered after migrating to the Hostinger VPS, specifically the Mixed Content blocks and backend connection failures.

## Proposed Changes

### 1. Fix Mixed Content Errors
We will move all client-side fetches to use relative Next.js API routes. This ensures the browser only talks to the HTTPS frontend, and the frontend server handles the HTTP communication with the backend.

#### [NEW] [route.ts](file:///d:/Projects/Sys_Logger/frontend/src/app/api/pricing/route.ts)
- Create a new proxy route for `/api/pricing` using `proxyGet`.

#### [MODIFY] [page.tsx](file:///d:/Projects/Sys_Logger/frontend/src/app/page.tsx)
- Change `fetch(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/pricing`)` to `fetch('/api/pricing')`.

#### [MODIFY] [DashboardView.tsx](file:///d:/Projects/Sys_Logger/frontend/src/app/DashboardView.tsx)
- Change any absolute backend fetches to relative `/api/...` routes.

### 2. Fix 500 Internal Server Error (Backend)
The 500 error on login usually indicates a database connection failure or a missing environment variable on the server.

#### [MODIFY] [.env](file:///d:/Projects/Sys_Logger/backend/.env)
- Update `CORS_ORIGINS` to include `https://lab-monitoring.nielitbhubaneswar.in`.
- Ensure `DB_HOST`, `DB_USER`, and `DB_PASS` match the VPS PostgreSQL setup.

#### [MODIFY] [sys_logger.py](file:///d:/Projects/Sys_Logger/backend/sys_logger.py)
- Improve error logging for database connection failures so they don't just return a generic 500 without a trace.

### 3. Fix Hydration Error (React #418)
- This should resolve automatically once the data fetching is consistent between server and client via the proxy routes.

## User Review Required

> [!IMPORTANT]
> **PostgreSQL Check**: Please verify that PostgreSQL is installed and running on your Hostinger VPS. You can check this by running `systemctl status postgresql` in your VPS terminal.
>
> **Database Credentials**: Ensure the `DB_PASS=root` and `DB_USER=postgres` in your `backend/.env` are correct for your local VPS database.

## Verification Plan

### Automated Tests
- Use `curl` to check the backend `/health` and `/api/pricing` endpoints directly on the VPS.
- Verify the frontend `/api/pricing` route returns data when accessed via the proxy.

### Manual Verification
- Refresh the live site `https://lab-monitoring.nielitbhubaneswar.in/` and check the console for Mixed Content errors.
- Attempt a login and verify it no longer returns a 500 error.
