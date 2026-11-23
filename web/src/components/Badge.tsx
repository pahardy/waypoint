const STYLES = {
  official: { label: "OFFICIAL", className: "bg-accent text-on-accent" },
  practice: { label: "PRACTICE", className: "bg-sky text-on-sky" },
  "non-CA": { label: "NON-CANADIAN", className: "border border-muted text-muted" },
  unverified: { label: "UNVERIFIED", className: "border border-accent text-accent" },
} as const;

/** A small label: official material, practice content, non-Canadian sources
 * or an exam fact not confirmed by Transport Canada. */
export default function Badge({ variant }: { variant: keyof typeof STYLES }) {
  const { label, className } = STYLES[variant];
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 font-mono text-xs font-semibold ${className}`}
    >
      {label}
    </span>
  );
}
