import { useEffect, useState, type ReactNode } from 'react'
import { api } from './lib/api'
import type { ProvidersResponse } from './lib/types'
import { usePhysicsAgent } from './hooks/usePhysicsAgent'
import { ProblemInput } from './components/ProblemInput'
import { SolutionPanel } from './components/SolutionPanel'
import { SimulationCanvas } from './components/SimulationCanvas'
import { VariableSliders } from './components/VariableSliders'
import { AtomLogo } from './components/AtomLogo'

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
    <div className="relative z-10 min-h-full">
      {/* drifting nebula orbs */}
      <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -left-32 top-10 h-80 w-80 rounded-full bg-nebula-violet/20 blur-3xl animate-float" />
        <div className="absolute right-0 top-40 h-72 w-72 rounded-full bg-nebula-fuchsia/15 blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-nebula-cyan/15 blur-3xl animate-float" />
      </div>

      <header className="sticky top-0 z-20 border-b border-white/5 bg-void/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <AtomLogo className="h-10 w-10" />
            <div>
              <h1 className="font-display text-base font-bold leading-tight sm:text-lg">
                Physics <span className="text-gradient">Simulation</span> Agent
              </h1>
              <p className="hidden text-xs text-violet-300/60 sm:block">
                Solve symbolically · simulate the universe live
              </p>
            </div>
          </div>
          <StatusBadge online={online} />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {!result && !error && (
          <div className="mb-8 text-center animate-fade-in">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-5xl">
              Ask physics <span className="text-gradient animate-gradient-x">anything</span>
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-sm text-violet-200/70 sm:text-base">
              Plain-English problems, solved exactly with SymPy, brought to life as interactive
              simulations you can tweak in real time.
            </p>
          </div>
        )}

        <ProblemInput
          onSolve={(p) => solve(p, provider || undefined)}
          loading={loading}
          providers={providers}
          provider={provider}
          onProviderChange={setProvider}
        />

        {online === false && (
          <Banner tone="warn">
            Backend offline at <code className="font-mono">{api.apiUrl}</code>. Start it with{' '}
            <code className="font-mono">uvicorn main:app --reload</code> in <code className="font-mono">backend/</code>.
          </Banner>
        )}

        {error && <Banner tone="error">{error}</Banner>}

        {result && answer && (
          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="panel animate-fade-in p-5 sm:p-6">
              <SolutionPanel result={result} answer={answer} />
            </section>
            <section className="animate-fade-in space-y-4">
              <SimulationCanvas type={result.simulation_type} params={params} />
              <VariableSliders inputs={result.inputs} values={values} onChange={updateVar} />
            </section>
          </div>
        )}
      </main>

      <footer className="relative z-10 mx-auto max-w-6xl px-4 py-10 text-center text-xs text-violet-300/40">
        Answers computed symbolically with SymPy · model-agnostic LLM layer
      </footer>
    </div>
  )
}

function StatusBadge({ online }: { online: boolean | null }) {
  const cfg =
    online === null
      ? { dot: 'bg-amber-400', ring: 'shadow-[0_0_8px_2px_rgba(251,191,36,0.6)]', label: 'Connecting…' }
      : online
        ? { dot: 'bg-emerald-400', ring: 'shadow-[0_0_8px_2px_rgba(52,211,153,0.6)]', label: 'Online' }
        : { dot: 'bg-rose-500', ring: 'shadow-[0_0_8px_2px_rgba(244,63,94,0.6)]', label: 'Offline' }
  return (
    <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs backdrop-blur">
      <span className={`h-2 w-2 rounded-full ${cfg.dot} ${cfg.ring}`} />
      <span className="hidden text-violet-100 sm:inline">{cfg.label}</span>
    </div>
  )
}

function Banner({ tone, children }: { tone: 'warn' | 'error'; children: ReactNode }) {
  const styles =
    tone === 'error'
      ? 'border-rose-500/30 bg-rose-500/10 text-rose-200'
      : 'border-amber-500/30 bg-amber-500/10 text-amber-200'
  return (
    <div className={`mt-5 rounded-xl border px-4 py-3 text-sm backdrop-blur ${styles}`}>{children}</div>
  )
}
