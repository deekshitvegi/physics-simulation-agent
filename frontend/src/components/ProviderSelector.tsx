import type { ProvidersResponse } from '../lib/types'

const LABELS: Record<string, string> = {
  gemini: 'Gemini',
  groq: 'Llama 3.3 (Groq)',
  mistral: 'Mistral',
  claude: 'Claude',
  openai: 'OpenAI',
}

interface Props {
  providers: ProvidersResponse | null
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}

export function ProviderSelector({ providers, value, onChange, disabled }: Props) {
  const all = providers?.providers ?? []
  const available = new Set(providers?.available ?? [])

  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="text-slate-400">Model</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100 outline-none focus:border-brand-500 disabled:opacity-50"
      >
        {all.length === 0 && <option value="">default</option>}
        {all.map((name) => (
          <option key={name} value={name}>
            {LABELS[name] ?? name}
            {available.has(name) ? '' : ' (no key)'}
          </option>
        ))}
      </select>
    </label>
  )
}
