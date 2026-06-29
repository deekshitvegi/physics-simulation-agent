import type p5 from 'p5'
import { useP5, type P5Sketch } from '../../hooks/useP5'
import type { SimProps } from '../../lib/types'
import { COLORS, SIM_HEIGHT, clamp, num } from './helpers'

function resistorBox(p: p5, x: number, y: number, w: number, label: string) {
  p.push()
  p.rectMode(p.CENTER)
  p.noFill()
  p.stroke(COLORS.warn)
  p.strokeWeight(2.5)
  p.rect(x, y, w, 22, 3)
  p.noStroke()
  p.fill(COLORS.text)
  p.textSize(11)
  p.textAlign(p.CENTER, p.CENTER)
  p.text(label, x, y - 0.5)
  p.pop()
}

const sketch: P5Sketch<SimProps> = (p, state, node) => {
  let flow = 0
  let lastReset = state.current.resetKey

  p.setup = () => {
    p.createCanvas(node.clientWidth, SIM_HEIGHT)
    p.textFont('monospace')
  }
  p.windowResized = () => p.resizeCanvas(node.clientWidth, SIM_HEIGHT)

  p.draw = () => {
    const { params, playing, resetKey } = state.current
    if (resetKey !== lastReset) {
      flow = 0
      lastReset = resetKey
    }

    const type = (params['circuitType'] as string) || 'single'
    const V = num(params, 'voltage', NaN)
    const I = num(params, 'current', NaN)
    const R = num(params, 'resistance', NaN)
    const r1 = num(params, 'r1', NaN)
    const r2 = num(params, 'r2', NaN)

    const left = 60
    const right = p.width - 60
    const top = 90
    const bottom = p.height - 70

    p.background(COLORS.bg)

    // wires (loop)
    p.stroke(COLORS.axis)
    p.strokeWeight(3)
    p.noFill()
    p.rect(left, top, right - left, bottom - top)

    // battery on the bottom edge
    const bx = (left + right) / 2
    p.stroke(COLORS.accent2)
    p.strokeWeight(3)
    p.line(bx - 10, bottom - 9, bx - 10, bottom + 9) // long (+)
    p.strokeWeight(6)
    p.line(bx + 6, bottom - 5, bx + 6, bottom + 5) // short (-)
    p.noStroke()
    p.fill(COLORS.muted)
    p.textSize(13)
    p.textAlign(p.CENTER, p.TOP)
    p.text('+   -', bx, bottom + 12)

    // resistor(s) on the top edge
    const midTopY = top
    if (type === 'series') {
      resistorBox(p, bx - 70, midTopY, 70, `R1 ${Number.isFinite(r1) ? r1 : '?'}`)
      resistorBox(p, bx + 70, midTopY, 70, `R2 ${Number.isFinite(r2) ? r2 : '?'}`)
    } else if (type === 'parallel') {
      resistorBox(p, bx, top + 46, 90, `R1 ${Number.isFinite(r1) ? r1 : '?'}`)
      resistorBox(p, bx, top + 92, 90, `R2 ${Number.isFinite(r2) ? r2 : '?'}`)
      // branch wires
      p.stroke(COLORS.axis)
      p.strokeWeight(3)
      p.line(bx - 100, top, bx - 100, top + 92)
      p.line(bx + 100, top, bx + 100, top + 92)
      p.line(bx - 100, top + 46, bx - 45, top + 46)
      p.line(bx + 45, top + 46, bx + 100, top + 46)
      p.line(bx - 100, top + 92, bx - 45, top + 92)
      p.line(bx + 45, top + 92, bx + 100, top + 92)
    } else {
      resistorBox(p, bx, midTopY, 90, `R ${Number.isFinite(R) ? R : '?'}`)
    }

    // animated current (dots around the loop)
    const perim = 2 * (right - left + bottom - top)
    const dots = 16
    const speed = Number.isFinite(I) ? clamp(I, 0.2, 8) : 1
    for (let i = 0; i < dots; i++) {
      const d = ((flow + (i * perim) / dots) % perim + perim) % perim
      const pt = pointOnLoop(d, left, right, top, bottom)
      p.noStroke()
      p.fill(COLORS.accent)
      p.circle(pt.x, pt.y, 6)
    }

    // labels
    p.noStroke()
    p.fill(COLORS.text)
    p.textSize(12)
    p.textAlign(p.LEFT, p.TOP)
    const totalR = Number.isFinite(R) ? R : type === 'series'
      ? (Number.isFinite(r1) && Number.isFinite(r2) ? r1 + r2 : NaN)
      : type === 'parallel' && Number.isFinite(r1) && Number.isFinite(r2)
        ? (r1 * r2) / (r1 + r2)
        : NaN
    const bits: string[] = [`${type} circuit`]
    if (Number.isFinite(V)) bits.push(`V = ${V}`)
    if (Number.isFinite(I)) bits.push(`I = ${I.toFixed(2)} A`)
    if (Number.isFinite(totalR)) bits.push(`R = ${totalR.toFixed(2)} ohm`)
    p.text(bits.join('    '), left, 14)

    if (playing) flow += (p.deltaTime / 1000) * speed * 60
  }
}

function pointOnLoop(d: number, left: number, right: number, top: number, bottom: number) {
  const w = right - left
  const h = bottom - top
  if (d < w) return { x: left + d, y: top } // top edge L->R
  d -= w
  if (d < h) return { x: right, y: top + d } // right edge
  d -= h
  if (d < w) return { x: right - d, y: bottom } // bottom edge
  d -= w
  return { x: left, y: bottom - d } // left edge
}

export default function CircuitSimulation({ params, playing, resetKey }: SimProps) {
  const ref = useP5<SimProps>(sketch, { params, playing, resetKey })
  return <div ref={ref} className="w-full overflow-hidden rounded-lg" />
}
