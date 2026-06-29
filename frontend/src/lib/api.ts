// Thin API client for the physics agent backend.
import type {
  DomainsResponse,
  ProvidersResponse,
  QuickSolveResponse,
  SolveResponse,
} from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(
      `Cannot reach the backend at ${API_URL}. Is it running? (uvicorn main:app --reload)`,
      0,
    )
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* keep default */
    }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  apiUrl: API_URL,

  health: () => request<{ status: string }>('/health'),

  providers: () => request<ProvidersResponse>('/api/providers'),

  domains: () => request<DomainsResponse>('/api/domains'),

  solve: (problem: string, provider?: string) =>
    request<SolveResponse>('/api/solve', {
      method: 'POST',
      body: JSON.stringify({ problem, provider: provider ?? null }),
    }),

  quickSolve: (equation_id: string, target: string, variables: Record<string, number>) =>
    request<QuickSolveResponse>('/api/solve/quick', {
      method: 'POST',
      body: JSON.stringify({ equation_id, target, variables }),
    }),
}
