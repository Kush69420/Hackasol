import type { CeilingRow, LegalViewData } from "./types";

const APPLICABILITY_LABELS = {
  applicable_primary: "Applicable Primary Provision",
  related: "Related Provision",
  conditional: "Conditional Provision",
  needs_legal_review: "Needs Legal Review (breach not established)",
} as const;

function amount(row: CeilingRow): string {
  if (row.statutory_maximum_inr_crore !== null) return `₹${row.statutory_maximum_inr_crore} crore`;
  return row.statutory_maximum_text ?? "no fixed figure";
}

export function LegalView({ legal, error }: { legal: LegalViewData | null; error: string | null }) {
  if (error) return <p className="callout" role="alert">{error}</p>;
  if (!legal) {
    return (
      <section id="legal" aria-label="Loading legal view" className="panel" aria-busy="true">
        <div className="panel-body"><div className="skeleton" style={{ height: "6rem" }} /></div>
      </section>
    );
  }
  const top = legal.highest_applicable_ceiling;
  return (
    <section id="legal" aria-label="Statutory Penalty Ceilings and Enforcement Timeline" data-testid="legal-view" className="panel">
      <header className="panel-head">
        <h2>Statutory Penalty Ceilings and Enforcement Timeline</h2>
        <p data-testid="ceiling-note">{legal.note}</p>
      </header>
      <div className="panel-body" style={{ paddingBottom: "0.75rem" }}>
        <p className="lede" data-testid="highest-ceiling">
          Highest applicable ceiling:{" "}
          <strong>{top ? `₹${top.amount_inr_crore} crore (${top.provisions.join(", ")})` : "none"}</strong>
        </p>
      </div>
      <div className="table-wrap" style={{ maxHeight: "none" }}>
        <table data-testid="ceiling-table">
          <thead>
            <tr>
              <th>Provision</th>
              <th>Schedule entry</th>
              <th>Statutory maximum</th>
              <th>Findings</th>
              <th>Severity mix</th>
            </tr>
          </thead>
          <tbody>
            {legal.ceilings.map((row) => (
              <tr key={row.provision} data-testid="ceiling-row">
                <td>{row.provision} ({row.citation})</td>
                <td>{row.schedule_entry ?? "none"}</td>
                <td className="num">{amount(row)}</td>
                <td>
                  {(Object.keys(APPLICABILITY_LABELS) as (keyof typeof APPLICABILITY_LABELS)[]).map((key) =>
                    row.finding_ids_by_applicability[key].length > 0 && (
                      <div key={key}>{APPLICABILITY_LABELS[key]}: {row.finding_ids_by_applicability[key].join(", ")}</div>
                    )
                  )}
                </td>
                <td>
                  {Object.entries(row.severity_mix)
                    .filter(([, n]) => n > 0)
                    .map(([band, n]) => `${band}: ${n}`)
                    .join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="panel-head" style={{ borderTop: "1px solid var(--line)", borderBottom: 0, paddingBottom: "0.5rem" }}>
        <h3 style={{ fontSize: "0.9375rem", color: "var(--ink)" }}>Enforcement timeline (relative to scan date {legal.as_of})</h3>
      </div>
      <ol className="timeline" data-testid="timeline">
        {legal.timeline.map((phase) => (
          <li key={phase.enforceable_from} data-testid="phase" data-enforceable={phase.already_enforceable}>
            <span className="when">
              {phase.enforceable_from}:{" "}
              <span className="state">
                {phase.already_enforceable ? "already enforceable" : `enforceable in ${phase.days_until} days`}
              </span>
            </span>
            <span>{phase.finding_ids.length} Finding(s): <span className="mono">{phase.finding_ids.join(", ")}</span></span>
          </li>
        ))}
      </ol>
    </section>
  );
}
