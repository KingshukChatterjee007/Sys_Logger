import { proxyGet } from '../proxyUtils'

export async function GET() {
    return proxyGet('/api/orgs')
}
