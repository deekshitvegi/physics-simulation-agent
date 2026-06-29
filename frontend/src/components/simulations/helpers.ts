import type { SimulationParams } from '../../lib/types'

export const SIM_HEIGHT = 360

export const COLORS = {
  bg: '#0b1220',
  grid: '#16203a',
  axis: '#334155',
  accent: '#818cf8',
  accent2: '#34d399',
  warn: '#f59e0b',
  danger: '#f472b6',
  text: '#cbd5e1',
  muted: '#64748b',
} as const

/** Read a numeric param with a fallback (handles nulls/strings/NaN). */
export function num(params: SimulationParams, key: string, dflt: number): number {
  const v = params[key]
  return typeof v === 'number' && Number.isFinite(v) ? v : dflt
}

export function clamp(x: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, x))
}
