import { NextRequest } from 'next/server'
import { proxyGet } from '../../proxyUtils'

export async function GET(request: NextRequest) {
    return proxyGet('/api/admin/orgs', request)
}
