import { useEffect, useState, type ReactNode } from 'react'
import { api } from './lib/api'
import type { ProvidersResponse } from './lib/types'
import { usePhysicsAgent } from './hooks/usePhysicsAgent'
import { ProblemInput } from './components/ProblemInput'
import { SolutionPanel } from './components/SolutionPanel'
import { SimulationCanvas } from './components/SimulationCanvas'
import { VariableSliders } from './components/VariableSliders'

export default function App() {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null)
  const [provider, setProvider] = useState('')
  const [online, setOnline] = useState<boolean | null>(null)

  const { result, answer, params, values, loading, error, solve, updateVar } = usePhysicsAgent()

  useEffect(() => {
    let cancelled = false
    api
      .providers()
      .then((p) => {
        if (cancelled) return
        setProviders(p)
        setProvider(p.available[0] ?? p.default ?? '')
        setOnline(true)
      })
      .catch(() => {
        if (!cancelled) setOnline(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 text-lg">⚛️</span>
            <div>
              <h1 className="text-base font-semibold leading-tight sm:text-lg">Physics Simulation Agent</h1>
              <p className="hidden text-xs text-slate-400 sm:block">
                Solve problems symbolically · watch them simulate live
              </p>
            </div>
          </div>
          <StatusBadge online={online} />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <ProblemInput
          onSolve={(p) => solve(p, provider || undefined)}
          loading={loading}
          providers={providers}
          provider={provider}
          onProviderChange={setProvider}
        />

        {online === false && (
          <Banner tone="warn">
            Backend offline at <code>{api.apiUrl}</code>. Start it with{' '}
            <code>uvicorn main:app --reload</code> in the <code>backend/</code> folder.
          </Banner>
        )}

        {error && <Banner tone="error">{error}</Banner>}

        {result && answer && (
          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="animate-fade-in rounded-xl border border-slate-800 bg-slate-900/40 p-5">
              <SolutionPanel result={result} answer={answer} />
            </section>
            <section className="animate-fade-in space-y-4">
              <SimulationCanvas type={result.simulation_type} params={params} />
              <VariableSliders inputs={result.inputs} values={values} onChange={updateVar} />
            </section>
          </div>
        )}

        {!result && !error && (
          <p className="mt-10 text-center text-sm text-slate-500">
            Enter a problem above or pick an example to get started.
          </p>
        )}
      </main>

      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-slate-600">
        Answers computed symbolically with SymPy · model-agnostic LLM layer
      </footer>
    </div>
  )
}

function StatusBadge({ online }: { online: boolean | null }) {
  const cfg =
    online === null
      ? { dot: 'bg-amber-400', label: 'Connecting…' }
      : online
        ? { dot: 'bg-emerald-400', label: 'Backend online' }
        : { dot: 'bg-rose-500', label: 'Backend offline' }
  return (
    <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs">
      <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
      <span className="hidden text-slate-300 sm:inline">{cfg.label}</span>
    </div>
  )
}

function Banner({ tone, children }: { tone: 'warn' | 'error'; children: ReactNode }) {
  const styles =
    tone === 'error'
      ? 'border-rose-800/60 bg-rose-950/40 text-rose-200'
      : 'border-amber-800/60 bg-amber-950/30 text-amber-200'
  return <div className={`mt-4 rounded-lg border px-4 py-3 text-sm ${styles}`}>{children}</div>
}
