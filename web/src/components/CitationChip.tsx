import type { Citation } from "@/lib/chat";

type Props = {
  citation: Citation;
  open: boolean;
  detailId: string;
  onToggle: () => void;
};

/** A citation in an answer. Selecting it opens or closes the source detail. */
export default function CitationChip({ citation, open, detailId, onToggle }: Props) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-expanded={open}
      aria-controls={detailId}
      aria-label={`Source: ${citation.label}`}
      className="mx-0.5 inline-flex min-h-11 items-center rounded border border-airway px-2 align-middle font-mono text-xs text-airway hover:bg-airway/10 sm:min-h-7"
    >
      {citation.label}
    </button>
  );
}
