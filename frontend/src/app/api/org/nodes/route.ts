import { NextRequest } from 'next/server'
import { proxyGet, proxyPost } from '../../proxyUtils'

export async function GET(request: NextRequest) {
    const { searchParams } = new URL(request.url)
    const orgSlug = searchParams.get('org_slug')
    const path = orgSlug ? `/api/org/nodes?org_slug=${orgSlug}` : '/api/org/nodes'
    return proxyGet(path, request)
}

export async function POST(request: NextRequest) {
    const body = await request.json()
    return proxyPost('/api/org/nodes/add', body, request)
}
