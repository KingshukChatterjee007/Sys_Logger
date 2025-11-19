import { NextRequest } from 'next/server';

export async function POST(request: NextRequest, { params }: { params: Promise<{ alertId: string }> }) {
  try {
    const { alertId } = await params;

    if (!alertId) {
      return new Response('Alert ID is required', { status: 400 });
    }

    const backendUrl = `http://localhost:5000/api/alerts/${alertId}/acknowledge`;

    const response = await fetch(backendUrl, {
      method: 'POST',
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
    console.error('Error acknowledging alert:', error);
    return new Response('Internal Server Error', { status: 500 });
  }
}