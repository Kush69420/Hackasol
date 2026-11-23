import { useEffect, useMemo, useRef, useState } from "react";
import {
  Check, Download, FileSearch, FlaskConical, Gavel, LayoutDashboard, ListChecks, Map as MapIcon,
  Moon, ScanSearch, ShieldCheck, Sun, Type, Wrench,
} from "lucide-react";
import { Band, LegalViewData, Report, ScanEvent } from "./types";
import { LiveProbes } from "./LiveProbes";
import { FixPatches } from "./FixPatches";
import { LegalView } from "./LegalView";
import { ConsentAssessment } from "./ConsentAssessment";
import { Overview, sortFindings } from "./Overview";
import { Findings } from "./Findings";
import { PersonalDataMap } from "./PersonalDataMap";
import { orderRecordings, provenance, targetLabel } from "./ui";

const STAGES: [string, string][] = [
  ["inventory", "Inventory"],
  ["elements", "Personal Data Elements"],
  ["data_flows", "Data Flows"],
  ["findings", "Findings"],
];
const FORMATS = [
  ["json", "JSON"],
  ["md", "Markdown"],
  ["html", "HTML"],
  ["pdf", "PDF"],
] as const;

type Theme = "light" | "dark";
function readPref(key: string): string | null {
  try { return window.localStorage.getItem(key); } catch { return null; }
}
function writePref(key: string, value: string) {
  try { window.localStorage.setItem(key, value); } catch { /* storage unavailable */ }
}

export function App() {
  const [target, setTarget] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<ScanEvent[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [legal, setLegal] = useState<LegalViewData | null>(null);
  const [legalError, setLegalError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [bandFilter, setBandFilter] = useState<Band | null>(null);
  const [activeReplay, setActiveReplay] = useState<string | null>(null);
  const [recordings, setRecordings] = useState<string[]>([]);
  const [theme, setTheme] = useState<Theme>(() => (readPref("dpdp-theme") === "dark" ? "dark" : "light"));
  const [large, setLarge] = useState<boolean>(() => readPref("dpdp-scale") === "large");
  const source = useRef<EventSource | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    writePref("dpdp-theme", theme);
  }, [theme]);
  useEffect(() => {
    document.documentElement.dataset.scale = large ? "large" : "normal";
    writePref("dpdp-scale", large ? "large" : "normal");
  }, [large]);

  useEffect(() => () => source.current?.close(), []);
  useEffect(() => {
    fetch("/api/replays")
      .then((r) => (r.ok ? r.json() : { recordings: [] }))
      .then((d: { recordings: string[] }) => setRecordings(orderRecordings([...new Set(["juice-shop", ...d.recordings])])))
      .catch(() => setRecordings(["juice-shop"]));
  }, []);

  const terminal = events.find((e) => e.type !== "stage");
  const status = !runId ? null : terminal ? terminal.type : "running";
  const mode = events.length ? events[events.length - 1].mode : undefined;

  // The Legal View feeds both the overview summary and its own section, so it is fetched once here.
  useEffect(() => {
    setLegal(null);
    setLegalError(null);
    if (!runId || !report) return;
    let cancelled = false;
    fetch(`/api/scans/${runId}/legal`)
      .then(async (response) => {
        if (!response.ok) throw new Error(`Legal view unavailable (${response.status})`);
        const body = (await response.json()) as LegalViewData;
        if (!cancelled) setLegal(body);
      })
      .catch((e: Error) => !cancelled && setLegalError(e.message));
    return () => { cancelled = true; };
  }, [runId, report === null]); // eslint-disable-line react-hooks/exhaustive-deps

  async function start(url: string, body?: unknown, replay?: string) {
    source.current?.close();
    setBusy(true);
    setError(null);
    setEvents([]);
    setReport(null);
    setSelected(null);
    setBandFilter(null);
    setRunId(null);
    setActiveReplay(replay ?? null);
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
            if (r.ok) {
              const loaded = (await r.json()) as Report;
              setReport(loaded);
              setSelected(sortFindings(loaded.findings)[0]?.id ?? null);
            } else setError(`Report could not be loaded (${r.status})`);
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

  const sections = useMemo(() => {
    if (!report) return [];
    const list: { id: string; label: string; icon: typeof Check; count?: number }[] = [
      { id: "overview", label: "Overview", icon: LayoutDashboard },
      { id: "findings", label: "Findings", icon: FileSearch, count: report.findings.length },
      { id: "personal-data-map", label: "Personal Data Map", icon: MapIcon, count: report.personal_data_map.length },
      { id: "consent", label: "Consent Assessment", icon: ListChecks },
      { id: "legal", label: "Legal view", icon: Gavel },
    ];
    if (mode !== "recorded") list.push({ id: "live-probes", label: "Live Probes", icon: FlaskConical });
    if (mode !== "recorded" && report.findings.some((f) => f.fix_patch)) list.push({ id: "fix-patches", label: "Fix Patches", icon: Wrench });
    return list;
  }, [report, mode]);
  const current = useScrollSpy(sections.map((s) => s.id));

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark"><ShieldCheck size={18} aria-hidden="true" /></span>
          <div>
            <div className="brand-name">DPDP Compliance Auditor</div>
            <div className="brand-sub">Act 2023 · Rules 2025</div>
          </div>
        </div>
        <nav className="nav" aria-label="Report sections">
          <div className="nav-label">Report</div>
          {sections.length === 0 && <p className="nav-empty">Sections appear once a scan completes.</p>}
          {sections.map(({ id, label, icon: Icon, count }) => (
            <a key={id} href={`#${id}`} aria-current={current === id ? "true" : undefined}>
              <Icon size={16} aria-hidden="true" />
              {label}
              {count !== undefined && <span className="count">{count}</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="toggles">
            <button
              type="button"
              className="btn btn-icon"
              aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
              title={theme === "dark" ? "Light theme" : "Dark theme"}
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
            </button>
            <button
              type="button"
              className="btn btn-icon"
              aria-pressed={large}
              aria-label="Large type for presenting"
              title="Large type for presenting"
              onClick={() => setLarge(!large)}
            >
              <Type size={16} aria-hidden="true" />
            </button>
          </div>
          <p className="foot-note">Evidence is masked before it is shown. Recorded scans never call the scanner.</p>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="switcher">
            <span className="switcher-label" id="recorded-label">Recorded scans</span>
            <div className="tabs" role="group" aria-labelledby="recorded-label">
              {recordings.length === 0 && <span className="muted" style={{ padding: "0.3rem 0.7rem" }}>None available</span>}
              {recordings.map((name) => (
                <button
                  key={name}
                  type="button"
                  className="tab"
                  disabled={busy}
                  aria-pressed={activeReplay === name}
                  aria-label={`Replay Mode (recorded ${targetLabel(name)} scan)`}
                  onClick={() => void start(`/api/replays/${name}`, undefined, name)}
                >
                  {targetLabel(name)}
                </button>
              ))}
            </div>
          </div>
          <form
            className="scan-form"
            onSubmit={(e) => {
              e.preventDefault();
              if (target.trim()) void start("/api/scans", { target: target.trim() });
            }}
          >
            <input
              className="field"
              aria-label="Target Application"
              placeholder="Local path or https Git URL"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={busy || !target.trim()}>
              <ScanSearch size={15} aria-hidden="true" />
              Scan
            </button>
          </form>
        </header>

        <main className="content">
          {error && <p className="callout" role="alert">{error}</p>}

          {!runId && !error && (
            <div className="panel start">
              <div className="start-inner">
                <span className="start-icon"><ScanSearch size={22} aria-hidden="true" /></span>
                <h1>Find where Personal Data is mishandled</h1>
                <p>
                  Pick a recorded scan above to replay it at its original pace, or enter a Target Application to scan.
                  Each Finding is traced from a Personal Data Element to a Processing Operation and mapped to the DPDP Act and Rules.
                </p>
              </div>
            </div>
          )}

          {runId && (
            <div className="run-head" aria-label="Run progress" role="region">
              <div className="run-top">
                <div className="stack" style={{ gap: "0.4rem" }}>
                  <div className="run-title">
                    <h1>{report ? targetLabel(report.target.name) : activeReplay ? targetLabel(activeReplay) : "Scanning…"}</h1>
                    {provenance(mode) && (
                      <span className={`badge badge-${mode}`} data-testid="provenance">{provenance(mode)}</span>
                    )}
                  </div>
                  <div className="run-meta">
                    {report && (
                      <span>
                        Target Application: <span className="mono">{report.target.name}</span>
                        {report.target.commit ? <> @ <span className="mono">{report.target.commit.slice(0, 12)}</span></> : null}
                      </span>
                    )}
                    <span data-testid="run-status" data-status={status ?? ""}>
                      Status: {status}
                      {terminal?.type === "completed" && ` (${terminal.finding_count} Findings)`}
                    </span>
                  </div>
                </div>
                {report && (
                  <div className="downloads" data-testid="downloads">
                    <span className="downloads-label">Report</span>
                    {FORMATS.map(([f, label]) => (
                      <a key={f} className="btn btn-sm" href={`/api/scans/${runId}/report/${f}`} download aria-label={`Download ${f.toUpperCase()}`}>
                        <Download size={14} aria-hidden="true" />
                        {label}
                      </a>
                    ))}
                  </div>
                )}
              </div>
              <ol className="stages" data-testid="stages">
                {STAGES.map(([key, label], i) => {
                  const ev = events.find((e) => e.type === "stage" && e.stage === key);
                  const prevDone = i === 0 || events.some((e) => e.type === "stage" && e.stage === STAGES[i - 1][0]);
                  const active = !ev && prevDone && status === "running";
                  return (
                    <li key={key} className={ev ? "done" : active ? "active" : "pending"} data-stage={key}>
                      <span className="stage-icon" aria-hidden="true">{ev ? <Check size={12} strokeWidth={3} /> : null}</span>
                      {label}
                      <span className="stage-ms">{ev ? `${ev.elapsed_ms} ms` : active ? "running" : "waiting"}</span>
                    </li>
                  );
                })}
              </ol>
              {terminal?.type === "failed" && (
                <p className="callout" role="alert" data-testid="failed">
                  Scan failed{terminal.message ? `: ${terminal.message}` : ""}
                </p>
              )}
            </div>
          )}

          {report && runId && (
            <>
              <Overview report={report} legal={legal} bandFilter={bandFilter} onBand={setBandFilter} />
              <Findings findings={report.findings} selected={selected} onSelect={setSelected} bandFilter={bandFilter} />
              <PersonalDataMap report={report} />
              <ConsentAssessment assessment={report.consent_assessment} replay={mode === "recorded"} />
              <LegalView legal={legal} error={legalError} />
              {mode !== "recorded" && <LiveProbes runId={runId} onReport={setReport} />}
              {mode !== "recorded" && <FixPatches runId={runId} findings={report.findings} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function useScrollSpy(ids: string[]): string | null {
  const [current, setCurrent] = useState<string | null>(null);
  const key = ids.join("|");
  useEffect(() => {
    if (!ids.length || typeof IntersectionObserver === "undefined") return;
    const seen = new Map<string, number>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const e of entries) seen.set(e.target.id, e.isIntersecting ? e.boundingClientRect.top : Infinity);
        const visible = [...seen.entries()].filter(([, top]) => top !== Infinity).sort((a, b) => a[1] - b[1]);
        if (visible.length) setCurrent(visible[0][0]);
      },
      { rootMargin: "-72px 0px -60% 0px" },
    );
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  return current ?? ids[0] ?? null;
}
