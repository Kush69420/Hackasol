import { useState } from "react";
import { Finding, Report } from "./types";

type ProbeResult = { assertion: string; finding_id: string | null; result: string; method: string; route: string; reason: string; request: string; response: string };

export function LiveProbes({ runId, onReport }: { runId: string; onReport: (report: Report) => void }) {
  const [target, setTarget] = useState("http://127.0.0.1:3000");
  const [authorized, setAuthorized] = useState(false);
  const [message, setMessage] = useState("");
  const [results, setResults] = useState<ProbeResult[]>([]);
  async function run() {
    setMessage("Running Live Probes…");
    try {
      const response = await fetch(`/api/scans/${runId}/probes`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target, authorized }) });
      if (!response.ok) throw new Error(`Request rejected (${response.status})`);
      const data = await response.json() as { report: Report; results: ProbeResult[] };
      onReport(data.report);
      setResults(data.results);
      setMessage(`${data.results.filter(item => item.finding_id !== null).length} matched Live Probe outcomes`);
    } catch (error) { setMessage((error as Error).message); }
  }
  return <section aria-label="Live Probes"><h2>Live Probes</h2>
    <input aria-label="Live Probe origin" value={target} onChange={e => setTarget(e.target.value)} />
    <label><input type="checkbox" checked={authorized} onChange={e => setAuthorized(e.target.checked)} /> I authorize probing this dedicated synthetic instance</label>
    <button disabled={!authorized} onClick={() => void run()}>Run Live Probes</button><p role="status">{message}</p>
    {results.length > 0 && <ul aria-label="Live Probe run details">{results.map((item, i) =>
      <li key={`${item.assertion}-${i}`}><strong>{item.assertion}: {item.result}</strong> — {item.method} {item.route}; {item.reason}<pre>Request: {item.request}{"\n"}Response: {item.response}</pre></li>)}</ul>}
  </section>;
}

export function LiveProbeEvidence({ finding }: { finding: Finding }) {
  const p = finding.live_probe;
  return p ? <section aria-label="Live Probe Evidence"><h3>Live Probe: {p.result}</h3><p>{p.method} {p.route} — {p.reason}</p><pre>Request: {p.request}{"\n"}Response: {p.response}</pre></section> : null;
}
