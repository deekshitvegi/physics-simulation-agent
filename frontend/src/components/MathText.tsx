import { Fragment, type ReactNode } from 'react'
import { Katex } from './Katex'

// Split on $$...$$ (display) or $...$ (inline) math segments.
const SEGMENT = /(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$)/g

function renderText(text: string, keyBase: string): ReactNode[] {
  // Bold via **...**
  return text.split(/(\*\*[^*]+\*\*)/g).map((chunk, i) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      return (
        <strong key={`${keyBase}-${i}`} className="font-semibold text-white">
          {chunk.slice(2, -2)}
        </strong>
      )
    }
    return (
      <span key={`${keyBase}-${i}`} className="whitespace-pre-wrap">
        {chunk}
      </span>
    )
  })
}

/** Renders an LLM reply: plain text + inline/display LaTeX math. */
export function MathText({ text }: { text: string }) {
  const parts = text.split(SEGMENT)
  return (
    <div className="text-sm leading-relaxed text-violet-50/90">
      {parts.map((part, i) => {
        if (part.startsWith('$$') && part.endsWith('$$')) {
          return (
            <div key={i} className="my-2 overflow-x-auto">
              <Katex expr={part.slice(2, -2).trim()} display />
            </div>
          )
        }
        if (part.length > 2 && part.startsWith('$') && part.endsWith('$')) {
          return <Katex key={i} expr={part.slice(1, -1).trim()} />
        }
        return <Fragment key={i}>{renderText(part, String(i))}</Fragment>
      })}
    </div>
  )
}
