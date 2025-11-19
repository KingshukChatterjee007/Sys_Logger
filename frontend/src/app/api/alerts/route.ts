import { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = 'http://localhost:5000/api/alerts';

    const response = await fetch(backendUrl, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      return new Response(response.statusText, { status: response.status });
    }

    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
}