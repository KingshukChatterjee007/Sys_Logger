import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Try both ports 5000 and 5001 for compatibility
    const tryFetch = async (url: string): Promise<Response> => {
      return fetch(`${url}/api/units`, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
    }

    let response: Response | null = null

    // If NEXT_PUBLIC_API_URL is set, use it
    if (process.env.NEXT_PUBLIC_API_URL) {
      response = await tryFetch(process.env.NEXT_PUBLIC_API_URL)
    } else {
      // Try 5001 first, then fallback to 5000
      const ports = ['5001', '5000']
      for (const port of ports) {
        try {
          const apiUrl = `http://localhost:${port}`
          response = await tryFetch(apiUrl)
          if (response.ok) {
            break
          }
        } catch {
          continue
        }
      }
    }

    if (!response || !response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch units' },
        { status: response?.status || 500 }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching units:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}