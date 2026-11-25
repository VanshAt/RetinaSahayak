const API_BASE = '/api/v1';

export function getStoredToken(): string | null {
  return localStorage.getItem('retinasahayak_token');
}

export function setStoredToken(token: string | null) {
  if (token) {
    localStorage.setItem('retinasahayak_token', token);
  } else {
    localStorage.removeItem('retinasahayak_token');
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ success: boolean; data?: T; error?: any }> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Do not set Content-Type for FormData (browser does it automatically with boundary)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401) {
      setStoredToken(null);
    }

    const data = await res.json();
    return data;
  } catch (err: any) {
    return {
      success: false,
      error: { message: err?.message || 'Network request failed' }
    };
  }
}
