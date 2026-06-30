import { useState } from 'react'
import type { ProvidersResponse } from '../lib/types'
import { ProviderSelector } from './ProviderSelector'

const EXAMPLES = [
  'A ball is thrown at 45° with initial velocity 20 m/s. How far does it travel?',
  'A pendulum is 2 meters long. What is its period?',
  'Two resistors of 4Ω and 6Ω are connected in parallel. What is the total resistance?',
  'A wave has frequency 440 Hz and wavelength 0.78 m. What is its speed?',
  'An ideal gas at 300K occupies 2L at 1atm. What volume at 600K and 2atm?',
  'What is the escape velocity from Earth?',
]

interface Props {
  onSolve: (problem: string) => void
  loading: boolean
  providers: ProvidersResponse | null
  provider: string
  onProviderChange: (value: string) => void
}

export function ProblemInput({ onSolve, loading, providers, provider, onProviderChange }: Props) {
  const [text, setText] = useState('')

  const submit = () => {
    const trimmed = text.trim()
    if (trimmed && !loading) onSolve(trimmed)
  }

  return (
    <div className="panel animate-fade-in p-4 sm:p-5">
      <div className="group relative rounded-xl">
        {/* gradient focus halo */}
        <div className="pointer-events-none absolute -inset-px rounded-xl bg-gradient-to-r from-violet-500/0 via-fuchsia-500/0 to-cyan-500/0 opacity-0 blur transition-opacity duration-300 group-focus-within:from-violet-500/40 group-focus-within:via-fuchsia-500/40 group-focus-within:to-cyan-500/40 group-focus-within:opacity-100" />
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit()
          }}
          placeholder="Describe a physics problem in plain English…  (Ctrl/⌘ + Enter to solve)"
          rows={3}
          className="relative w-full resize-y rounded-xl border border-white/10 bg-black/30 p-4 text-sm text-violet-50 outline-none placeholder:text-violet-300/40 focus:border-fuchsia-400/40"
        />
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <ProviderSelector
          providers={providers}
          value={provider}
          onChange={onProviderChange}
          disabled={loading}
        />
        <button onClick={submit} disabled={loading || !text.trim()} className="btn-cosmic">
          {loading ? (
            <>
              <Spinner /> Solving…
            </>
          ) : (
            <>Solve ✦</>
          )}
        </button>
      </div>

      <div className="mt-5">
        <p className="mb-2 font-mono text-[11px] uppercase tracking-[0.2em] text-violet-300/50">
          Try an example
        </p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setText(ex)
                if (!loading) onSolve(ex)
              }}
              disabled={loading}
              className="chip text-left disabled:opacity-50"
            >
              {ex.length > 50 ? `${ex.slice(0, 50)}…` : ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function Spinner() {
  return <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
}
