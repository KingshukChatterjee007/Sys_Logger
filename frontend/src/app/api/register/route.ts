import { NextRequest } from 'next/server'
import { proxyPost } from '../proxyUtils'

export async function POST(request: NextRequest) {
    const body = await request.json()
    return proxyPost('/api/register-org', body, request)
}
