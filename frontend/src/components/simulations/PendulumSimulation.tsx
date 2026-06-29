import { useP5, type P5Sketch } from '../../hooks/useP5'
import type { SimProps } from '../../lib/types'
import { COLORS, SIM_HEIGHT, clamp, num } from './helpers'

const sketch: P5Sketch<SimProps> = (p, state, node) => {
  let t = 0
  let lastReset = state.current.resetKey

  p.setup = () => {
    p.createCanvas(node.clientWidth, SIM_HEIGHT)
    p.textFont('monospace')
  }
  p.windowResized = () => p.resizeCanvas(node.clientWidth, SIM_HEIGHT)

  p.draw = () => {
    const { params, playing, resetKey } = state.current
    if (resetKey !== lastReset) {
      t = 0
      lastReset = resetKey
    }

    const L = clamp(num(params, 'length', 1), 0.05, 100)
    const g = clamp(num(params, 'g', 9.81), 0.1, 100)
    const amp = (clamp(num(params, 'angle', 30), 3, 85) * Math.PI) / 180
    const omega = Math.sqrt(g / L)
    const period = (2 * Math.PI) / omega

    const pivotX = p.width / 2
    const pivotY = 40
    const avail = p.height - pivotY - 50
    const lengthPx = clamp((L / 3) * avail, 40, avail)
    const theta = amp * Math.cos(omega * t)
    const bobX = pivotX + lengthPx * Math.sin(theta)
    const bobY = pivotY + lengthPx * Math.cos(theta)

    p.background(COLORS.bg)

    // swing arc
    p.noFill()
    p.stroke(COLORS.grid)
    p.strokeWeight(1.5)
    p.arc(pivotX, pivotY, lengthPx * 2, lengthPx * 2, Math.PI / 2 - amp, Math.PI / 2 + amp)

    // pivot
    p.noStroke()
    p.fill(COLORS.axis)
    p.circle(pivotX, pivotY, 10)

    // rod + bob
    p.stroke(COLORS.accent)
    p.strokeWeight(3)
    p.line(pivotX, pivotY, bobX, bobY)
    p.noStroke()
    p.fill(COLORS.danger)
    p.circle(bobX, bobY, 26)

    // labels
    p.fill(COLORS.text)
    p.textSize(12)
    p.textAlign(p.LEFT, p.TOP)
    p.text(`L = ${L.toFixed(2)} m   g = ${g.toFixed(2)}`, 14, 8)
    p.fill(COLORS.accent2)
    p.textAlign(p.RIGHT, p.TOP)
    p.text(`Period ${period.toFixed(2)} s`, p.width - 14, 8)

    if (playing) t += p.deltaTime / 1000
  }
}

export default function PendulumSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
