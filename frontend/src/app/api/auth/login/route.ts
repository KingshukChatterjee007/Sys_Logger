import { proxyPost } from '../../proxyUtils'

export async function POST(request: Request) {
    const body = await request.json()
    return proxyPost('/api/auth/login', body)
}
