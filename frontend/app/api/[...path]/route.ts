import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  return proxyRequest(request, params.path, 'PATCH');
}

async function proxyRequest(
  request: NextRequest,
  pathParts: string[],
  method: string
) {
  const path = pathParts.join('/');
  const { searchParams } = new URL(request.url);
  const queryString = searchParams.toString();
  const url = `${BACKEND_URL}/api/${path}${queryString ? '?' + queryString : ''}`;
  
  // Debug logging for date filter issue
  if (path === 'transactions/filtered') {
    console.log('[Proxy Debug] Filtering request:', {
      queryString,
      startDate: searchParams.get('start_date'),
      endDate: searchParams.get('end_date'),
      fullUrl: url
    });
  }
  
  const headers = new Headers();
  
  // Copy relevant headers
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.set('authorization', authHeader);
  }
  
  const contentType = request.headers.get('content-type');
  if (contentType) {
    headers.set('content-type', contentType);
  }

  let body = null;
  if (method !== 'GET' && method !== 'DELETE') {
    if (contentType?.includes('application/json')) {
      body = await request.text();
    } else {
      body = await request.blob();
    }
  }

  try {
    const response = await fetch(url, {
      method,
      headers,
      body,
    });

    const responseData = await response.text();
    
    return new NextResponse(responseData, {
      status: response.status,
      headers: {
        'content-type': response.headers.get('content-type') || 'application/json',
      },
    });
  } catch (error) {
    console.error(`Proxy error for ${method} ${url}:`, error);
    return NextResponse.json(
      { error: 'Failed to connect to backend server' },
      { status: 503 }
    );
  }
}