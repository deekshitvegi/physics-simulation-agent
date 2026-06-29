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
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 sm:p-5">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submit()
        }}
        placeholder="Describe a physics problem in plain English…  (Ctrl/⌘ + Enter to solve)"
        rows={3}
        className="w-full resize-y rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 outline-none placeholder:text-slate-500 focus:border-brand-500"
      />

      <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <ProviderSelector
          providers={providers}
          value={provider}
          onChange={onProviderChange}
          disabled={loading}
        />
        <button
          onClick={submit}
          disabled={loading || !text.trim()}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <>
              <Spinner /> Solving…
            </>
          ) : (
            'Solve'
          )}
        </button>
      </div>

      <div className="mt-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Try an example</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setText(ex)
                if (!loading) onSolve(ex)
              }}
              disabled={loading}
              className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1.5 text-left text-xs text-slate-300 transition-colors hover:border-brand-500 hover:text-white disabled:opacity-50"
            >
              {ex.length > 52 ? `${ex.slice(0, 52)}…` : ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function Spinner() {
  return (
    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
  )
}
