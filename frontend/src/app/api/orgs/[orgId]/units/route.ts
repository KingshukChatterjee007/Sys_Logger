import { NextRequest } from 'next/server'
import { proxyGet } from '../../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ orgId: string }> }
) {
    const { orgId } = await params
    const token = request.headers.get('Authorization')
    return proxyGet(`/api/orgs/${orgId}/units`, token)
}
