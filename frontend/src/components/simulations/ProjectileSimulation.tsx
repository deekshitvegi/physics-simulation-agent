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

    const v0 = clamp(num(params, 'v0', 20), 0.1, 1000)
    const angle = clamp(num(params, 'angle', 45), 1, 89)
    const g = clamp(num(params, 'g', 9.81), 0.1, 100)
    const rad = (angle * Math.PI) / 180
    const vx = v0 * Math.cos(rad)
    const vy = v0 * Math.sin(rad)
    const flight = (2 * vy) / g
    const range = vx * flight
    const apex = (vy * vy) / (2 * g)

    const mL = 46
    const mR = 18
    const mT = 26
    const mB = 34
    const groundY = p.height - mB
    const scale = Math.min(
      (p.width - mL - mR) / Math.max(range, 0.001),
      (groundY - mT) / Math.max(apex, 0.001),
    )
    const toX = (x: number) => mL + x * scale
    const toY = (y: number) => groundY - y * scale

    p.background(COLORS.bg)

    // ground
    p.stroke(COLORS.axis)
    p.strokeWeight(2)
    p.line(mL, groundY, p.width - mR, groundY)

    // trajectory path (dashed)
    p.noFill()
    p.stroke(COLORS.accent)
    p.strokeWeight(1.5)
    p.drawingContext.setLineDash([4, 5])
    p.beginShape()
    for (let i = 0; i <= 80; i++) {
      const tt = (flight * i) / 80
      const y = vy * tt - 0.5 * g * tt * tt
      p.vertex(toX(vx * tt), toY(Math.max(0, y)))
    }
    p.endShape()
    p.drawingContext.setLineDash([])

    // launch angle vector
    p.stroke(COLORS.warn)
    p.strokeWeight(2.5)
    p.line(toX(0), toY(0), toX(0) + Math.cos(rad) * 38, toY(0) - Math.sin(rad) * 38)

    // projectile
    const x = vx * t
    const y = Math.max(0, vy * t - 0.5 * g * t * t)
    p.noStroke()
    p.fill(COLORS.danger)
    p.circle(toX(x), toY(y), 15)

    // labels
    p.noStroke()
    p.fill(COLORS.text)
    p.textSize(12)
    p.textAlign(p.LEFT, p.TOP)
    p.text(`v0 = ${v0.toFixed(1)} m/s   angle = ${angle.toFixed(0)}deg   g = ${g.toFixed(2)}`, mL, 6)
    p.fill(COLORS.accent2)
    p.textAlign(p.RIGHT, p.TOP)
    p.text(`Range ${range.toFixed(1)} m`, p.width - mR, 6)
    p.text(`Apex ${apex.toFixed(1)} m`, p.width - mR, 22)

    if (playing) {
      t += (p.deltaTime / 1000) * (flight / 2.5)
      if (t > flight) t = 0
    }
  }
}

export default function ProjectileSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
