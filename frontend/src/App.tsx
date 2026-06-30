import { useEffect, useRef, useState } from 'react'
import { api, ApiError } from './lib/api'
import type { ChatMessage, ProvidersResponse } from './lib/types'
import { ProviderSelector } from './components/ProviderSelector'
import { SimulationCanvas } from './components/SimulationCanvas'
import { MathText } from './components/MathText'
import { AtomLogo } from './components/AtomLogo'

const EXAMPLES = [
  'A ball is thrown at 30° with 25 m/s. How far does it travel? Show me the simulation.',
  'A source emits 492 Hz; a car approaches at 2 m/s and reflects it. What is the beat frequency?',
  'What is the escape velocity from Earth, and show the orbit?',
  'Why do resistors in parallel have lower total resistance? Give an example.',
]

export default function App() {
  const [providers, setProviders] = useState<ProvidersResponse | null>(null)
  const [provider, setProvider] = useState('')
  const [online, setOnline] = useState<boolean | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    api
      .providers()
      .then((p) => {
        setProviders(p)
        setProvider(p.available[0] ?? p.default ?? '')
        setOnline(true)
      })
      .catch(() => setOnline(false))
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    const history: ChatMessage[] = [...messages, { role: 'user', content: trimmed }]
    setMessages(history)
    setInput('')
    setLoading(true)
    try {
      const res = await api.chat(
        history.map((m) => ({ role: m.role, content: m.content })),
        provider || undefined,
      )
      setMessages([...history, { role: 'assistant', content: res.reply, artifacts: res.artifacts }])
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Something went wrong.'
      setMessages([...history, { role: 'assistant', content: `⚠️ ${msg}` }])
    } finally {
      setLoading(false)
    }
  }

  const empty = messages.length === 0

  return (
    <div className="relative z-10 flex h-full flex-col">
      <div aria-hidden className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -left-32 top-10 h-80 w-80 rounded-full bg-nebula-violet/20 blur-3xl animate-float" />
        <div className="absolute right-0 top-40 h-72 w-72 rounded-full bg-nebula-fuchsia/15 blur-3xl animate-pulse-glow" />
        <div className="absolute bottom-0 left-1/3 h-72 w-72 rounded-full bg-nebula-cyan/15 blur-3xl animate-float" />
      </div>

      <header className="z-20 shrink-0 border-b border-white/5 bg-void/50 backdrop-blur-xl">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <AtomLogo className="h-9 w-9" />
            <div>
              <h1 className="font-display text-base font-bold leading-tight">
                Physics <span className="text-gradient">Tutor</span> Agent
              </h1>
              <p className="hidden text-xs text-violet-300/60 sm:block">
                Chat · exact math via SymPy · live simulations
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ProviderSelector providers={providers} value={provider} onChange={setProvider} disabled={loading} />
            <StatusDot online={online} />
          </div>
        </div>
      </header>

      <div className="z-10 flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6">
          {empty ? (
            <Hero onPick={send} disabled={online === false} />
          ) : (
            <div className="space-y-5">
              {messages.map((m, i) => (
                <Bubble key={i} message={m} />
              ))}
              {loading && <Thinking />}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="z-20 shrink-0 border-t border-white/5 bg-void/60 backdrop-blur-xl">
        <div className="mx-auto max-w-3xl px-4 py-3">
          {online === false && (
            <p className="mb-2 text-center text-xs text-rose-300">
              Backend offline at <code className="font-mono">{api.apiUrl}</code> — start it with{' '}
              <code className="font-mono">uvicorn main:app --reload</code>.
            </p>
          )}
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  send(input)
                }
              }}
              rows={1}
              placeholder="Ask a physics or math question…  (Enter to send, Shift+Enter for a new line)"
              className="max-h-40 min-h-[44px] flex-1 resize-none rounded-xl border border-white/10 bg-black/30 p-3 text-sm text-violet-50 outline-none placeholder:text-violet-300/40 focus:border-fuchsia-400/40"
            />
            <button onClick={() => send(input)} disabled={loading || !input.trim()} className="btn-cosmic h-[44px]">
              {loading ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Hero({ onPick, disabled }: { onPick: (t: string) => void; disabled: boolean }) {
  return (
    <div className="animate-fade-in py-10 text-center">
      <AtomLogo className="mx-auto mb-5 h-16 w-16" />
      <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
        Ask physics <span className="text-gradient animate-gradient-x">anything</span>
      </h2>
      <p className="mx-auto mt-3 max-w-md text-sm text-violet-200/70">
        I tutor step by step, compute every number exactly with SymPy, and bring problems to life
        as live simulations.
      </p>
      <div className="mx-auto mt-6 grid max-w-2xl grid-cols-1 gap-2 sm:grid-cols-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => onPick(ex)}
            disabled={disabled}
            className="chip text-left disabled:opacity-50"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}

function Bubble({ message }: { message: ChatMessage }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm border border-fuchsia-400/20 bg-gradient-to-br from-violet-600/25 to-fuchsia-600/20 px-4 py-2.5 text-sm text-violet-50">
          <span className="whitespace-pre-wrap">{message.content}</span>
        </div>
      </div>
    )
  }
  return (
    <div className="flex gap-3">
      <AtomLogo className="mt-1 h-7 w-7 shrink-0" />
      <div className="min-w-0 flex-1 space-y-3">
        <div className="panel px-4 py-3">
          <MathText text={message.content} />
        </div>
        {message.artifacts?.map((art, i) => (
          <SimulationCanvas key={i} type={art.simulation_type} params={art.simulation_params} />
        ))}
      </div>
    </div>
  )
}

function Thinking() {
  return (
    <div className="flex gap-3">
      <AtomLogo className="mt-1 h-7 w-7 shrink-0" />
      <div className="panel flex items-center gap-1.5 px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 animate-pulse rounded-full bg-fuchsia-400"
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
      </div>
    </div>
  )
}

function StatusDot({ online }: { online: boolean | null }) {
  const dot = online === null ? 'bg-amber-400' : online ? 'bg-emerald-400' : 'bg-rose-500'
  return (
    <span
      className={`h-2.5 w-2.5 rounded-full ${dot}`}
      title={online === false ? 'Backend offline' : online ? 'Online' : 'Connecting…'}
    />
  )
}
