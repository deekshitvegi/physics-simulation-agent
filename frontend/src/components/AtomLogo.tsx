/** Custom animated atom/orbit logo mark with a cosmic gradient. */
export function AtomLogo({ className }: { className?: string }) {
  return (
    <span className={`relative inline-grid place-items-center ${className ?? ''}`}>
      <span className="absolute inset-0 rounded-full bg-nebula-fuchsia/30 blur-md animate-pulse-glow" />
      <svg viewBox="0 0 48 48" fill="none" className="relative h-full w-full">
        <defs>
          <linearGradient id="atomGrad" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
            <stop stopColor="#a78bfa" />
            <stop offset="0.5" stopColor="#e879f9" />
            <stop offset="1" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <g stroke="url(#atomGrad)" strokeWidth="1.6">
          <ellipse cx="24" cy="24" rx="20" ry="8" />
          <ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(60 24 24)" />
          <ellipse cx="24" cy="24" rx="20" ry="8" transform="rotate(120 24 24)" />
        </g>
        <circle cx="24" cy="24" r="3.4" fill="url(#atomGrad)" />
      </svg>
    </span>
  )
}
