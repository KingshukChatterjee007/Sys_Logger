import { NextRequest } from 'next/server'
import { proxyPost, proxyGet } from '../proxyUtils'

export async function POST(req: NextRequest) {
    const body = await req.json()
    const token = req.headers.get('Authorization')
    return proxyPost('/api/users', body, token)
}

export async function GET(req: NextRequest) {
    const token = req.headers.get('Authorization')
    const { searchParams } = new URL(req.url)
    const t = searchParams.get('t')
    const path = t ? `/api/users?t=${t}` : '/api/users'
    return proxyGet(path, token)
}
