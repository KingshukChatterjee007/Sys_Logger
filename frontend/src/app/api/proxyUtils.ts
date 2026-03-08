/**
 * Shared proxy utility for API route handlers.
 * All backend requests from Next.js API routes go through here.
 */

export function getBackendUrl(): string {
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'
}

/**
 * Proxy a GET request to the Flask backend and return the JSON response.
 */
export async function proxyGet(backendPath: string): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
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
    return Response.json(data)
}

/**
 * Proxy a POST request to the Flask backend.
 */
export async function proxyPost(backendPath: string, body?: unknown): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
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
    return Response.json(data)
}

/**
     * Proxy a PUT request to the Flask backend.
     */
export async function proxyPut(backendPath: string, body?: unknown): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const response = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
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
    return Response.json(data)
}

/**
 * Proxy a DELETE request to the Flask backend.
 */
export async function proxyDelete(backendPath: string): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const response = await fetch(url, {
        method: 'DELETE',
        headers: {
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
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
