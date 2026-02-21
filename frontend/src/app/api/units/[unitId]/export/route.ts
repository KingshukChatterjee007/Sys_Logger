import { NextRequest } from 'next/server'
import { getBackendUrl } from '../../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const { searchParams } = new URL(request.url)

    // Forward all query params (range, start_date, end_date)
    const queryString = searchParams.toString()
    const backendPath = `/api/units/${unitId}/export${queryString ? `?${queryString}` : ''}`
    const url = `${getBackendUrl()}${backendPath}`

    try {
        const response = await fetch(url, { cache: 'no-store' })

        if (!response.ok) {
            return new Response('Export failed', { status: response.status })
        }

        // Stream the CSV back to the client
        const csvData = await response.text()
        return new Response(csvData, {
            headers: {
                'Content-Type': 'text/csv',
                'Content-Disposition': response.headers.get('Content-Disposition') || `attachment; filename=${unitId}_export.csv`,
            },
        })
    } catch (error) {
        console.error('Export proxy error:', error)
        return new Response('Internal Server Error', { status: 500 })
    }
}
