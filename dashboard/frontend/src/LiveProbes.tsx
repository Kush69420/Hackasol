import { useState } from "react";
import { Finding, Report } from "./types";

type ProbeResult = { assertion: string; finding_id: string | null; result: string; method: string; route: string; reason: string; request: string; response: string };

function resultClass(result: string): string {
  if (result === "Confirmed") return "chip-bad";
  if (result === "Refuted") return "chip-good";
  return "chip-legal";
}

export function LiveProbes({ runId, onReport }: { runId: string; onReport: (report: Report) => void }) {
  const [target, setTarget] = useState("http://127.0.0.1:3000");
  const [authorized, setAuthorized] = useState(false);
  const [message, setMessage] = useState("");
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<ProbeResult[]>([]);
  async function run() {
    setMessage("Running Live Probes…");
    setRunning(true);
    try {
      const response = await fetch(`/api/scans/${runId}/probes`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target, authorized }) });
      if (!response.ok) throw new Error(`Request rejected (${response.status})`);
      const data = await response.json() as { report: Report; results: ProbeResult[] };
      onReport(data.report);
      setResults(data.results);
      setMessage(`${data.results.filter(item => item.finding_id !== null).length} matched Live Probe outcomes`);
    } catch (error) { setMessage((error as Error).message); } finally { setRunning(false); }
  }
  return (
    <section id="live-probes" aria-label="Live Probes" className="panel">
      <header className="panel-head">
        <h2>Live Probes</h2>
        <p>Send requests to a running instance on localhost to confirm or refute static Findings.</p>
      </header>
      <div className="form-grid">
        <div className="form-row">
          <input className="field" aria-label="Live Probe origin" value={target} onChange={e => setTarget(e.target.value)} />
          <button type="button" className="btn btn-primary" disabled={!authorized || running} onClick={() => void run()}>Run Live Probes</button>
        </div>
        <label className="check">
          <input type="checkbox" checked={authorized} onChange={e => setAuthorized(e.target.checked)} />
          I authorize probing this dedicated synthetic instance
        </label>
        <p role="status" className="muted">{message}</p>
      </div>
      {results.length > 0 && (
        <ul aria-label="Live Probe run details" className="result-list">
          {results.map((item, i) => (
            <li key={`${item.assertion}-${i}`}>
              <div><span className={`chip ${resultClass(item.result)}`}>{item.result}</span> <strong>{item.assertion}</strong></div>
              <div className="muted">{item.method} {item.route}; {item.reason}</div>
              <pre className="plain-pre">Request: {item.request}{"\n"}Response: {item.response}</pre>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function LiveProbeEvidence({ finding }: { finding: Finding }) {
  const p = finding.live_probe;
  return p ? (
    <section aria-label="Live Probe Evidence" className="stack" style={{ gap: "0.5rem" }}>
      <h3>Live Probe: <span className={`chip ${resultClass(p.result)}`}>{p.result}</span></h3>
      <p className="muted">{p.method} {p.route} — {p.reason}</p>
      <pre className="plain-pre">Request: {p.request}{"\n"}Response: {p.response}</pre>
    </section>
  ) : null;
}
