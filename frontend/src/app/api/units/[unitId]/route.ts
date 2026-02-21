import { NextRequest } from 'next/server'
import { proxyGet } from '../../proxyUtils'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ unitId: string }> }
) {
  const { unitId } = await params
  return proxyGet(`/api/units/${unitId}/usage`)
}