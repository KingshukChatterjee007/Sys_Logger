/**
 * Shared proxy utility for API route handlers.
 * All backend requests from Next.js API routes go through here.
 */

export function getBackendUrl(): string {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'
}

/**
 * Extract Authorization header from incoming request for forwarding.
 */
function getAuthHeaders(request?: Request): Record<string, string> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (request) {
        const auth = request.headers.get('Authorization')
        if (auth) headers['Authorization'] = auth
    }
    return headers
}

/**
 * Proxy a GET request to the Flask backend and return the JSON response.
 */
export async function proxyGet(backendPath: string, request?: Request): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`

    const response = await fetch(url, {
        headers: getAuthHeaders(request),
        cache: 'no-store',
    })

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        return new Response(JSON.stringify({ error: text }), {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
        })
    }

    const data = await response.json()
    return Response.json(data)
}

/**
 * Proxy a POST request to the Flask backend.
 */
export async function proxyPost(backendPath: string, body?: unknown, request?: Request): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`

    const response = await fetch(url, {
        method: 'POST',
        headers: getAuthHeaders(request),
        body: body ? JSON.stringify(body) : undefined,
    })

    // Special handling for binary responses (ZIP downloads)
    const contentType = response.headers.get('Content-Type') || ''
    if (contentType.includes('application/zip') || contentType.includes('application/octet-stream')) {
        const blob = await response.blob()
        return new Response(blob, {
            status: response.status,
            headers: {
                'Content-Type': contentType,
                'Content-Disposition': response.headers.get('Content-Disposition') || 'attachment',
            },
        })
    }

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        return new Response(JSON.stringify({ error: text }), {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
        })
    }

    const data = await response.json()
    return Response.json(data)
}
