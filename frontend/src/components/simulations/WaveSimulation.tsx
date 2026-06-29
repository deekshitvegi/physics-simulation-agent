import { useP5, type P5Sketch } from '../../hooks/useP5'
import type { SimProps } from '../../lib/types'
import { COLORS, SIM_HEIGHT, clamp, num } from './helpers'

const sketch: P5Sketch<SimProps> = (p, state, node) => {
  let phase = 0
  let lastReset = state.current.resetKey

  p.setup = () => {
    p.createCanvas(node.clientWidth, SIM_HEIGHT)
    p.textFont('monospace')
  }
  p.windowResized = () => p.resizeCanvas(node.clientWidth, SIM_HEIGHT)

  p.draw = () => {
    const { params, playing, resetKey } = state.current
    if (resetKey !== lastReset) {
      phase = 0
      lastReset = resetKey
    }

    const f = clamp(num(params, 'frequency', 1), 0.01, 100000)
    const wavelength = clamp(num(params, 'wavelength', 1), 0.001, 100000)
    const speed = num(params, 'speed', f * wavelength)
    const amp = clamp(num(params, 'amplitude', 1) * 40, 20, p.height / 2 - 30)

    const margin = 24
    const midY = p.height / 2
    const lambdaPx = (p.width - 2 * margin) / 2.5
    const k = (2 * Math.PI) / lambdaPx

    p.background(COLORS.bg)

    // midline
    p.stroke(COLORS.axis)
    p.strokeWeight(1)
    p.line(margin, midY, p.width - margin, midY)

    // wave
    p.noFill()
    p.stroke(COLORS.accent)
    p.strokeWeight(2.5)
    p.beginShape()
    for (let x = margin; x <= p.width - margin; x += 3) {
      const y = midY - amp * Math.sin(k * (x - margin) - phase)
      p.vertex(x, y)
    }
    p.endShape()

    // wavelength marker
    p.stroke(COLORS.warn)
    p.strokeWeight(1.5)
    p.drawingContext.setLineDash([3, 4])
    p.line(margin, midY + amp + 14, margin + lambdaPx, midY + amp + 14)
    p.drawingContext.setLineDash([])
    p.noStroke()
    p.fill(COLORS.warn)
    p.textSize(11)
    p.textAlign(p.CENTER, p.TOP)
    p.text('1 wavelength', margin + lambdaPx / 2, midY + amp + 18)

    // oscillating source dot
    p.fill(COLORS.danger)
    p.circle(margin, midY - amp * Math.sin(-phase), 12)

    // labels
    p.fill(COLORS.text)
    p.textSize(12)
    p.textAlign(p.LEFT, p.TOP)
    p.text(`f = ${f} Hz   lambda = ${wavelength} m`, margin, 8)
    p.fill(COLORS.accent2)
    p.textAlign(p.RIGHT, p.TOP)
    p.text(`Speed ${speed.toFixed(2)} m/s`, p.width - margin, 8)

    if (playing) {
      const visualHz = clamp(f / 100, 0.15, 2.5)
      phase += (p.deltaTime / 1000) * visualHz * 2 * Math.PI
    }
  }
}

export default function WaveSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
