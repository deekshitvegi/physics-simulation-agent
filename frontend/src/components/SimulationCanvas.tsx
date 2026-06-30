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
      <div className="panel grid h-[360px] place-items-center text-center text-sm text-violet-200/60">
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
      <div className="relative overflow-hidden rounded-2xl border border-white/10 shadow-glow-cyan">
        {/* gradient frame edge */}
        <div className="pointer-events-none absolute inset-0 z-10 rounded-2xl ring-1 ring-inset ring-white/5" />
        <Sim params={params} playing={playing} resetKey={resetKey} />
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button onClick={() => setPlaying((v) => !v)} className="btn-cosmic !px-4 !py-2">
          {playing ? '❚❚ Pause' : '▶ Play'}
        </button>
        <button
          onClick={() => {
            setResetKey((k) => k + 1)
            setPlaying(true)
          }}
          className="btn-ghost"
        >
          ↺ Reset
        </button>
        <span className="ml-auto font-mono text-[11px] uppercase tracking-[0.2em] text-violet-300/40">
          {type}
        </span>
      </div>
    </div>
  )
}
