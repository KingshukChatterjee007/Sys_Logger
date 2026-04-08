import { getBackendUrl } from '../../proxyUtils'

export async function POST(request: Request) {
    const body = await request.json()
    const token = request.headers.get('Authorization')
    const url = `${getBackendUrl()}/api/units/generate-link`

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': token } : {})
        },
        body: JSON.stringify(body),
    })

    const data = await response.json().catch(() => ({}))
    
    if (response.ok && data.download_url) {
        const parts = data.download_url.split('/')
        const jwtToken = parts[parts.length - 1]
        data.download_url = `/api/units/installer/${jwtToken}`
    }

    return Response.json(data, { status: response.status })
}
