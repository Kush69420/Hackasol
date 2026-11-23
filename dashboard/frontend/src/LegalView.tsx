import { useEffect, useState } from "react";

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

export function LegalView({ runId }: { runId: string }) {
  const [legal, setLegal] = useState<LegalViewData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/api/scans/${runId}/legal`)
      .then(async (response) => {
        if (!response.ok) throw new Error(`Legal view unavailable (${response.status})`);
        const body = (await response.json()) as LegalViewData;
        if (!cancelled) setLegal(body);
      })
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (error) return <p className="failed" role="alert">{error}</p>;
  if (!legal) return null;
  const top = legal.highest_applicable_ceiling;
  return (
    <section aria-label="Statutory Penalty Ceilings and Enforcement Timeline" data-testid="legal-view">
      <h2>Statutory Penalty Ceilings and Enforcement Timeline</h2>
      <p data-testid="ceiling-note">{legal.note}</p>
      <p data-testid="highest-ceiling">
        Highest applicable ceiling:{" "}
        {top ? `₹${top.amount_inr_crore} crore (${top.provisions.join(", ")})` : "none"}
      </p>
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
              <td>{amount(row)}</td>
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
      <h3>Enforcement timeline (relative to scan date {legal.as_of})</h3>
      <ol data-testid="timeline">
        {legal.timeline.map((phase) => (
          <li key={phase.enforceable_from} data-testid="phase" data-enforceable={phase.already_enforceable}>
            <strong>{phase.enforceable_from}</strong>:{" "}
            {phase.already_enforceable
              ? "already enforceable"
              : `enforceable in ${phase.days_until} days`}
            {" — "}
            {phase.finding_ids.length} Finding(s): {phase.finding_ids.join(", ")}
          </li>
        ))}
      </ol>
    </section>
  );
}
