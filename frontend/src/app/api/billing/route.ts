import { NextRequest } from 'next/server'
import { proxyGet, proxyPost } from '../proxyUtils'

export async function GET(request: NextRequest) {
    return proxyGet('/api/billing/info', request)
}

export async function POST(request: NextRequest) {
    const body = await request.json()
    return proxyPost('/api/billing/switch-tier', body, request)
}
