import { NextRequest } from 'next/server'
import { proxyPost } from '../proxyUtils'

export async function POST(req: NextRequest) {
    const body = await req.json()
    const token = req.headers.get('Authorization')
    return proxyPost('/api/users', body, token)
}
