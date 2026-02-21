import { NextRequest } from 'next/server'
import { proxyPost } from '../../../proxyUtils'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ alertId: string }> }
) {
  const { alertId } = await params
  return proxyPost(`/api/alerts/${alertId}/acknowledge`)
}