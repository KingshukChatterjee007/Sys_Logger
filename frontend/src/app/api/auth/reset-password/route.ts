import { NextRequest } from 'next/server'
import { proxyPost } from '../../proxyUtils'

export async function POST(request: NextRequest) {
    const body = await request.json()
    return proxyPost('/api/auth/reset-password', body, request)
}
