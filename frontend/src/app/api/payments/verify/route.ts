import { NextRequest } from 'next/server'
import { proxyPost } from '../../proxyUtils'

export async function POST(req: NextRequest) {
    const token = req.headers.get('Authorization')
    const body = await req.json()
    return proxyPost('/api/payments/verify', body, token)
}
