import { NextRequest } from 'next/server'
import { proxyGet } from '../proxyUtils'

export async function GET(req: NextRequest) {
    const token = req.headers.get('Authorization')
    return proxyGet('/api/usage', token)
}
