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
        <span className="rounded-full bg-brand-600/20 px-2.5 py-1 text-xs font-medium capitalize text-brand-300">
          {result.domain}
        </span>
        <span className="text-sm text-slate-400">{result.equation_name}</span>
      </div>

      {/* Equation */}
      <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/60 p-4">
        <Katex expr={result.equation_latex} display className="text-slate-100" />
      </div>

      {/* Answer */}
      <div className="rounded-lg border border-brand-700/50 bg-brand-600/10 p-4">
        <p className="text-xs uppercase tracking-wide text-brand-300">Answer</p>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-3xl font-bold text-white">{formatValue(answer.value)}</span>
          <span className="text-lg text-slate-300">{answer.unit}</span>
        </div>
        {answer.latex && (
          <div className="mt-2 overflow-x-auto text-slate-300">
            <Katex expr={answer.latex} />
          </div>
        )}
      </div>

      {/* Steps */}
      <div>
        <h3 className="mb-2 text-sm font-semibold text-slate-200">Step-by-step</h3>
        <ol className="space-y-2">
          {result.steps.map((step, i) => (
            <li key={i} className="flex gap-3 text-sm text-slate-300">
              <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-slate-800 text-xs text-slate-400">
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
          <h3 className="mb-2 text-sm font-semibold text-slate-200">Explanation</h3>
          <p className="text-sm leading-relaxed text-slate-400">{result.explanation}</p>
        </div>
      )}
    </div>
  )
}
