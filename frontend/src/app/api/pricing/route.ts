import { NextRequest } from 'next/server'
import { proxyGet, proxyPut } from '../proxyUtils'

export async function GET(req: NextRequest) {
    const token = req.headers.get('Authorization')
    return proxyGet('/api/pricing', token)
}

export async function PUT(req: NextRequest) {
    const token = req.headers.get('Authorization')
    const body = await req.json()
    return proxyPut('/api/pricing', body, token)
}
