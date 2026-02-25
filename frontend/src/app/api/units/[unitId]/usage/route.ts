import { NextRequest } from 'next/server'
import { proxyGet } from '../../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params

    // Manual proxying for consistency across methods
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'}/api/units/${unitId}/usage`
    const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store'
    })

    const data = await response.json().catch(() => ({}))
    return Response.json(data, { status: response.status })
}
