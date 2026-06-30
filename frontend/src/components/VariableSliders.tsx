import type { InputVar } from '../lib/types'

interface Props {
  inputs: InputVar[]
  values: Record<string, number>
  onChange: (name: string, value: number) => void
}

function rangeFor(input: InputVar, current: number): { min: number; max: number; step: number } {
  if (input.unit === 'deg') return { min: 0, max: 90, step: 1 }
  if (input.name === 'g') return { min: 0.5, max: 25, step: 0.1 }
  if (current === 0) return { min: -10, max: 10, step: 0.1 }
  if (current < 0) {
    const m = Math.abs(current) * 2
    return { min: -m, max: m, step: m / 200 }
  }
  const max = current * 2
  return { min: 0, max, step: max / 200 || 0.1 }
}

function fmt(v: number): string {
  if (v !== 0 && (Math.abs(v) >= 1e5 || Math.abs(v) < 1e-3)) return v.toExponential(2)
  return Number(v.toFixed(3)).toString()
}

export function VariableSliders({ inputs, values, onChange }: Props) {
  if (inputs.length === 0) return null

  return (
    <div className="panel p-5">
      <h3 className="mb-4 font-display text-sm font-semibold text-violet-100">
        Adjust variables{' '}
        <span className="font-sans font-normal text-violet-300/50">— the simulation updates live</span>
      </h3>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
        {inputs.map((input) => {
          const current = values[input.name] ?? input.value
          const { min, max, step } = rangeFor(input, current)
          return (
            <div key={input.name}>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="font-mono font-medium text-violet-100">{input.name}</span>
                <span className="font-mono tabular-nums text-cyan-300">
                  {fmt(current)} {input.unit}
                </span>
              </div>
              <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={current}
                onChange={(e) => onChange(input.name, Number(e.target.value))}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
