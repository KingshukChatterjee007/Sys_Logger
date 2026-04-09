import { NextRequest } from 'next/server'
import { proxyGet } from '../../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ orgId: string }> }
) {
    const { orgId } = await params
    const searchParams = request.nextUrl.searchParams
    const range = searchParams.get('range') || '7d'
    const token = request.headers.get('Authorization')
    
    return proxyGet(`/api/reports/org/${orgId}?range=${range}`, token)
}
