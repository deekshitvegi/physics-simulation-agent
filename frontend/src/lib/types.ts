// Types mirroring the backend API responses.

export type SimulationType =
  | 'projectile'
  | 'pendulum'
  | 'wave'
  | 'circuit'
  | 'orbital'
  | 'collision'

export interface Answer {
  value: number
  unit: string
  expression: string
}

export interface InputVar {
  name: string
  value: number
  unit: string
}

export type SimulationParams = Record<string, number | string | null>

export interface SolveResponse {
  domain: string
  equation_id: string
  equation_name: string
  target: string
  variables: Record<string, number>
  inputs: InputVar[]
  equations: string[]
  answer: Answer
  simulation_type: SimulationType | null
  simulation_params: SimulationParams
  steps: string[]
  explanation: string
}

export interface QuickSolveResponse {
  equation_id: string
  target: string
  variables: Record<string, number>
  answer: Answer
  simulation_type: SimulationType | null
  simulation_params: SimulationParams
  steps: string[]
  equations: string[]
}

export interface ProvidersResponse {
  providers: string[]
  available: string[]
  default: string
}

export interface DomainInfo {
  id: string
  name: string
  description: string
}

export interface DomainsResponse {
  domains: DomainInfo[]
  simulations: string[]
}
