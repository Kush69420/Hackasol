import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { BANDS, Band, Evidence, Finding, FlowStep } from "./types";
import { LiveProbeEvidence } from "./LiveProbes";
import { LlmCitations, ProvisionView } from "./ProvisionView";
import { SeverityBadge, formatCrore, formatDate } from "./ui";

const PAST_TENSE: Record<string, string | undefined> = {
  Collect: "collected by",
  Store: "stored in",
  Log: "logged by",
  Transfer: "transferred by",
  Expose: "exposed by",
  Erase: "erased by",
};

const CITED_LINE = /([\w./-]+\.\w+):(\d+)/g;

function llmText(field: { status: string; value?: unknown } | undefined): string {
  if (!field) return "not assessed";
  if (field.status !== "assessed") return field.status;
  const v = field.value;
  if (typeof v === "string") return v;
  if (v && typeof v === "object" && "fix" in v && typeof v.fix === "string") return v.fix;
  if (v && typeof v === "object" && "verdict" in v) {
    const verdict = String(v.verdict);
    const reason = "reason" in v && typeof v.reason === "string" ? v.reason : "";
    return `${verdict}${reason ? `: ${reason}` : ""}`;
  }
  return JSON.stringify(v);
}

/** `aadhaar_number` becomes "Aadhaar number"; all-caps acronyms such as IFSC stay as written. */
function humanize(field: string): string {
  const words = field.split(/[_.\s-]+|(?<=[a-z0-9])(?=[A-Z])/).filter(Boolean);
  const text = words.map((w) => (/^[A-Z]{2,}$/.test(w) ? w : w.toLowerCase())).join(" ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Splits `kind:Owner.field`; a `param:METHOD /route#body.field` name keeps its route as the owner. */
function splitElement(name: string): { kind: string; owner: string; field: string } {
  const colon = name.indexOf(":");
  const kind = colon < 0 ? "" : name.slice(0, colon);
  const rest = colon < 0 ? name : name.slice(colon + 1);
  if (kind === "param") {
    const field = rest.slice(Math.max(rest.lastIndexOf("."), rest.lastIndexOf("#"), rest.lastIndexOf("?")) + 1);
    return { kind, owner: rest.split(/[#?]/)[0], field };
  }
  const dot = rest.indexOf(".");
  return { kind, owner: dot < 0 ? rest : rest.slice(0, dot), field: rest.slice(rest.lastIndexOf(".") + 1) };
}

/** Evidence blocks that the justification cites ("file:line") come first; the rest keep their order. */
export function orderEvidence(evidence: Evidence[], justification: string): Evidence[] {
  for (const [, file, digits] of justification.matchAll(CITED_LINE)) {
    const line = Number(digits);
    const i = evidence.findIndex((e) => (e.file === file || e.file.endsWith(`/${file}`)) && e.start_line <= line && line <= e.end_line);
    if (i > 0) return [evidence[i], ...evidence.slice(0, i), ...evidence.slice(i + 1)];
    if (i === 0) return evidence;
  }
  return evidence;
}

/** Plain statement of a Finding: its Personal Data Element and Processing Operation, with the Issue Type shown beside it. */
export function findingTitle(f: Finding): string {
  const verb = PAST_TENSE[f.processing_operation ?? ""] ?? null;
  const el = f.personal_data_element;
  if (!el) {
    const where = orderEvidence(f.evidence, f.severity.justification)[0]?.file;
    if (!where) return "Personal Data";
    return verb ? `Personal Data ${verb} ${where}` : `Personal Data in ${where}`;
  }
  const { kind, owner, field } = splitElement(el.name);
  const subject = kind === "param" ? `${humanize(field || owner)} parameter` : humanize(field || owner);
  const place = kind === "model" ? `the ${owner} model` : owner;
  return verb ? `${subject} ${verb} ${place}` : `${subject} in ${place}`;
}

/**
 * The Finding to open first: the highest band, then Risk Matrix order within it.
 * Prefers a Finding with a traced Data Flow and a Personal Data Element; otherwise the first Finding of the highest band.
 */
export function pickHeadlineFinding(findings: Finding[]): string | null {
  const ranked = [...findings].sort((a, b) => BANDS.indexOf(a.severity.band) - BANDS.indexOf(b.severity.band));
  const headline = ranked.find((f) => f.data_flow.length > 0 && f.personal_data_element !== null) ?? ranked[0];
  return headline?.id ?? null;
}

function matches(f: Finding, q: string): boolean {
  if (!q) return true;
  const hay = [
    f.id,
    f.issue_type,
    findingTitle(f),
    f.personal_data_element?.name ?? "",
    f.data_category,
    f.processing_operation ?? "",
    f.primary_provision,
  ]
    .join(" ")
    .toLowerCase();
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
                      {shown.map((f) => {
                        const where = orderEvidence(f.evidence, f.severity.justification)[0]?.file;
                        return (
                          <li key={f.id}>
                            <button type="button" className="row-btn" aria-current={f.id === props.selected} onClick={() => props.onSelect(f.id)}>
                              <span className="row-title">{findingTitle(f)}</span>
                              <span className="row-type chip mono">{f.issue_type}</span>
                              <span className="row-sub">
                                {where ? `${where} · ` : null}
                                <span className="prov">{f.primary_provision}</span>
                              </span>
                            </button>
                          </li>
                        );
                      })}
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

/** Report prose: `backticks` render as code and a doubled "CVSS CVSS:" prefix is shortened. Unbalanced backticks stay literal. */
function ReportText({ text }: { text: string }) {
  const clean = text.replace(/CVSS CVSS:/g, "CVSS:");
  const parts = clean.split("`");
  if (parts.length % 2 === 0) return <>{clean}</>;
  return <>{parts.map((part, i) => (i % 2 === 1 ? <code key={i}>{part}</code> : part))}</>;
}

/** CWE entries name the coding flaw behind a Finding; they are not statutory Provisions. */
function TechnicalWeaknesses({ ids }: { ids: string[] }) {
  if (ids.length === 0) return null;
  return (
    <div className="weakness-group">
      <h4>Technical weakness</h4>
      <p>Common Weakness Enumeration (CWE) references, not statutory Provisions.</p>
      <div className="chips">
        {ids.map((id) => <span key={id} className="chip mono">{id}</span>)}
      </div>
    </div>
  );
}

function FindingDetail({ finding: f }: { finding: Finding }) {
  const title = findingTitle(f);
  const evidence = orderEvidence(f.evidence, f.severity.justification);
  const triage = llmText(f.llm_triage);
  const tailored = llmText(f.recommended_fix.tailored);
  const verdict = f.llm_triage.status === "assessed" ? f.llm_triage.value?.verdict : undefined;
  const statutory = f.other_provisions.filter((id) => !id.startsWith("CWE-"));
  const weaknesses = f.other_provisions.filter((id) => id.startsWith("CWE-"));
  return (
    <div className="detail" aria-label="Finding detail" role="region" data-testid="finding-detail" key={f.id}>
      <div className="detail-head">
        <div className="detail-title">
          <SeverityBadge band={f.severity.band} />
          <h2 className="finding-title">{title}</h2>
          <span className="chip mono">{f.issue_type}</span>
          {f.status && f.status !== "open" ? <span className="chip chip-legal">{f.status}</span> : null}
        </div>
        <p className="detail-id mono">Finding {f.id}</p>
        <p className="facts">
          {f.personal_data_element ? <span><b className="mono">{f.personal_data_element.name}</b></span> : null}
          <span>Data Category {f.data_category}</span>
          {f.processing_operation ? <span>Processing Operation {f.processing_operation}</span> : null}
        </p>
      </div>

      <div className="dsec">
        <h3>Why this Severity</h3>
        <p className="just" data-testid="justification"><ReportText text={f.severity.justification} /></p>
      </div>

      <div className="dsec">
        <h3>Evidence</h3>
        {evidence.map((e, i) => <EvidenceView key={i} evidence={e} />)}
        <LiveProbeEvidence finding={f} />
      </div>

      <div className="dsec">
        <h3>Data Flow</h3>
        <DataFlowGraph steps={f.data_flow} />
      </div>

      <div className="dsec">
        <h3>Provisions</h3>
        <ProvisionView id={f.primary_provision} primary />
        {statutory.map((id) => <ProvisionView key={id} id={id} />)}
        <TechnicalWeaknesses ids={weaknesses} />
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
        <p className="prose" data-testid="recommended-fix"><ReportText text={f.recommended_fix.guidance} /></p>
        <p className="muted">Tailored fix: <ReportText text={tailored} /></p>
      </div>

      <div className="dsec triage">
        <h3>LLM triage</h3>
        <p className="prose" data-testid="llm-triage">
          {verdict ? <span className={`chip ${verdictClass(verdict)}`} style={{ marginRight: "0.5rem" }}>{verdict}</span> : null}
          <ReportText text={verdict ? triage.replace(/^[^:]*:\s*/, "") : triage} />
        </p>
        {f.llm_triage.status === "assessed" && <LlmCitations ids={f.llm_triage.value?.citations} />}
      </div>
    </div>
  );
}
