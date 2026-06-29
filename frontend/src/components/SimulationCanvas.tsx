import { useState, type ComponentType } from 'react'
import type { SimulationParams, SimulationType } from '../lib/types'
import ProjectileSimulation from './simulations/ProjectileSimulation'
import PendulumSimulation from './simulations/PendulumSimulation'
import WaveSimulation from './simulations/WaveSimulation'
import CircuitSimulation from './simulations/CircuitSimulation'
import OrbitalSimulation from './simulations/OrbitalSimulation'
import CollisionSimulation from './simulations/CollisionSimulation'
import type { SimProps } from '../lib/types'

const REGISTRY: Record<SimulationType, ComponentType<SimProps>> = {
  projectile: ProjectileSimulation,
  pendulum: PendulumSimulation,
  wave: WaveSimulation,
  circuit: CircuitSimulation,
  orbital: OrbitalSimulation,
  collision: CollisionSimulation,
}

interface Props {
  type: SimulationType | null
  params: SimulationParams
}

export function SimulationCanvas({ type, params }: Props) {
  const [playing, setPlaying] = useState(true)
  const [resetKey, setResetKey] = useState(0)

  if (!type || !(type in REGISTRY)) {
    return (
      <div className="grid h-[360px] place-items-center rounded-lg border border-dashed border-slate-700 bg-slate-900/40 text-center text-sm text-slate-400">
        <p className="max-w-xs px-6">
          This result is solved exactly, but it doesn’t map to a visual simulation. The full
          step-by-step solution is on the left.
        </p>
      </div>
    )
  }

  const Sim = REGISTRY[type]

  return (
    <div>
      <div className="rounded-lg border border-slate-800 bg-[#0b1220]">
        <Sim params={params} playing={playing} resetKey={resetKey} />
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button
          onClick={() => setPlaying((v) => !v)}
          className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-500"
        >
          {playing ? '⏸ Pause' : '▶ Play'}
        </button>
        <button
          onClick={() => {
            setResetKey((k) => k + 1)
            setPlaying(true)
          }}
          className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition-colors hover:bg-slate-800"
        >
          ↺ Reset
        </button>
        <span className="ml-auto text-xs capitalize text-slate-500">{type} simulation</span>
      </div>
    </div>
  )
}
