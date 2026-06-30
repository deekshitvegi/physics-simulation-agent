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
  latex?: string
}

// Props shared by every p5.js simulation component.
export interface SimProps {
  params: SimulationParams
  playing: boolean
  resetKey: number
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
  equation_latex: string
  answer: Answer
  simulation_type: SimulationType | null
  simulation_params: SimulationParams
  steps: string[]
  derivation: string[]
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
  derivation: string[]
  equations: string[]
  equation_latex: string
}

export interface ProvidersResponse {
  providers: string[]
  available: string[]
  default: string
}

// --- Tutor chat ---
export interface ChatSimArtifact {
  type: 'simulation'
  simulation_type: SimulationType
  simulation_params: SimulationParams
}

export interface ChatResponse {
  reply: string
  artifacts: ChatSimArtifact[]
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  artifacts?: ChatSimArtifact[]
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
