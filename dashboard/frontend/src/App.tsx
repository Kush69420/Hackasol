import { useEffect, useRef, useState } from "react";
import { BANDS, Band, Evidence, Finding, FlowStep, Provision, Report, ScanEvent } from "./types";
import { LiveProbes, LiveProbeEvidence } from "./LiveProbes";
import { FixPatches } from "./FixPatches";
import { LegalView } from "./LegalView";
import { ConsentAssessment } from "./ConsentAssessment";

const STAGES: [string, string][] = [
  ["inventory", "Inventory"],
  ["elements", "Personal Data Elements"],
  ["data_flows", "Data Flows"],
  ["findings", "Findings"],
];
const FORMATS = ["json", "md", "html", "pdf"] as const;

function provenance(mode: string | undefined): string | null {
  if (mode === "live") return "Live";
  if (mode === "cache-only") return "Cache-only";
  if (mode === "recorded") return "Replay Mode";
  return null;
}

export function App() {
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const source = useRef<EventSource | null>(null);

  const [recordings, setRecordings] = useState<string[]>([]);

  useEffect(() => () => source.current?.close(), []);
  useEffect(() => {
    fetch("/api/replays")
      .then((r) => (r.ok ? r.json() : { recordings: [] }))
      .then((d: { recordings: string[] }) => setRecordings(d.recordings))
      .catch(() => setRecordings([]));
  }, []);

  const terminal = events.find((e) => e.type !== "stage");
  const status = !runId ? null : terminal ? terminal.type : "running";
  const mode = events.length ? events[events.length - 1].mode : undefined;

  async function start(url: string, body?: unknown) {
    source.current?.close();
    setBusy(true);
    setError(null);
    setEvents([]);
    setReport(null);
    setSelected(null);
    setRunId(null);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Request rejected (${res.status})`);
      const { run_id } = (await res.json()) as { run_id: string };
      setRunId(run_id);
      const es = new EventSource(`/api/scans/${run_id}/events`);
      source.current = es;
      es.onmessage = async (m) => {
        const ev = JSON.parse(m.data) as ScanEvent;
        setEvents((prev) => (prev.some((p) => p.ordinal === ev.ordinal) ? prev : [...prev, ev]));
        if (ev.type !== "stage") {
          es.close();
          if (ev.type === "completed") {
            const r = await fetch(`/api/scans/${run_id}/report/json`);
            if (r.ok) setReport((await r.json()) as Report);
            else setError(`Report could not be loaded (${r.status})`);
          }
          setBusy(false);
        }
      };
      es.onerror = () => {
        // The server closes the stream after the terminal event; only report early drops.
        if (es.readyState === EventSource.CLOSED) setBusy(false);
      };
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }

  const finding = report?.findings.find((f) => f.id === selected) ?? null;

  return (
    <main>
      <h1>DPDP Compliance Auditor</h1>
      <form
        className="row"
        onSubmit={(e) => {
          e.preventDefault();
          if (target.trim()) void start("/api/scans", { target: target.trim() });
        }}
      >
        <input
          aria-label="Target Application"
          placeholder="Target Application: local path or https Git URL"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
        />
        <button type="submit" disabled={busy || !target.trim()}>
          Scan
        </button>
        <button type="button" disabled={busy} onClick={() => void start("/api/replays/juice-shop")}>
          Replay Mode (recorded Juice Shop scan)
        </button>
        {recordings.filter((name) => name !== "juice-shop").map((name) => (
          <button key={name} type="button" disabled={busy} onClick={() => void start(`/api/replays/${name}`)}>
            Replay Mode (recorded {name} scan)
          </button>
        ))}
      </form>
      {error && <p className="failed" role="alert">{error}</p>}

      {runId && (
        <section aria-label="Run progress">
          <h2>
            Run{" "}
            {provenance(mode) && (
              <span className={`badge badge-${mode}`} data-testid="provenance">
                {provenance(mode)}
              </span>
            )}
          </h2>
          <ol className="stages" data-testid="stages">
            {STAGES.map(([key, label]) => {
              const ev = events.find((e) => e.type === "stage" && e.stage === key);
              return (
                <li key={key} className={ev ? "done" : "pending"} data-stage={key}>
                  {label} {ev ? `✓ ${ev.elapsed_ms} ms` : "…"}
                </li>
              );
            })}
          </ol>
          <p data-testid="run-status" data-status={status ?? ""}>
            Status: {status}
            {terminal?.type === "completed" && ` (${terminal.finding_count} Findings)`}
          </p>
          {terminal?.type === "failed" && (
            <p className="failed" role="alert" data-testid="failed">
              Scan failed{terminal.message ? `: ${terminal.message}` : ""}
            </p>
          )}
        </section>
      )}

      {report && runId && (
        <>
          <section aria-label="Report downloads">
            <h2>Report</h2>
            <p>
              Target Application: {report.target.name}
              {report.target.commit ? ` @ ${report.target.commit.slice(0, 12)}` : ""}
            </p>
            <div className="row" data-testid="downloads">
              {FORMATS.map((f) => (
                <a key={f} href={`/api/scans/${runId}/report/${f}`} download>
                  Download {f.toUpperCase()}
                </a>
              ))}
            </div>
          </section>
          {mode !== "recorded" && <LiveProbes runId={runId} onReport={setReport} />}
          <ConsentAssessment assessment={report.consent_assessment} replay={mode === "recorded"} />
          <LegalView runId={runId} />
          {mode !== "recorded" && <FixPatches runId={runId} findings={report.findings} />}

          <section aria-label="Findings">
            <h2>Findings</h2>
            {BANDS.map((band) => (
              <BandGroup
                key={band}
                band={band}
                findings={report.findings.filter((f) => f.severity.band === band)}
                selected={selected}
                onSelect={setSelected}
              />
            ))}
          </section>

          {finding && <FindingDetail finding={finding} />}

          <PersonalDataMap report={report} />
        </>
      )}
    </main>
  );
}

function BandGroup(props: {
  band: Band;
  findings: Finding[];
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className={`band band-${props.band}`} data-testid={`severity-${props.band}`}>
      <h3>
        {props.band} ({props.findings.length})
      </h3>
      <ul>
        {props.findings.map((f) => (
          <li key={f.id}>
            <button
              type="button"
              className={f.id === props.selected ? "active" : ""}
              onClick={() => props.onSelect(f.id)}
            >
              {f.issue_type} · {f.personal_data_element?.name ?? "configuration"} · {f.processing_operation}
            </button>
          </li>
        ))}
      </ul>
    </div>
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
  if (steps.length === 0) return <p>No Data Flow recorded for this Finding.</p>;
  return (
    <ol className="flow" data-testid="data-flow">
      {steps.map((s, i) => (
        <li key={i} data-testid="flow-step">
          <strong>
            {i + 1}. {s.operation}
          </strong>
          <span className="anchor">
            {s.evidence.file}:{s.evidence.start_line}
          </span>
        </li>
      ))}
    </ol>
  );
}

function ProvisionView({ id, primary }: { id: string; primary?: boolean }) {
  const [p, setP] = useState<Provision | null | undefined>(undefined);
  useEffect(() => {
    let live = true;
    fetch(`/api/provisions/${encodeURIComponent(id)}`)
      .then((r) => (r.ok ? (r.json() as Promise<Provision>) : null))
      .then((v) => live && setP(v))
      .catch(() => live && setP(null));
    return () => {
      live = false;
    };
  }, [id]);
  return (
    <div className="provision" data-testid={primary ? "primary-provision" : "related-provision"}>
      <strong>{p ? p.citation : id}</strong>
      {p && <span> — {p.title}</span>}
      {p === undefined && <em> loading…</em>}
      {p === null && <em> (no registry excerpt available)</em>}
      {p && <blockquote data-testid="statute-excerpt">{p.excerpt}</blockquote>}
    </div>
  );
}

function llmText(field: { status: string; value?: unknown } | undefined): string {
  if (!field) return "not assessed";
  if (field.status !== "assessed") return field.status;
  const v = field.value;
  if (typeof v === "string") return v;
  if (v && typeof v === "object" && "verdict" in v) {
    const t = v as { verdict: string; reason?: string };
    return `${t.verdict}${t.reason ? `: ${t.reason}` : ""}`;
  }
  return JSON.stringify(v);
}

function FindingDetail({ finding: f }: { finding: Finding }) {
  return (
    <section aria-label="Finding detail" data-testid="finding-detail" key={f.id}>
      <h2>
        Finding {f.id} <span className={`badge sev-${f.severity.band}`}>{f.severity.band}</span>
      </h2>
      <p>
        {f.personal_data_element?.name ?? "No single Personal Data Element (configuration Finding)"} · Data Category {f.data_category} · Processing Operation{" "}
        {f.processing_operation}
      </p>
      <h3>Evidence</h3>
      {f.evidence.map((e, i) => (
        <EvidenceView key={i} evidence={e} />
      ))}
      <LiveProbeEvidence finding={f} />
      <h3>Data Flow</h3>
      <DataFlowGraph steps={f.data_flow} />
      <h3>Provisions</h3>
      <ProvisionView id={f.primary_provision} primary />
      {f.other_provisions.map((id) => (
        <ProvisionView key={id} id={id} />
      ))}
      <h3>Penalty Ceiling</h3>
      <p data-testid="penalty-ceiling">
        ₹{f.penalty_ceiling.amount_inr_crore} crore ({f.penalty_ceiling.parent_section}); enforceable from{" "}
        {f.enforceable_from}
      </p>
      <h3>Severity justification</h3>
      <p data-testid="justification">{f.severity.justification}</p>
      <h3>Recommended fix</h3>
      <p data-testid="recommended-fix">{f.recommended_fix.guidance}</p>
      <p>Tailored fix: {llmText(f.recommended_fix.tailored)}</p>
      <h3>LLM triage</h3>
      <p data-testid="llm-triage">{llmText(f.llm_triage)}</p>
    </section>
  );
}

function PersonalDataMap({ report }: { report: Report }) {
  const withFinding = new Set(report.findings.flatMap((f) => (f.personal_data_element ? [f.personal_data_element.name] : [])));
  return (
    <section aria-label="Personal Data Map">
      <h2>Personal Data Map</h2>
      <table data-testid="personal-data-map">
        <thead>
          <tr>
            <th>Element</th>
            <th>Data Category</th>
            <th>Processing Operations</th>
            <th>Finding</th>
          </tr>
        </thead>
        <tbody>
          {report.personal_data_map.map((m) => (
            <tr key={m.element.name} data-testid="map-row">
              <td>{m.element.name}</td>
              <td>{m.element.data_category}</td>
              <td>{[...new Set(m.operations.map((o) => o.operation))].join(", ") || "—"}</td>
              <td>{withFinding.has(m.element.name) ? "Yes" : "No Finding"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
