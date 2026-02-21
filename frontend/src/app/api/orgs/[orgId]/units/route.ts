import { NextRequest } from 'next/server'
import { proxyGet } from '../../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ orgId: string }> }
) {
    const { orgId } = await params
    return proxyGet(`/api/orgs/${orgId}/units`)
}
