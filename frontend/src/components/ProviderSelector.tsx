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
      <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-violet-300/50">Model</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-white/10 bg-black/40 px-3 py-2 text-sm text-violet-50 outline-none transition-colors focus:border-fuchsia-400/50 disabled:opacity-50"
      >
        {all.length === 0 && <option value="">default</option>}
        {all.map((name) => (
          <option key={name} value={name} className="bg-deep text-violet-50">
            {LABELS[name] ?? name}
            {available.has(name) ? '' : ' (no key)'}
          </option>
        ))}
      </select>
    </label>
  )
}
