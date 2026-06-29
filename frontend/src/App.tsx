import { useEffect, useState } from 'react'
import { api, ApiError } from './lib/api'
import type { ProvidersResponse } from './lib/types'

type BackendState =
  | { status: 'checking' }
  | { status: 'online'; providers: ProvidersResponse }
  | { status: 'offline'; message: string }

export default function App() {
  const [backend, setBackend] = useState<BackendState>({ status: 'checking' })

  useEffect(() => {
    let cancelled = false
    api
      .providers()
      .then((providers) => {
        if (!cancelled) setBackend({ status: 'online', providers })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        const message = err instanceof ApiError ? err.message : 'Backend unavailable.'
        setBackend({ status: 'offline', message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-full">
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 text-lg">⚛️</span>
            <div>
              <h1 className="text-lg font-semibold leading-tight">Physics Simulation Agent</h1>
              <p className="text-xs text-slate-400">Solve problems symbolically · watch them simulate live</p>
            </div>
          </div>
          <BackendBadge backend={backend} />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-10">
        <div className="animate-fade-in rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center">
          <h2 className="text-xl font-semibold">Frontend scaffold ready</h2>
          <p className="mx-auto mt-2 max-w-xl text-sm text-slate-400">
            React + TypeScript + Tailwind are wired up and talking to the backend. The problem
            input, KaTeX solution panel, live p5.js simulations, and variable sliders are coming
            next.
          </p>
          {backend.status === 'online' && (
            <p className="mt-4 text-xs text-slate-500">
              Configured providers:{' '}
              {backend.providers.available.length > 0
                ? backend.providers.available.join(', ')
                : 'none yet — add an API key to backend/.env'}
            </p>
          )}
        </div>
      </main>
    </div>
  )
}

function BackendBadge({ backend }: { backend: BackendState }) {
  const map = {
    checking: { dot: 'bg-amber-400', label: 'Checking backend…' },
    online: { dot: 'bg-emerald-400', label: 'Backend online' },
    offline: { dot: 'bg-rose-500', label: 'Backend offline' },
  } as const
  const cfg = map[backend.status]
  return (
    <div
      className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs"
      title={backend.status === 'offline' ? backend.message : api.apiUrl}
    >
      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
      <span className="text-slate-300">{cfg.label}</span>
    </div>
  )
}
