import { useP5, type P5Sketch } from '../../hooks/useP5'
import type { SimProps } from '../../lib/types'
import { COLORS, SIM_HEIGHT, clamp, num } from './helpers'

const sketch: P5Sketch<SimProps> = (p, state, node) => {
  let angle = 0
  let lastReset = state.current.resetKey

  p.setup = () => {
    p.createCanvas(node.clientWidth, SIM_HEIGHT)
    p.textFont('monospace')
  }
  p.windowResized = () => p.resizeCanvas(node.clientWidth, SIM_HEIGHT)

  p.draw = () => {
    const { params, playing, resetKey } = state.current
    if (resetKey !== lastReset) {
      angle = 0
      lastReset = resetKey
    }

    const M = num(params, 'mass', 5.972e24)
    const r = clamp(num(params, 'radius', 6.371e6), 1, 1e15)
    const v = num(params, 'velocity', NaN)

    const cx = p.width / 2
    const cy = p.height / 2
    const orbitR = Math.min(p.width, p.height) / 2 - 46
    const planetX = cx + orbitR * Math.cos(angle)
    const planetY = cy + orbitR * Math.sin(angle)

    p.background(COLORS.bg)

    // stars
    p.noStroke()
    p.fill(COLORS.grid)
    for (let i = 0; i < 40; i++) {
      const sx = (i * 97) % p.width
      const sy = (i * 53) % p.height
      p.circle(sx, sy, 1.5)
    }

    // orbit path
    p.noFill()
    p.stroke(COLORS.axis)
    p.strokeWeight(1)
    p.drawingContext.setLineDash([3, 5])
    p.circle(cx, cy, orbitR * 2)
    p.drawingContext.setLineDash([])

    // central body (glow)
    p.noStroke()
    for (let g = 26; g > 0; g -= 4) {
      p.fill(251, 191, 36, 18)
      p.circle(cx, cy, g * 2.2)
    }
    p.fill(COLORS.warn)
    p.circle(cx, cy, 30)

    // planet + velocity vector
    p.fill(COLORS.accent)
    p.circle(planetX, planetY, 16)
    if (Number.isFinite(v)) {
      const tx = -Math.sin(angle)
      const ty = Math.cos(angle)
      p.stroke(COLORS.accent2)
      p.strokeWeight(2)
      p.line(planetX, planetY, planetX + tx * 26, planetY + ty * 26)
      p.noStroke()
    }

    // labels
    p.fill(COLORS.text)
    p.textSize(12)
    p.textAlign(p.LEFT, p.TOP)
    p.text(`M = ${M.toExponential(2)} kg   r = ${r.toExponential(2)} m`, 14, 10)
    if (Number.isFinite(v)) {
      p.fill(COLORS.accent2)
      p.textAlign(p.RIGHT, p.TOP)
      p.text(`v = ${(v / 1000).toFixed(2)} km/s`, p.width - 14, 10)
    }

    if (playing) {
      const omega = Number.isFinite(v) ? clamp((v / r) * 600, 0.2, 2.5) : 0.7
      angle += (p.deltaTime / 1000) * omega
    }
  }
}

export default function OrbitalSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
