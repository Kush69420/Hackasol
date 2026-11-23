import { useState } from "react";
import type { Finding } from "./types";

const FORK = "TanKaizokuO/juice-shop";

function rescanStatus(reason: string) {
  try {
    const r = JSON.parse(reason) as { remaining?: unknown[]; new?: unknown[] };
    if (Array.isArray(r.remaining) && Array.isArray(r.new))
      return `Re-scan: ${r.remaining.length} selected Finding(s) remaining, ${r.new.length} new`;
  } catch { /* free-text reason */ }
  return "Re-scan: not yet verified";
}

export function FixPatches({ runId, findings }: { runId: string; findings: Finding[] }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [destination, setDestination] = useState(FORK);
  const [branch, setBranch] = useState("dpdp-fix-review");
  const [authorized, setAuthorized] = useState(false);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const patches = findings.filter((f) => f.fix_patch);
  if (!patches.length) return null;
  const byType = new Map<string, Finding[]>();
  for (const f of patches) byType.set(f.issue_type, [...(byType.get(f.issue_type) ?? []), f]);
  const wrongDestination = destination.trim().toLowerCase() !== FORK.toLowerCase();

  async function openPr() {
    setBusy(true);
    setMessage("");
    try {
      const response = await fetch(`/api/scans/${runId}/fix-patches/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ destination: destination.trim(), branch, finding_ids: selected, authorized }),
      });
      const result: { url?: string; detail?: string } = await response.json();
      if (!response.ok || !result.url) throw new Error(result.detail || "Publishing failed");
      setMessage(`Review PR opened: ${result.url}`);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return <section id="fix-patches" aria-label="Fix Patch review" className="panel">
    <header className="panel-head">
      <h2>Fix Patch review</h2>
      <p>Destination: {destination}; branch: {branch}; base: dpdp-pinned-base</p>
    </header>
    <div className="form-grid">
      <label className="field-label">Destination fork
        <input className="field" value={destination} onChange={(event) => setDestination(event.target.value)} />
      </label>
      {wrongDestination && <p className="callout" role="alert">Destination must be the authorized fork {FORK}, not upstream</p>}
    </div>
    <div className="divided" style={{ borderTop: "1px solid var(--line)" }}>
      {[...byType].map(([issueType, group]) => <section key={issueType} aria-label={`Issue Type ${issueType}`} className="panel-body stack">
        <h3 style={{ color: "var(--ink)", fontSize: "0.9375rem" }}>{issueType}</h3>
        {group.map((finding) => <div key={finding.id} className="stack" style={{ gap: "0.45rem" }}>
          <label className="check">
            <input type="checkbox" disabled={finding.fix_patch?.status !== "accepted"}
              checked={selected.includes(finding.id)}
              onChange={(event) => setSelected(event.target.checked ? [...selected, finding.id] : selected.filter((id) => id !== finding.id))} />
            <span>{finding.issue_type} · <span className="mono">{finding.id}</span> · {finding.fix_patch?.status} · {finding.fix_patch?.provenance}</span>
          </label>
          <p className="muted">{finding.fix_patch?.reason}</p>
          <p className="muted">{rescanStatus(finding.fix_patch?.reason ?? "")}</p>
          <pre className="plain-pre">{finding.fix_patch?.diff}</pre>
        </div>)}
      </section>)}
    </div>
    <div className="form-grid" style={{ borderTop: "1px solid var(--line)" }}>
      <label className="field-label">Review branch
        <input className="field" value={branch} onChange={(event) => setBranch(event.target.value)} />
      </label>
      <label className="check"><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
        I authorize opening a PR in this fork after a fresh combined re-scan.</label>
      <div className="form-row">
        <button type="button" className="btn btn-primary" disabled={busy || wrongDestination || !authorized || !selected.length || !branch} onClick={() => void openPr()}>
          Open PR
        </button>
      </div>
      {message && <p role="status" className="muted">{message}</p>}
    </div>
  </section>;
}
