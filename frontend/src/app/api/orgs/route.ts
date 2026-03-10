import { NextRequest } from 'next/server'
import { proxyGet, proxyPost } from '../proxyUtils'

export async function GET(req: NextRequest) {
    const token = req.headers.get('Authorization')
    return proxyGet('/api/orgs', token)
}

export async function POST(req: NextRequest) {
    const body = await req.json()
    const token = req.headers.get('Authorization')
    return proxyPost('/api/orgs', body, token)
}
