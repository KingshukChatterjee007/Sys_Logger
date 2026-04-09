/**
 * Shared proxy utility for API route handlers.
 * All backend requests from Next.js API routes go through here.
 */

export function getBackendUrl(): string {
    return process.env.NEXT_PUBLIC_API_URL || 'http://187.127.142.58'
}

/**
 * Proxy a GET request to the Flask backend and return the JSON response.
 */
export async function proxyGet(backendPath: string, token?: string | null): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const effectiveToken = token || (typeof window !== 'undefined' ? localStorage.getItem('token') : null)

    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            'X-Proxy-Token-Present': effectiveToken ? 'true' : 'false',
            ...(effectiveToken ? { 'Authorization': effectiveToken.startsWith('Bearer ') ? effectiveToken : `Bearer ${effectiveToken}` } : {})
        },
        cache: 'no-store',
    })

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        try {
            // Try to parse as JSON to see if it's a backend error message
            const json = JSON.parse(text)
            return new Response(JSON.stringify(json), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            })
        } catch {
            return new Response(JSON.stringify({ error: text }), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            })
        }
    }

    const data = await response.json()
    return Response.json(data, {
        headers: {
            'Cache-Control': 'no-store, max-age=0, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
    })
}

/**
 * Proxy a POST request to the Flask backend.
 */
export async function proxyPost(backendPath: string, body?: unknown, token?: string | null): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const effectiveToken = token || (typeof window !== 'undefined' ? localStorage.getItem('token') : null)

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(effectiveToken ? { 'Authorization': effectiveToken.startsWith('Bearer ') ? effectiveToken : `Bearer ${effectiveToken}` } : {})
        },
        body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        try {
            // Try to parse as JSON to see if it's a backend error message
            const json = JSON.parse(text)
            return new Response(JSON.stringify(json), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            })
        } catch {
            return new Response(JSON.stringify({ error: text }), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            })
        }
    }

    const data = await response.json()
    return Response.json(data, {
        headers: {
            'Cache-Control': 'no-store, max-age=0, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
    })
}

/**
     * Proxy a PUT request to the Flask backend.
     */
export async function proxyPut(backendPath: string, body?: unknown, token?: string | null): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const effectiveToken = token || (typeof window !== 'undefined' ? localStorage.getItem('token') : null)

    const response = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-Proxy-Token-Present': effectiveToken ? 'true' : 'false',
            ...(effectiveToken ? { 'Authorization': effectiveToken.startsWith('Bearer ') ? effectiveToken : `Bearer ${effectiveToken}` } : {})
        },
        body: body ? JSON.stringify(body) : undefined,
    })

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        return new Response(JSON.stringify({ error: text }), {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
        })
    }

    const data = await response.json()
    return Response.json(data, {
        headers: {
            'Cache-Control': 'no-store, max-age=0, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
    })
}

/**
 * Proxy a DELETE request to the Flask backend.
 */
export async function proxyDelete(backendPath: string, token?: string | null): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const effectiveToken = token || (typeof window !== 'undefined' ? localStorage.getItem('token') : null)

    const response = await fetch(url, {
        method: 'DELETE',
        headers: {
            ...(effectiveToken ? { 'Authorization': effectiveToken.startsWith('Bearer ') ? effectiveToken : `Bearer ${effectiveToken}` } : {})
        },
    })

    if (!response.ok) {
        const text = await response.text().catch(() => 'Unknown error')
        return new Response(JSON.stringify({ error: text }), {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
        })
    }

    return new Response(null, { status: 204 })
}
