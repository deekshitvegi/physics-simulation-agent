import { useEffect, useRef } from 'react'
import p5 from 'p5'

/**
 * Sketch function for a p5 instance. It is created once; live data flows in
 * through `state` (a ref whose `.current` is updated every React render) so the
 * sketch reads the latest params/playing/resetKey each frame without being
 * recreated. `node` is the container element (use it for responsive sizing).
 */
export type P5Sketch<S> = (p: p5, state: { current: S }, node: HTMLElement) => void

export function useP5<S>(sketch: P5Sketch<S>, state: S) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const stateRef = useRef<S>(state)
  stateRef.current = state

  useEffect(() => {
    const node = containerRef.current
    if (!node) return
    const instance = new p5((p) => sketch(p, stateRef, node), node)
    return () => instance.remove()
    // `sketch` is a stable module-level function; state flows via stateRef.
  }, [sketch])

  return containerRef
}
