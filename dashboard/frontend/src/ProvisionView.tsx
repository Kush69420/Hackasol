import { useEffect, useState } from "react";
import type { Provision } from "./types";

export function ProvisionView({ id, primary, citationOnly }: { id: string; primary?: boolean; citationOnly?: boolean }) {
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
  if (citationOnly) return <span data-testid="llm-citation">{p?.citation ?? id}</span>;
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

export function LlmCitations({ ids }: { ids?: string[] }) {
  if (!ids?.length) return null;
  return (
    <p>Citations: {[...new Set(ids)].map((id, index) => (
      <span key={id}>{index > 0 && ", "}<ProvisionView id={id} citationOnly /></span>
    ))}</p>
  );
}
