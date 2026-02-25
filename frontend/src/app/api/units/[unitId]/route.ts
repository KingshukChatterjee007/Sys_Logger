import { NextRequest } from 'next/server'

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'}/api/units/${unitId}`
    const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        cache: 'no-store'
    })
    const data = await response.json().catch(() => ({}))
    return Response.json(data, { status: response.status })
}

export async function PUT(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const body = await request.json()
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'}/api/units/${unitId}`
    const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    })
    const data = await response.json().catch(() => ({}))
    return Response.json(data, { status: response.status })
}

export async function DELETE(
    request: NextRequest,
    { params }: { params: Promise<{ unitId: string }> }
) {
    const { unitId } = await params
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5010'}/api/units/${unitId}`
    const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
    })
    const data = await response.json().catch(() => ({}))
    return Response.json(data, { status: response.status })
}
