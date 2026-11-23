import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { formatCrore, formatDate } from "./ui";
import { BANDS, type CeilingRow, type LegalViewData } from "./types";

type Applicability = keyof CeilingRow["finding_ids_by_applicability"];

const APPLICABILITY_LABELS: Record<Applicability, string> = {
  applicable_primary: "Applicable Primary Provision",
  related: "Related Provision",
  conditional: "Conditional Provision",
  needs_legal_review: "Needs Legal Review (breach not established)",
};
const APPLICABILITY_KEYS = Object.keys(APPLICABILITY_LABELS) as Applicability[];

function amount(row: CeilingRow): string {
  if (row.statutory_maximum_inr_crore !== null) return formatCrore(row.statutory_maximum_inr_crore);
  return row.statutory_maximum_text ?? "no fixed figure";
}

function findingsSummary(count: number): string {
  return `${count} ${count === 1 ? "Finding" : "Findings"}`;
}

function Disclosure({ className, summary, children }: { className: string; summary: string; children: ReactNode }) {
  return (
    <details className={className}>
      <summary>
        <span>{summary}</span>
        <ChevronRight size={15} aria-hidden="true" className="legal-chevron" />
      </summary>
      {children}
    </details>
  );
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
        <p>Statutory maximums from the Schedule, not predicted amounts.</p>
      </header>
      <div className="legal-top">
        <div className="legal-figure-block" data-testid="highest-ceiling">
          <p className="legal-label">Highest applicable Penalty Ceiling</p>
          {top ? (
            <>
              <span className="legal-figure">{formatCrore(top.amount_inr_crore)}</span>{" "}
              <span className="legal-figure-caption mono">({top.provisions.join(", ")})</span>
            </>
          ) : (
            <span className="legal-figure is-unassessed">not assessed</span>
          )}
        </div>
        <Disclosure className="legal-disclose" summary="How ceilings are read">
          <p data-testid="ceiling-note">{legal.note}</p>
        </Disclosure>
      </div>
      <div className="table-wrap legal-table-wrap">
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
                <td>
                  {row.citation}
                  <span className="legal-provision-id mono">{row.provision}</span>
                </td>
                <td>{row.schedule_entry ?? "none"}</td>
                <td className="num">{amount(row)}</td>
                <td>
                  <Disclosure className="legal-ids" summary={findingsSummary(row.finding_ids.length)}>
                    <ul className="legal-groups">
                      {APPLICABILITY_KEYS.filter((key) => row.finding_ids_by_applicability[key].length > 0).map((key) => (
                        <li key={key}>
                          <span className="legal-group-label">{APPLICABILITY_LABELS[key]}:</span>{" "}
                          <span className="mono">{row.finding_ids_by_applicability[key].join(", ")}</span>
                        </li>
                      ))}
                    </ul>
                  </Disclosure>
                </td>
                <td className="legal-mix">
                  {BANDS.filter((band) => row.severity_mix[band] > 0)
                    .map((band) => `${band}: ${row.severity_mix[band]}`)
                    .join(", ")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="panel-head legal-timeline-head">
        <h3>Enforcement timeline (relative to scan date {formatDate(legal.as_of)})</h3>
      </div>
      <ol className="timeline" data-testid="timeline">
        {legal.timeline.map((phase) => (
          <li key={phase.enforceable_from} data-testid="phase" data-enforceable={phase.already_enforceable}>
            <span className="when">
              {formatDate(phase.enforceable_from)}:{" "}
              <span className="state">
                {phase.already_enforceable ? "already enforceable" : `enforceable in ${phase.days_until} days`}
              </span>
            </span>
            <div>
              <Disclosure className="legal-ids" summary={findingsSummary(phase.finding_ids.length)}>
                <p className="mono legal-ids-body">{phase.finding_ids.join(", ")}</p>
              </Disclosure>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
