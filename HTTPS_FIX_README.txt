=============================================================================
         HTTPS/HTTP PROXY FIX — WHAT WAS DONE & WHAT NEEDS TO BE DONE
=============================================================================

THE PROBLEM
-----------
The live frontend on Vercel (https) could not fetch data from the backend 
(http) because browsers block "mixed content" — HTTP requests from HTTPS pages.
The graphs and unit data appeared empty on the live site, even though the 
backend was receiving client data just fine.


WHAT WAS DONE (Code Changes)
-----------------------------
All changes are in: frontend/src/app/api/

1. CREATED: proxyUtils.ts
   - Shared utility with getBackendUrl(), proxyGet(), proxyPost()
   - Reads NEXT_PUBLIC_API_URL env variable for the backend URL
   - All API route handlers use this single source of truth

2. FIXED: units/[unitId]/route.ts
   - BUG FIX: Was calling /api/unit/ (singular) instead of /api/units/ (plural)
   - This was silently returning 404 on every unit usage request

3. FIXED: units/route.ts
   - Replaced hardcoded port-scanning logic with proxyGet()

4. FIXED: alerts/route.ts
   - Replaced hardcoded "http://localhost:5000" with getBackendUrl()

5. FIXED: alerts/[alertId]/acknowledge/route.ts
   - Replaced hardcoded "http://localhost:5000" with getBackendUrl()

6. CREATED: usage/route.ts        → proxies /api/usage
7. CREATED: orgs/route.ts         → proxies /api/orgs
8. CREATED: orgs/[orgId]/units/route.ts → proxies /api/orgs/:orgId/units
9. CREATED: units/[unitId]/export/route.ts → proxies CSV export with query params
10. CREATED: health/route.ts      → proxies /health

11. MODIFIED: components/hooks/useUsageData.ts
    - Removed Socket.IO dependency (can't work through Vercel serverless)
    - Replaced with 2-second HTTP polling (reliable, near-real-time)

HOW IT WORKS:
  Browser (HTTPS) → Vercel API Route (HTTPS) → Flask Backend (HTTP)
  The browser only talks to Vercel (same origin, no mixed content).
  Vercel's server-side code talks to the HTTP backend freely.


WHAT NEEDS TO BE DONE (Deployment Steps)
-----------------------------------------

Step 1: Set Environment Variable on Vercel
   - Go to: Vercel Dashboard → sys-logger → Settings → Environment Variables
   - Set: NEXT_PUBLIC_API_URL = http://203.193.145.59:5010
   - (Replace with your actual backend server's public IP and port)
   - Make sure it applies to "All Environments"
   - Click Save

Step 2: Push Code to GitHub
   - git add .
   - git commit -m "Fix HTTPS proxy for live site"
   - git push

Step 3: Vercel Auto-Redeploys
   - Vercel will detect the push and rebuild automatically
   - The build should pass (already verified locally)

Step 4: Verify on Live Site
   - Open your Vercel URL (e.g., https://sys-logger.vercel.app)
   - Open browser DevTools (F12) → Console tab
   - Check there are NO "Mixed Content" errors
   - Select a unit from the sidebar → graphs should appear
   - Check Network tab: /api/units/<id>/usage should return JSON data


TROUBLESHOOTING
---------------
If graphs still don't appear after deployment:

1. Check Vercel Function Logs:
   - Vercel Dashboard → sys-logger → Deployments → Latest → Function Logs
   - Look for errors like "ECONNREFUSED" (backend unreachable)

2. Check if backend is running:
   - From any machine: curl http://203.193.145.59:5010/health
   - Should return {"status": "ok", ...}

3. Check PostgreSQL:
   - If backend is reachable but /api/units/<id>/usage returns []
   - The issue is PostgreSQL not being set up or accessible
   - Check backend logs for "Failed to write to DB" errors

4. Check NEXT_PUBLIC_API_URL:
   - Must include http:// prefix
   - Must include the port number
   - Must NOT have a trailing slash
   - Correct:   http://203.193.145.59:5010
   - Incorrect: https://203.193.145.59:5010  (backend is HTTP, not HTTPS)
   - Incorrect: 203.193.145.59:5010          (missing http://)
   - Incorrect: http://203.193.145.59:5010/  (trailing slash)

=============================================================================
