import type { SimulationParams } from '../../lib/types'

export const SIM_HEIGHT = 360

export const COLORS = {
  bg: '#0a0716',
  grid: '#241a45',
  axis: '#4c3a7a',
  accent: '#a78bfa', // violet
  accent2: '#22d3ee', // cyan
  warn: '#fbbf24',
  danger: '#e879f9', // fuchsia
  text: '#ddd6fe',
  muted: '#8b7fb8',
} as const

/** Read a numeric param with a fallback (handles nulls/strings/NaN). */
export function num(params: SimulationParams, key: string, dflt: number): number {
  const v = params[key]
  return typeof v === 'number' && Number.isFinite(v) ? v : dflt
}

export function clamp(x: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, x))
}
