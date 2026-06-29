import { useP5, type P5Sketch } from '../../hooks/useP5'
import type { SimProps } from '../../lib/types'
import { COLORS, SIM_HEIGHT, clamp, num } from './helpers'

const SPEED = 16 // px per (m/s)

const sketch: P5Sketch<SimProps> = (p, state, node) => {
  let cx1 = 0
  let cx2 = 0
  let collided = false
  let inited = false
  let lastReset = state.current.resetKey

  const trackY = () => p.height / 2 + 20

  function reset(w1: number, w2: number) {
    cx1 = 70 + w1 / 2
    cx2 = p.width - 70 - w2 / 2
    collided = false
  }

  p.setup = () => {
    p.createCanvas(node.clientWidth, SIM_HEIGHT)
    p.textFont('monospace')
  }
  p.windowResized = () => p.resizeCanvas(node.clientWidth, SIM_HEIGHT)

  p.draw = () => {
    const { params, playing, resetKey } = state.current
    const m1 = clamp(num(params, 'm1', 1), 0.1, 50)
    const m2 = clamp(num(params, 'm2', 1), 0.1, 50)
    const u1 = num(params, 'u1', 1)
    const u2 = num(params, 'u2', 0)
    const v1f = num(params, 'v1f', NaN)
    const v2f = num(params, 'v2f', NaN)
    const w1 = clamp(26 + 10 * Math.sqrt(m1), 26, 84)
    const w2 = clamp(26 + 10 * Math.sqrt(m2), 26, 84)

    if (!inited || resetKey !== lastReset) {
      reset(w1, w2)
      inited = true
      lastReset = resetKey
    }

    const v1 = collided && Number.isFinite(v1f) ? v1f : u1
    const v2 = collided && Number.isFinite(v2f) ? v2f : u2

    // collision detection (only while approaching)
    if (!collided && cx1 + w1 / 2 >= cx2 - w2 / 2 && u1 - u2 > 0) {
      collided = true
    }

    const y = trackY()
    p.background(COLORS.bg)

    // track
    p.stroke(COLORS.axis)
    p.strokeWeight(2)
    p.line(20, y + 26, p.width - 20, y + 26)

    // blocks
    p.rectMode(p.CENTER)
    p.noStroke()
    p.fill(COLORS.accent)
    p.rect(cx1, y, w1, w1, 4)
    p.fill(COLORS.danger)
    p.rect(cx2, y, w2, w2, 4)

    // mass labels
    p.fill('#0b1220')
    p.textSize(11)
    p.textAlign(p.CENTER, p.CENTER)
    p.text(`${m1}kg`, cx1, y)
    p.text(`${m2}kg`, cx2, y)

    // velocity labels
    p.textAlign(p.CENTER, p.BOTTOM)
    p.fill(COLORS.text)
    p.text(`${v1.toFixed(1)} m/s`, cx1, y - w1 / 2 - 6)
    p.text(`${v2.toFixed(1)} m/s`, cx2, y - w2 / 2 - 6)

    p.textAlign(p.LEFT, p.TOP)
    p.text(collided ? 'after collision' : 'approaching', 16, 12)

    if (playing) {
      const dt = p.deltaTime / 1000
      cx1 += v1 * SPEED * dt
      cx2 += v2 * SPEED * dt
      if (cx1 < -140 || cx1 > p.width + 140 || cx2 < -140 || cx2 > p.width + 140) {
        reset(w1, w2)
      }
    }
  }
}

export default function CollisionSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
