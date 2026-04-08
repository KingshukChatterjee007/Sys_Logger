import { NextRequest } from 'next/server'
import { getBackendUrl } from '../../../proxyUtils'

export async function GET(request: NextRequest, { params }: { params: Promise<{ token: string }> }) {
    const { token } = await params
    const url = `${getBackendUrl()}/api/units/installer/${token}`

    const response = await fetch(url, {
        method: 'GET',
    })

    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch {
            errorData = { message: 'Failed to download installer' };
        }
        return Response.json(errorData, { status: response.status })
    }

    const blob = await response.blob()
    return new Response(blob, {
        headers: {
            'Content-Type': 'application/zip',
            'Content-Disposition': response.headers.get('Content-Disposition') || 'attachment; filename="installer.zip"'
        }
    })
}
