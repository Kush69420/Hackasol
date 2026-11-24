import { useEffect, useId, useState } from "react";
import { navigate } from "./route";
import { provenance, targetLabel } from "./ui";
import { BANDS, type Band } from "./types";

type Counts = Record<Band, number> & { total: number };

type TargetSummary = {
  name: string;
  label: string;
  replay_available: boolean;
  live_available: boolean;
  scan_date: string | null;
  llm: { provider: string; model: string };
  counts: Counts;
};

type RunSummary = {
  run_id: string;
  mode: string;
  target: string;
  status: string;
  started_at: string | null;
  finding_count: number | null;
};

type ListState<T> = { status: "loading" } | { status: "error" } | { status: "ok"; items: T[] };

/** Loads a JSON list once; a failed or malformed response becomes the "error" state. */
function useList<T>(url: string): ListState<T> {
  const [state, setState] = useState<ListState<T>>({ status: "loading" });
  useEffect(() => {
    let live = true;
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(String(res.status));
        return res.json() as Promise<unknown>;
      })
      .then((body) => {
        if (!live) return;
        if (!Array.isArray(body)) throw new Error("not a list");
        setState({ status: "ok", items: body as T[] });
      })
      .catch(() => {
        if (live) setState({ status: "error" });
      });
    return () => {
      live = false;
    };
  }, [url]);
  return state;
}

/** The server's rejection text (its `detail`) when it gives one, else a status line. */
async function failureMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* response was not JSON */
  }
  return `Request rejected (${res.status})`;
}

function formatDateTime(iso: string | null): string {
  if (!iso) return "not stated";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function TargetCard({ target: t }: { target: TargetSummary }) {
  const titleId = useId();
  const liveHintId = useId();
  const [pending, setPending] = useState<null | "replay" | "scan">(null);
  const [error, setError] = useState<string | null>(null);

  async function launch(kind: "replay" | "scan") {
    if (pending) return;
    setPending(kind);
    setError(null);
    try {
      const path = kind === "replay"
        ? `/api/replays/${encodeURIComponent(t.name)}`
        : `/api/targets/${encodeURIComponent(t.name)}/scan`;
      const res = await fetch(path, { method: "POST" }).catch(() => {
        throw new Error("Could not reach the server. Try again.");
      });
      if (!res.ok) throw new Error(await failureMessage(res));
      const body = (await res.json()) as { run_id?: unknown };
      if (typeof body.run_id !== "string") throw new Error("The server did not return a run.");
      // Leaves Home on success; the dashboard attaches to the run from the query string.
      navigate(`/dashboard?run=${encodeURIComponent(body.run_id)}`);
    } catch (err) {
      setError((err as Error).message);
      setPending(null);
    }
  }

  const busy = pending !== null;
  const severityLabel = `Findings by severity, ${t.label}`;

  return (
    <li>
      <article className="target-card" aria-labelledby={titleId}>
        <div className="target-head">
          <h3 id={titleId} className="target-title">{t.label}</h3>
          {t.replay_available && <span className="badge badge-recorded">Recorded</span>}
        </div>

        <dl className="target-meta">
          <div>
            <dt>Scan date</dt>
            <dd>{formatDateTime(t.scan_date)}</dd>
          </div>
          <div>
            <dt>LLM</dt>
            <dd className="mono">{`${t.llm.provider} · ${t.llm.model}`}</dd>
          </div>
        </dl>

        <ul className="chips home-counts" aria-label={severityLabel}>
          {BANDS.map((band) => (
            <li key={band}>
              <span className={`badge sev sev-${band}`}>
                <span className={`dot dot-${band}`} aria-hidden="true" />
                {`${t.counts[band]} ${band}`}
              </span>
            </li>
          ))}
          <li>
            <span className="chip">{`${t.counts.total} total`}</span>
          </li>
        </ul>

        <div className="target-actions">
          {t.replay_available && (
            <button
              type="button"
              className="btn btn-sm"
              disabled={busy}
              aria-busy={pending === "replay"}
              aria-label={`Replay recorded scan: ${t.label}`}
              onClick={() => void launch("replay")}
            >
              {pending === "replay" ? "Starting…" : "Replay"}
            </button>
          )}
          <button
            type="button"
            className="btn btn-sm"
            disabled={!t.live_available || busy}
            aria-busy={pending === "scan"}
            aria-describedby={t.live_available ? undefined : liveHintId}
            aria-label={`Scan live: ${t.label}`}
            title={t.live_available ? undefined : "Clone missing: see README Set-up"}
            onClick={() => void launch("scan")}
          >
            {pending === "scan" ? "Starting…" : "Scan live"}
          </button>
          {!t.live_available && (
            <span id={liveHintId} className="sr-only">Clone missing: see README Set-up</span>
          )}
        </div>

        {error && <p className="home-error" role="alert">{error}</p>}
      </article>
    </li>
  );
}

export function TargetApplications() {
  const list = useList<TargetSummary>("/api/targets");
  return (
    <section className="panel home-browse" aria-labelledby="home-targets-title">
      <div className="panel-head">
        <h2 id="home-targets-title">Target Applications</h2>
        <p>Replay a recorded scan, or scan a clone live.</p>
      </div>
      <div className="home-browse-body">
        {list.status === "loading" && <p className="muted">Loading Target Applications…</p>}
        {list.status === "error" && <p className="muted">Target Applications are unavailable right now. The form above still works.</p>}
        {list.status === "ok" && list.items.length === 0 && <p className="muted">No Target Applications are configured.</p>}
        {list.status === "ok" && list.items.length > 0 && (
          <ul className="target-grid">
            {list.items.map((t) => <TargetCard key={t.name} target={t} />)}
          </ul>
        )}
      </div>
    </section>
  );
}

const STAGES: { name: string; line: string }[] = [
  { name: "Inventory", line: "Reads the Target Application and lists the files and configuration it holds." },
  { name: "Personal Data Elements", line: "Finds each field, column, form input or config key that holds Personal Data." },
  { name: "Data Flows", line: "Traces each Personal Data Element through its Processing Operations, from collection to erasure." },
  { name: "Findings", line: "Flags each mishandling with Evidence, Severity and a recommended fix." },
];

export function AuditPipeline() {
  return (
    <section className="panel home-browse" aria-labelledby="home-pipeline-title">
      <div className="panel-head">
        <h2 id="home-pipeline-title">How an audit works</h2>
        <p>Four stages, run in order on the code itself.</p>
      </div>
      <div className="home-browse-body">
        <ol className="pipeline">
          {STAGES.map((stage, i) => (
            <li key={stage.name} className="pipeline-step">
              <span className="pipeline-n mono" aria-hidden="true">{String(i + 1).padStart(2, "0")}</span>
              <span className="pipeline-name">{stage.name}</span>
              <span className="pipeline-line">{stage.line}</span>
            </li>
          ))}
        </ol>
        <p className="pipeline-end">Each Finding is mapped to DPDP Act 2023 and Rules 2025 Provisions.</p>
      </div>
    </section>
  );
}

export function RecentRuns() {
  const list = useList<RunSummary>("/api/runs?limit=10");
  return (
    <section className="panel home-browse" aria-labelledby="home-runs-title">
      <div className="panel-head">
        <h2 id="home-runs-title">Recent runs</h2>
        <p>Open a run to read its Report.</p>
      </div>
      <div className="home-browse-body">
        {list.status === "loading" && <p className="muted">Loading recent runs…</p>}
        {list.status === "error" && <p className="muted">Recent runs are unavailable right now.</p>}
        {list.status === "ok" && list.items.length === 0 && (
          <p className="muted">No runs yet. Start an audit above or replay a Target Application.</p>
        )}
        {list.status === "ok" && list.items.length > 0 && (
          <ul className="run-list">
            {list.items.map((run) => {
              const href = `/dashboard?run=${encodeURIComponent(run.run_id)}`;
              const findings = run.finding_count === null
                ? "not assessed"
                : `${run.finding_count} ${run.finding_count === 1 ? "Finding" : "Findings"}`;
              return (
                <li key={run.run_id}>
                  <a
                    className="run-link"
                    href={href}
                    onClick={(e) => { e.preventDefault(); navigate(href); }}
                  >
                    <span className="run-target">{targetLabel(run.target)}</span>
                    <span className="run-status">{run.status}</span>
                    <span className="run-meta">
                      <span>{provenance(run.mode) ?? run.mode}</span>
                      <span>{findings}</span>
                      <span>{formatDateTime(run.started_at)}</span>
                    </span>
                  </a>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
