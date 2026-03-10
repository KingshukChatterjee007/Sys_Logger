import { NextRequest } from 'next/server'
import { proxyGet, proxyPut, proxyDelete } from '../../proxyUtils'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const token = request.headers.get('Authorization')
    return proxyGet(`/api/units/${unitId}`, token)
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const body = await request.json()
    const token = request.headers.get('Authorization')
    return proxyPut(`/api/units/${unitId}`, body, token)
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const token = request.headers.get('Authorization')
    return proxyDelete(`/api/units/${unitId}`, token)
}
