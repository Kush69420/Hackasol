import { useRef, useState, type ChangeEvent, type DragEvent, type FormEvent, type KeyboardEvent } from "react";
import { ArrowRight, Code, FileUp, Globe, ShieldCheck, X } from "lucide-react";
import { navigate } from "./route";

type Tab = "git" | "file" | "snippet";

const TABS: { id: Tab; label: string; icon: typeof Globe }[] = [
  { id: "git", label: "Git URL", icon: Globe },
  { id: "file", label: "File", icon: FileUp },
  { id: "snippet", label: "Code snippet", icon: Code },
];
const LANGUAGES: [string, string][] = [
  ["python", "Python"], ["javascript", "JavaScript"], ["typescript", "TypeScript"], ["java", "Java"],
  ["go", "Go"], ["ruby", "Ruby"], ["php", "PHP"], ["sql", "SQL"], ["yaml", "YAML"], ["json", "JSON"],
  ["env", ".env"], ["other", "Other"],
];
const FILE_EXTENSIONS = [
  ".zip", ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".go", ".rb", ".php", ".sql",
  ".yaml", ".yml", ".json", ".env", ".toml", ".ini", ".cfg", ".conf", ".properties", ".xml",
];
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_SNIPPET_BYTES = 200 * 1024;

/** Returns an inline error for a non-empty Git URL, or null when it is usable. */
function gitUrlError(value: string): string | null {
  const v = value.trim();
  if (!/^https:\/\//i.test(v)) return "Use an https:// address, for example https://github.com/owner/repo.";
  if (/\s/.test(v)) return "The URL cannot contain spaces.";
  try {
    const url = new URL(v);
    if (url.protocol !== "https:" || !url.hostname) throw new Error("invalid");
  } catch {
    return "This is not a valid https:// URL.";
  }
  return null;
}

function fileError(file: File): string | null {
  const name = file.name.toLowerCase();
  const supported = FILE_EXTENSIONS.some((ext) => name.endsWith(ext)) || /^\.env(\.[\w.-]+)?$/.test(name);
  if (!supported) return "This file type is not supported. Choose one source or config file, or a .zip.";
  if (file.size === 0) return "This file is empty.";
  if (file.size > MAX_FILE_BYTES) return `${file.name} is larger than 20 MB.`;
  return null;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

async function rejectionMessage(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* response was not JSON */
  }
  return `Request rejected (${res.status})`;
}

export function Home() {
  const [tab, setTab] = useState<Tab>("git");
  const tabRefs = useRef<Record<Tab, HTMLButtonElement | null>>({ git: null, file: null, snippet: null });
  const fileInput = useRef<HTMLInputElement>(null);

  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileProblem, setFileProblem] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const urlError = url.trim() ? gitUrlError(url) : null;
  const codeBytes = new TextEncoder().encode(code).length;
  const codeTooLarge = codeBytes > MAX_SNIPPET_BYTES;

  const ready =
    tab === "git" ? url.trim() !== "" && urlError === null
    : tab === "file" ? file !== null
    : code.trim() !== "" && !codeTooLarge;

  function selectTab(next: Tab) {
    setTab(next);
    setError(null);
  }

  function onTabKey(e: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next: number | null = null;
    if (e.key === "ArrowRight") next = (index + 1) % TABS.length;
    else if (e.key === "ArrowLeft") next = (index - 1 + TABS.length) % TABS.length;
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = TABS.length - 1;
    if (next === null) return;
    e.preventDefault();
    selectTab(TABS[next].id);
    tabRefs.current[TABS[next].id]?.focus();
  }

  function chooseFile(list: FileList | null) {
    setError(null);
    if (!list || list.length === 0) return;
    if (list.length > 1) {
      setFile(null);
      setFileProblem("Choose one file at a time, or a single .zip.");
      return;
    }
    const picked = list[0];
    const problem = fileError(picked);
    setFileProblem(problem);
    setFile(problem ? null : picked);
  }

  function clearFile() {
    setFile(null);
    setFileProblem(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    chooseFile(e.dataTransfer.files);
  }

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!ready || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      let res: Response;
      if (tab === "git") {
        res = await fetch("/api/scans", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: url.trim() }),
        });
      } else if (tab === "file") {
        const form = new FormData();
        form.append("file", file as File);
        res = await fetch("/api/scans/upload", { method: "POST", body: form });
      } else {
        res = await fetch("/api/scans/snippet", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code, language }),
        });
      }
      if (!res.ok) throw new Error(await rejectionMessage(res));
      const { run_id } = (await res.json()) as { run_id: string };
      // Leaves Home on success; the dashboard attaches to the run from the query string.
      navigate(`/dashboard?run=${encodeURIComponent(run_id)}`);
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <div className="home">
      <header className="home-top">
        <div className="brand">
          <span className="brand-mark"><ShieldCheck size={18} aria-hidden="true" /></span>
          <div>
            <div className="brand-name">DPDP Compliance Auditor</div>
            <div className="brand-sub">Act 2023 · Rules 2025</div>
          </div>
        </div>
      </header>

      <main className="home-main">
        <section className="home-hero" aria-labelledby="home-title">
          <h1 id="home-title">Find where Personal Data is mishandled</h1>
          <p className="lede">
            Audit a Target Application from a Git repository, a single file or a code snippet. Each Finding is traced
            from a Personal Data Element to a Processing Operation and mapped to the DPDP Act and Rules.
          </p>
        </section>

        <section className="panel home-panel" aria-labelledby="home-form-title">
          <div className="panel-head">
            <h2 id="home-form-title">Target Application</h2>
            <p>Choose one input type, then start the audit.</p>
          </div>

          <form className="home-form" onSubmit={submit} noValidate>
            <div className="tabs home-tabs" role="tablist" aria-label="Input type">
              {TABS.map(({ id, label, icon: Icon }, i) => (
                <button
                  key={id}
                  ref={(el) => { tabRefs.current[id] = el; }}
                  type="button"
                  role="tab"
                  id={`home-tab-${id}`}
                  aria-selected={tab === id}
                  aria-controls={`home-panel-${id}`}
                  tabIndex={tab === id ? 0 : -1}
                  className="tab"
                  onClick={() => selectTab(id)}
                  onKeyDown={(e) => onTabKey(e, i)}
                >
                  <Icon size={15} aria-hidden="true" />
                  {label}
                </button>
              ))}
            </div>

            <div className="home-pane" role="tabpanel" id="home-panel-git" aria-labelledby="home-tab-git" hidden={tab !== "git"}>
              <label className="home-label" htmlFor="home-url">Git URL</label>
              <input
                id="home-url"
                className="field home-input"
                type="url"
                inputMode="url"
                autoComplete="off"
                spellCheck={false}
                placeholder="https://github.com/owner/repo"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setError(null); }}
                aria-invalid={urlError ? true : undefined}
                aria-describedby={urlError ? "home-url-error" : "home-url-hint"}
              />
              {urlError
                ? <p id="home-url-error" className="home-error">{urlError}</p>
                : <p id="home-url-hint" className="home-hint">Must start with https://. Public repositories or URLs your account can read.</p>}
            </div>

            <div className="home-pane" role="tabpanel" id="home-panel-file" aria-labelledby="home-tab-file" hidden={tab !== "file"}>
              <span className="home-label" id="home-file-label">Source or config file, or .zip</span>
              <div
                className="home-drop"
                data-over={dragOver}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
              >
                <input
                  ref={fileInput}
                  id="home-file"
                  className="sr-only file-input"
                  type="file"
                  aria-labelledby="home-file-label"
                  aria-describedby="home-file-hint"
                  accept={FILE_EXTENSIONS.join(",")}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => chooseFile(e.target.files)}
                />
                <p>Drop one file here, or</p>
                <label className="btn btn-sm" htmlFor="home-file">Choose file</label>
                <p id="home-file-hint" className="home-hint">Up to 20 MB. One file per audit.</p>
              </div>
              {file && (
                <div className="home-file" role="group" aria-label="Selected file">
                  <FileUp size={16} aria-hidden="true" />
                  <span className="mono">{file.name}</span>
                  <span className="home-file-meta">{formatBytes(file.size)}</span>
                  <button type="button" className="btn btn-sm" onClick={clearFile}>
                    <X size={14} aria-hidden="true" />
                    Remove
                  </button>
                </div>
              )}
              {fileProblem && <p className="home-error" role="alert">{fileProblem}</p>}
            </div>

            <div className="home-pane" role="tabpanel" id="home-panel-snippet" aria-labelledby="home-tab-snippet" hidden={tab !== "snippet"}>
              <label className="home-label" htmlFor="home-lang">Language</label>
              <select
                id="home-lang"
                className="field home-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {LANGUAGES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
              <label className="home-label" htmlFor="home-code">Code</label>
              <textarea
                id="home-code"
                className="home-code"
                spellCheck={false}
                autoCapitalize="off"
                autoCorrect="off"
                placeholder="Paste the code to audit"
                value={code}
                onChange={(e) => { setCode(e.target.value); setError(null); }}
                aria-invalid={codeTooLarge ? true : undefined}
                aria-describedby="home-code-count"
              />
              <p id="home-code-count" className="home-counter" data-over={codeTooLarge}>
                {(codeBytes / 1024).toFixed(1)} of 200 KB
              </p>
              {codeTooLarge && <p className="home-error" role="alert">The snippet is larger than 200 KB. Remove some code to continue.</p>}
            </div>

            <div className="home-actions">
              {error && <p className="callout" role="alert">{error}</p>}
              <button type="submit" className="btn btn-primary home-submit" disabled={!ready || submitting} aria-busy={submitting}>
                {submitting ? "Starting audit…" : "Audit"}
                {!submitting && <ArrowRight size={15} aria-hidden="true" />}
              </button>
            </div>
          </form>
        </section>

        <p className="home-foot">
          Already have a report?{" "}
          <a href="/dashboard" onClick={(e) => { e.preventDefault(); navigate("/dashboard"); }}>
            Open the dashboard
          </a>{" "}
          to replay a recorded scan.
        </p>
      </main>
    </div>
  );
}
