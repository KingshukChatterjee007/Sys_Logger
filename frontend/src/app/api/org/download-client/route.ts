import { NextRequest } from 'next/server'
import { proxyPost } from '../../proxyUtils'

export async function POST(request: NextRequest) {
    const body = await request.json()
    return proxyPost('/api/org/download-client', body, request)
}
