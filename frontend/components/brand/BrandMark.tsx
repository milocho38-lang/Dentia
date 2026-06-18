export function BrandMark({
  compact = false,
  inverse = false,
}: {
  compact?: boolean;
  inverse?: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl shadow-sm ${
          inverse ? "bg-white/15" : "bg-gradient-to-br from-green-600 to-green-400"
        }`}
        aria-hidden="true"
      >
        <svg viewBox="0 0 40 40" className="h-8 w-8 text-white" fill="none">
          <path
            d="M11.2 11.4c2.6-3.2 6.1-2.7 8.8-.7 2.7-2 6.2-2.5 8.8.7 3 3.7 1.2 8.3-.1 12.8-1.2 4.2-2.3 8.4-5.1 8.4-2.1 0-1.3-7.2-3.6-7.2s-1.5 7.2-3.6 7.2c-2.8 0-3.9-4.2-5.1-8.4-1.3-4.5-3.1-9.1-.1-12.8Z"
            fill="currentColor"
          />
          <path
            d="M7 27.5c6.2-4.1 10.4-5.3 14.1-4.4 4.4 1.1 7.6.2 12-3.1-4.2 6.4-8.5 9.2-13.5 8-4.1-1-7.6-.4-12.6 2.6"
            stroke="white"
            strokeWidth="3.2"
            strokeLinecap="round"
          />
        </svg>
      </div>
      {!compact && (
        <div>
          <p
            className={`text-xl font-bold leading-none tracking-tight ${
              inverse ? "text-white" : "text-slate-900"
            }`}
          >
            Dentia
          </p>
          <p
            className={`mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${
              inverse ? "text-green-100" : "text-green-700"
            }`}
          >
            Gestión odontológica
          </p>
        </div>
      )}
    </div>
  );
}
