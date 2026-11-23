import { useEffect, useState } from "react";
import type { Provision } from "./types";

export function ProvisionView({ id, primary, citationOnly }: { id: string; primary?: boolean; citationOnly?: boolean }) {
  const [p, setP] = useState<Provision | null | undefined>(undefined);
  const [open, setOpen] = useState(false);
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
      <div className="provision-head">
        <strong>{p ? p.citation : id}</strong>
        {primary && <span className="chip chip-good">Primary Provision</span>}
        {p && <span className="muted">{p.title}</span>}
        {p === undefined && <span className="muted">loading…</span>}
        {p === null && <span className="muted">(no registry excerpt available)</span>}
      </div>
      {p && (
        <>
          <blockquote data-testid="statute-excerpt" className={open ? "open" : undefined}>{p.excerpt}</blockquote>
          {p.excerpt.length > 220 && (
            <button type="button" className="more" aria-expanded={open} onClick={() => setOpen(!open)}>
              {open ? "Show less" : "Show full text"}
            </button>
          )}
        </>
      )}
    </div>
  );
}

export function LlmCitations({ ids }: { ids?: string[] }) {
  if (!ids?.length) return null;
  return (
    <p className="muted">Citations: {[...new Set(ids)].map((id, index) => (
      <span key={id}>{index > 0 && ", "}<ProvisionView id={id} citationOnly /></span>
    ))}</p>
  );
}
