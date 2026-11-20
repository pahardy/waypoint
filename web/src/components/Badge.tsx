const STYLES = {
  official: { label: "OFFICIAL", className: "bg-accent text-night" },
  practice: { label: "PRACTICE", className: "bg-sky text-night" },
  "non-CA": { label: "NON-CANADIAN", className: "border border-muted text-muted" },
} as const;

/** A small label: official material, practice content or non-Canadian sources. */
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
