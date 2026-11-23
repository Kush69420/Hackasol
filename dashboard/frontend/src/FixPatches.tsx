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

  return <section aria-label="Fix Patch review">
    <h2>Fix Patch review</h2>
    <p>Destination: {destination}; branch: {branch}; base: dpdp-pinned-base</p>
    <label>Destination fork <input value={destination} onChange={(event) => setDestination(event.target.value)} /></label>
    {wrongDestination && <p role="alert">Destination must be the authorized fork {FORK}, not upstream</p>}
    {[...byType].map(([issueType, group]) => <section key={issueType} aria-label={`Issue Type ${issueType}`}>
    <h3>{issueType}</h3>
    {group.map((finding) => <div key={finding.id}>
      <label>
        <input type="checkbox" disabled={finding.fix_patch?.status !== "accepted"}
          checked={selected.includes(finding.id)}
          onChange={(event) => setSelected(event.target.checked ? [...selected, finding.id] : selected.filter((id) => id !== finding.id))} />
        {finding.issue_type} · {finding.id} · {finding.fix_patch?.status} · {finding.fix_patch?.provenance}
      </label>
      <p>{finding.fix_patch?.reason}</p>
      <p>{rescanStatus(finding.fix_patch?.reason ?? "")}</p>
      <pre>{finding.fix_patch?.diff}</pre>
    </div>)}
    </section>)}
    <label>Review branch <input value={branch} onChange={(event) => setBranch(event.target.value)} /></label>
    <label><input type="checkbox" checked={authorized} onChange={(event) => setAuthorized(event.target.checked)} />
      I authorize opening a PR in this fork after a fresh combined re-scan.</label>
    <button type="button" disabled={busy || wrongDestination || !authorized || !selected.length || !branch} onClick={() => void openPr()}>
      Open PR
    </button>
    {message && <p role="status">{message}</p>}
  </section>;
}
