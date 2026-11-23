import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { BANDS, Band, Evidence, Finding, FlowStep } from "./types";
import { LiveProbeEvidence } from "./LiveProbes";
import { LlmCitations, ProvisionView } from "./ProvisionView";
import { SeverityBadge, formatCrore, formatDate } from "./ui";

function llmText(field: { status: string; value?: unknown } | undefined): string {
  if (!field) return "not assessed";
  if (field.status !== "assessed") return field.status;
  const v = field.value;
  if (typeof v === "string") return v;
  if (v && typeof v === "object" && "fix" in v && typeof (v as { fix: unknown }).fix === "string") return (v as { fix: string }).fix;
  if (v && typeof v === "object" && "verdict" in v) {
    const t = v as { verdict: string; reason?: string };
    return `${t.verdict}${t.reason ? `: ${t.reason}` : ""}`;
  }
  return JSON.stringify(v);
}

function matches(f: Finding, q: string): boolean {
  if (!q) return true;
  const hay = [f.id, f.issue_type, f.personal_data_element?.name ?? "", f.data_category, f.processing_operation, f.primary_provision].join(" ").toLowerCase();
  return q.toLowerCase().split(/\s+/).every((t) => hay.includes(t));
}

export function Findings(props: {
  findings: Finding[];
  selected: string | null;
  onSelect: (id: string) => void;
  bandFilter: Band | null;
}) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const categories = useMemo(() => [...new Set(props.findings.map((f) => f.data_category))].sort(), [props.findings]);
  const finding = props.findings.find((f) => f.id === props.selected) ?? null;
  const filtering = Boolean(query || category || props.bandFilter);

  return (
    <section id="findings" aria-label="Findings" className="panel findings">
      <header className="panel-head">
        <h2>Findings</h2>
        <p>Grouped by Severity. Select a Finding to see its Evidence, Data Flow and Provisions.</p>
      </header>
      <div className="findings-grid">
        <div className="list-col">
          <div className="list-tools">
            <label className="search">
              <Search size={15} aria-hidden="true" />
              <input type="text" aria-label="Search Findings" placeholder="Search Findings" value={query} onChange={(e) => setQuery(e.target.value)} />
            </label>
            <select aria-label="Filter by Data Category" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="list-scroll">
            {BANDS.map((band) => {
              const inBand = props.findings.filter((f) => f.severity.band === band);
              const shown = inBand.filter(
                (f) => (!props.bandFilter || props.bandFilter === band) && (!category || f.data_category === category) && matches(f, query),
              );
              return (
                <div className="band" key={band} data-testid={`severity-${band}`}>
                  <h3 className="band-head">
                    <span className={`dot dot-${band}`} aria-hidden="true" />
                    {band}
                    <span className="count">{filtering ? `${shown.length} of ${inBand.length}` : inBand.length}</span>
                  </h3>
                  {shown.length === 0 ? (
                    <p className="band-empty">{inBand.length === 0 ? "No Findings in this band." : "No Findings match the current filter."}</p>
                  ) : (
                    <ul>
                      {shown.map((f) => (
                        <li key={f.id}>
                          <button type="button" className="row-btn" aria-current={f.id === props.selected} onClick={() => props.onSelect(f.id)}>
                            <span className="row-type">{f.issue_type}</span>
                            <span className="row-op">{f.processing_operation}</span>
                            <span className="row-sub">
                              {f.personal_data_element?.name ?? "configuration"} · <span className="prov">{f.primary_provision}</span>
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>
        {finding ? (
          <FindingDetail finding={finding} />
        ) : (
          <div className="empty" style={{ alignSelf: "center" }}>
            {props.findings.length ? "Select a Finding to open its Evidence, Data Flow and Provisions." : "This scan produced no Findings."}
          </div>
        )}
      </div>
    </section>
  );
}

function EvidenceView({ evidence }: { evidence: Evidence }) {
  const lines = evidence.excerpt.split("\n");
  return (
    <figure className="evidence" data-testid="evidence">
      <figcaption>
        {evidence.file}:{evidence.start_line}
        {evidence.end_line !== evidence.start_line ? `-${evidence.end_line}` : ""}
      </figcaption>
      <pre>
        {lines.map((l, i) => (
          <div key={i} className="hl" data-testid="evidence-line">
            <span className="ln">{evidence.start_line + i}</span>
            {l}
          </div>
        ))}
      </pre>
    </figure>
  );
}

function DataFlowGraph({ steps }: { steps: FlowStep[] }) {
  if (steps.length === 0) return <p className="muted">No Data Flow recorded for this Finding.</p>;
  return (
    <ol className="flow" data-testid="data-flow">
      {steps.map((s, i) => (
        <li key={i} data-testid="flow-step">
          <span className="op">
            <span className="idx" aria-hidden="true">{i + 1}</span>
            {s.operation}
          </span>
          <span className="anchor">
            {s.evidence.file}:{s.evidence.start_line}
          </span>
        </li>
      ))}
    </ol>
  );
}

function verdictClass(text: string): string {
  if (text.startsWith("true-positive")) return "chip-good";
  if (text.startsWith("false-positive")) return "chip-bad";
  return "chip-legal";
}

function FindingDetail({ finding: f }: { finding: Finding }) {
  const triage = llmText(f.llm_triage);
  const tailored = llmText(f.recommended_fix.tailored);
  const verdict = f.llm_triage.status === "assessed" ? f.llm_triage.value?.verdict : undefined;
  return (
    <div className="detail" aria-label="Finding detail" role="region" data-testid="finding-detail" key={f.id}>
      <div className="detail-head">
        <div className="detail-title">
          <SeverityBadge band={f.severity.band} />
          <h2>{f.issue_type}</h2>
          {f.status && f.status !== "open" ? <span className="chip chip-legal">{f.status}</span> : null}
        </div>
        <p className="detail-id mono">Finding {f.id}</p>
        <p className="facts">
          <span><b>{f.personal_data_element?.name ?? "No single Personal Data Element (configuration Finding)"}</b></span>
          <span>Data Category {f.data_category}</span>
          <span>Processing Operation {f.processing_operation}</span>
        </p>
      </div>

      <div className="dsec">
        <h3>Why this Severity</h3>
        <p className="just" data-testid="justification">{f.severity.justification}</p>
      </div>

      <div className="dsec">
        <h3>Evidence</h3>
        {f.evidence.map((e, i) => <EvidenceView key={i} evidence={e} />)}
        <LiveProbeEvidence finding={f} />
      </div>

      <div className="dsec">
        <h3>Data Flow</h3>
        <DataFlowGraph steps={f.data_flow} />
      </div>

      <div className="dsec">
        <h3>Provisions</h3>
        <ProvisionView id={f.primary_provision} primary />
        {f.other_provisions.map((id) => <ProvisionView key={id} id={id} />)}
      </div>

      <div className="dsec">
        <h3>Penalty Ceiling</h3>
        <p className="ceiling" data-testid="penalty-ceiling">
          <span className="ceiling-amt">{formatCrore(f.penalty_ceiling.amount_inr_crore)}</span>
          <span className="muted">
            {f.penalty_ceiling.parent_section} · enforceable from <span title={f.enforceable_from}>{formatDate(f.enforceable_from)}</span>
          </span>
        </p>
      </div>

      <div className="dsec">
        <h3>Recommended fix</h3>
        <p className="prose" data-testid="recommended-fix">{f.recommended_fix.guidance}</p>
        <p className="muted">Tailored fix: {tailored}</p>
      </div>

      <div className="dsec triage">
        <h3>LLM triage</h3>
        <p className="prose" data-testid="llm-triage">
          {verdict ? <span className={`chip ${verdictClass(verdict)}`} style={{ marginRight: "0.5rem" }}>{verdict}</span> : null}
          {verdict ? triage.replace(/^[^:]*:\s*/, "") : triage}
        </p>
        {f.llm_triage.status === "assessed" && <LlmCitations ids={f.llm_triage.value?.citations} />}
      </div>
    </div>
  );
}
