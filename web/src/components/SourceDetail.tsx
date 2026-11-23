import Badge from "@/components/Badge";
import type { Citation } from "@/lib/chat";

/** The cited passage: document, edition, section, page and its text. */
export default function SourceDetail({ citation }: { citation: Citation }) {
  return (
    <section
      aria-label={`Source detail: ${citation.label}`}
      className="mt-3 rounded border-l-4 border-airway bg-surface p-4"
    >
      <h3 className="font-display text-lg font-semibold">
        {citation.document_title}{" "}
        {citation.jurisdiction === "non-CA" && <Badge variant="non-CA" />}
      </h3>
      <dl className="mt-1 grid grid-cols-[auto_1fr] gap-x-3 text-sm">
        <dt className="text-muted">Edition</dt>
        <dd>{citation.edition}</dd>
        <dt className="text-muted">Section</dt>
        <dd className="font-mono">{citation.section_ref}</dd>
        {citation.page !== null && (
          <>
            <dt className="text-muted">Page</dt>
            <dd>{citation.page}</dd>
          </>
        )}
      </dl>
      <blockquote className="mt-3 whitespace-pre-wrap text-sm">{citation.text}</blockquote>
    </section>
  );
}
