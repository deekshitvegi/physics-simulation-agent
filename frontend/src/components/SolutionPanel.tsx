import type { Answer, SolveResponse } from '../lib/types'
import { Katex } from './Katex'

interface Props {
  result: SolveResponse
  answer: Answer
}

function formatValue(v: number): string {
  if (!Number.isFinite(v)) return '—'
  if (v !== 0 && (Math.abs(v) >= 1e5 || Math.abs(v) < 1e-3)) return v.toExponential(3)
  return Number(v.toFixed(4)).toString()
}

export function SolutionPanel({ result, answer }: Props) {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-fuchsia-400/30 bg-gradient-to-r from-violet-500/20 to-fuchsia-500/20 px-3 py-1 text-xs font-medium capitalize text-fuchsia-200">
          {result.domain}
        </span>
        <span className="text-sm text-violet-200/70">{result.equation_name}</span>
      </div>

      {/* Equation */}
      <div className="overflow-x-auto rounded-xl border border-white/10 bg-black/30 p-4 text-violet-50">
        <Katex expr={result.equation_latex} display />
      </div>

      {/* Answer */}
      <div className="relative overflow-hidden rounded-xl border border-fuchsia-400/20 bg-gradient-to-br from-violet-600/15 via-fuchsia-600/10 to-cyan-500/10 p-5">
        <div className="pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full bg-fuchsia-500/20 blur-2xl" />
        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-fuchsia-200/70">Answer</p>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-gradient font-display text-4xl font-bold">{formatValue(answer.value)}</span>
          <span className="text-lg text-violet-100/80">{answer.unit}</span>
        </div>
        {answer.latex && (
          <div className="mt-2 overflow-x-auto text-violet-200/80">
            <Katex expr={answer.latex} />
          </div>
        )}
      </div>

      {/* Steps */}
      <div>
        <h3 className="mb-3 font-display text-sm font-semibold text-violet-100">Step-by-step</h3>
        <ol className="space-y-2.5">
          {result.steps.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm text-violet-100/80">
              <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-[11px] font-semibold text-white">
                {i + 1}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Explanation */}
      {result.explanation && (
        <div>
          <h3 className="mb-2 font-display text-sm font-semibold text-violet-100">Explanation</h3>
          <p className="text-sm leading-relaxed text-violet-200/60">{result.explanation}</p>
        </div>
      )}
    </div>
  )
}
