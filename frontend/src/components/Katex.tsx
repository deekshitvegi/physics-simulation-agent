import { useMemo } from 'react'
import katex from 'katex'

interface KatexProps {
  expr: string
  display?: boolean
  className?: string
}

/** Renders a LaTeX string with KaTeX. Falls back to the raw string on error. */
export function Katex({ expr, display = false, className }: KatexProps) {
  const html = useMemo(() => {
    try {
      return katex.renderToString(expr, {
        displayMode: display,
        throwOnError: false,
        output: 'html',
      })
    } catch {
      return expr
    }
  }, [expr, display])

  return <span className={className} dangerouslySetInnerHTML={{ __html: html }} />
}
