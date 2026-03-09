import { getBackendUrl } from '../../proxyUtils'

export async function POST(request: Request) {
    const body = await request.json()
    const token = request.headers.get('Authorization')
    const url = `${getBackendUrl()}/api/units/download-installer`

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': token } : {})
        },
        body: JSON.stringify(body),
    })

    if (!response.ok) {
        const data = await response.json().catch(() => ({ message: 'Failed to download installer' }))
        return Response.json(data, { status: response.status })
    }

    const blob = await response.blob()
    return new Response(blob, {
        headers: {
            'Content-Type': 'application/zip',
            'Content-Disposition': response.headers.get('Content-Disposition') || 'attachment; filename="installer.zip"'
        }
    })
}
