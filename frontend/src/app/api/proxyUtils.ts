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

    const response = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
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
export async function proxyPost(backendPath: string, body?: unknown): Promise<Response> {
    const url = `${getBackendUrl()}${backendPath}`

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
