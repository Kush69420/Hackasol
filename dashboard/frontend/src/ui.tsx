import type { ReactNode } from "react";
import type { Band } from "./types";

export const BAND_LABEL: Record<Band, string> = { critical: "Critical", high: "High", medium: "Medium", low: "Low" };

export function SeverityBadge({ band }: { band: Band }) {
  return (
    <span className={`badge sev sev-${band}`}>
      <span className={`dot dot-${band}`} aria-hidden="true" />
      {band}
    </span>
  );
}

export function provenance(mode: string | undefined): string | null {
  if (mode === "live") return "Live";
  if (mode === "cache-only") return "Cache-only";
  if (mode === "recorded") return "Replay Mode";
  return null;
}

const TARGET_LABELS: Record<string, string> = {
  "juice-shop": "Juice Shop",
  "juice-shop-fork": "Juice Shop (fork)",
  "ai-kyc-platform": "ai-kyc-platform",
  trackmyrupee: "TrackMyRupee",
  "singharya-e-kyc": "singharya E-KYC",
};
export function targetLabel(name: string): string {
  return TARGET_LABELS[name] ?? name;
}
/** Lead with the two Targets the demo features, keep the rest in their served order. */
export function orderRecordings(names: string[]): string[] {
  const lead = ["juice-shop", "ai-kyc-platform"];
  return [...lead.filter((n) => names.includes(n)), ...names.filter((n) => !lead.includes(n))];
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "not stated";
  const d = new Date(`${iso}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}

export function formatCrore(n: number): string {
  return `₹${n.toLocaleString("en-IN")} crore`;
}

export function Panel(props: { id?: string; label: string; testId?: string; title: ReactNode; note?: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section id={props.id} aria-label={props.label} data-testid={props.testId} className="panel">
      <header className="panel-head">
        <h2>{props.title}</h2>
        {props.note ? <p>{props.note}</p> : null}
        {props.actions}
      </header>
      {props.children}
    </section>
  );
}
