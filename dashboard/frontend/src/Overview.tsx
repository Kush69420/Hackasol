import { BANDS, Band, Finding, LegalViewData, Report } from "./types";
import { BAND_LABEL, formatCrore, formatDate } from "./ui";

export function Overview(props: {
  report: Report;
  legal: LegalViewData | null;
  bandFilter: Band | null;
  onBand: (band: Band | null) => void;
}) {
  const { report, legal } = props;
  const findings = report.findings;
  const counts = Object.fromEntries(BANDS.map((b) => [b, findings.filter((f) => f.severity.band === b).length])) as Record<Band, number>;
  const elements = report.personal_data_map.length;
  const withFinding = new Set(findings.flatMap((f) => (f.personal_data_element ? [f.personal_data_element.name] : []))).size;

  const byCategory = new Map<string, Record<Band, number>>();
  for (const f of findings) {
    const row = byCategory.get(f.data_category) ?? { critical: 0, high: 0, medium: 0, low: 0 };
    row[f.severity.band] += 1;
    byCategory.set(f.data_category, row);
  }
  const rows = [...byCategory.entries()]
    .map(([category, mix]) => ({ category, mix, total: BANDS.reduce((s, b) => s + mix[b], 0) }))
    .sort((a, b) => b.total - a.total);
  const max = Math.max(1, ...rows.map((r) => r.total));

  const top = legal?.highest_applicable_ceiling ?? null;
  const next = legal?.timeline.find((p) => !p.already_enforceable) ?? null;

  return (
    <section id="overview" aria-label="Overview" className="panel">
      <header className="panel-head">
        <div className="stack" style={{ gap: "0.5rem" }}>
          <h2>Overview</h2>
          <p className="lede" data-testid="overview-summary">
            <strong className="num">{findings.length}</strong> {findings.length === 1 ? "Finding" : "Findings"} across{" "}
            <strong className="num">{withFinding}</strong> of <span className="num">{elements}</span> Personal Data Elements.
            {top ? (
              <>
                {" "}The highest applicable Penalty Ceiling is <strong>{formatCrore(top.amount_inr_crore)}</strong> ({top.provisions.slice(0, 2).join(", ")}{top.provisions.length > 2 ? ` and ${top.provisions.length - 2} more` : ""}).
              </>
            ) : null}
            {next ? (
              <>
                {" "}Further obligations become enforceable on <strong>{formatDate(next.enforceable_from)}</strong>.
              </>
            ) : null}
          </p>
        </div>
      </header>
      <div className="overview-grid">
        <div>
          <p className="viz-title">Findings by Severity</p>
          {findings.length ? (
            <div className="sevbar" role="img" aria-label={BANDS.map((b) => `${counts[b]} ${b}`).join(", ")}>
              {BANDS.filter((b) => counts[b] > 0).map((b) => (
                <span key={b} style={{ flex: counts[b], background: `var(--sev-${b})` }} title={`${BAND_LABEL[b]}: ${counts[b]}`} />
              ))}
            </div>
          ) : (
            <div className="sevbar"><span className="sevbar-empty" /></div>
          )}
          <div className="sev-legend">
            {BANDS.map((b) => (
              <button
                key={b}
                type="button"
                className="sev-key"
                aria-pressed={props.bandFilter === b}
                aria-label={`${props.bandFilter === b ? "Clear filter" : "Filter Findings to"} ${b}: ${counts[b]}`}
                onClick={() => props.onBand(props.bandFilter === b ? null : b)}
              >
                <span className="k"><span className={`dot dot-${b}`} aria-hidden="true" />{b}</span>
                <span className="v">{counts[b]}</span>
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="viz-title">Findings by Data Category</p>
          {rows.length === 0 ? <p className="muted">No Findings to chart.</p> : (
            <div>
              {rows.map((r) => (
                <div className="cat-row" key={r.category}>
                  <span className="cat-label" title={r.category}>{r.category}</span>
                  <div
                    className="cat-bar"
                    role="img"
                    aria-label={`${r.category}: ${BANDS.filter((b) => r.mix[b]).map((b) => `${r.mix[b]} ${b}`).join(", ")}`}
                    style={{ width: `${(r.total / max) * 100}%`, minWidth: "0.5rem" }}
                  >
                    {BANDS.filter((b) => r.mix[b] > 0).map((b) => (
                      <span key={b} style={{ flex: r.mix[b], background: `var(--sev-${b})` }} title={`${BAND_LABEL[b]}: ${r.mix[b]}`} />
                    ))}
                  </div>
                  <span className="cat-total">{r.total}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export function sortFindings(findings: Finding[]): Finding[] {
  const rank = (f: Finding) => BANDS.indexOf(f.severity.band);
  return [...findings].sort((a, b) => rank(a) - rank(b));
}
