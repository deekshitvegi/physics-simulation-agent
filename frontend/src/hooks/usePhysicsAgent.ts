import { useCallback, useRef, useState } from 'react'
import { api, ApiError } from '../lib/api'
import type { Answer, SimulationParams, SolveResponse } from '../lib/types'

/**
 * Owns the solve lifecycle: the initial LLM-backed solve and the debounced,
 * LLM-free quick re-solve used while dragging variable sliders.
 */
export function usePhysicsAgent() {
  const [result, setResult] = useState<SolveResponse | null>(null)
  const [answer, setAnswer] = useState<Answer | null>(null)
  const [params, setParams] = useState<SimulationParams>({})
  const [values, setValues] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const resultRef = useRef<SolveResponse | null>(null)
  const valuesRef = useRef<Record<string, number>>({})
  const debounceRef = useRef<number | undefined>(undefined)

  const solve = useCallback(async (problem: string, provider?: string) => {
    setLoading(true)
    setError(null)
    try {
      const r = await api.solve(problem, provider)
      const v = Object.fromEntries(r.inputs.map((i) => [i.name, i.value]))
      resultRef.current = r
      valuesRef.current = v
      setResult(r)
      setAnswer(r.answer)
      setParams(r.simulation_params)
      setValues(v)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'Something went wrong.')
      setResult(null)
      setAnswer(null)
      setParams({})
    } finally {
      setLoading(false)
    }
  }, [])

  const updateVar = useCallback((name: string, value: number) => {
    const r = resultRef.current
    if (!r) return
    const v = { ...valuesRef.current, [name]: value }
    valuesRef.current = v
    setValues(v)

    window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(async () => {
      try {
        const q = await api.quickSolve(r.equation_id, r.target, valuesRef.current)
        setAnswer(q.answer)
        setParams(q.simulation_params)
      } catch {
        /* keep the last good state on transient slider-solve errors */
      }
    }, 70)
  }, [])

  return { result, answer, params, values, loading, error, solve, updateVar }
}
