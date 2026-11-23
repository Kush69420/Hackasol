import type { ConsentAssessmentData } from "./types";
import { LlmCitations } from "./ProvisionView";

function probeClass(status: string): string {
  if (status === "Confirmed") return "chip-bad";
  if (status === "Not Confirmed") return "chip-good";
  return "chip-legal";
}

export function ConsentAssessment({ assessment, replay }: { assessment: ConsentAssessmentData | null; replay: boolean }) {
  const reasoning = assessment?.llm_reasoning;
  return (
    <section id="consent" aria-label="Consent Assessment" data-testid="consent-assessment" className="panel">
      <header className="panel-head">
        <h2>Consent Assessment</h2>
        <p>Whether consent is recorded, specific, enforced, withdrawable with comparable ease, and propagated to Data Processors.</p>
      </header>
      {!assessment ? <p className="empty">Not assessed.</p> : (
        <div className="criteria divided">
          {assessment.criteria.map((row) => (
            <article key={row.criterion} data-testid="consent-criterion">
              <h3>{row.criterion}</h3>
              <p><span className="k">Applicability:</span> {row.applicability} — {row.reason}</p>
              <p className="assess">Assessment: {row.assessment}</p>
              <p><span className="k">Issue Types:</span> {row.issue_types.join(", ") || "none"}</p>
              <p><span className="k">Linked identifiers:</span> {row.linked_identifiers.join(", ") || "none"}</p>
              {row.step_counts && <p><span className="k">Static step counts:</span> <span className="mono">{JSON.stringify(row.step_counts)}</span></p>}
              {row.evidence.map((ev, index) => (
                <figure className="evidence" key={`${ev.file}:${ev.start_line}:${index}`}>
                  <figcaption>{ev.file}:{ev.start_line}{ev.end_line !== ev.start_line ? `-${ev.end_line}` : ""}</figcaption>
                  <pre>{ev.excerpt}</pre>
                </figure>
              ))}
              {row.live_probes && row.live_probes.length > 0 && (
                <div className="probe-block" data-testid="consent-live-probes">
                  {replay && <p>Past Live Probe results (Replay Mode); static assessments above are unchanged.</p>}
                  {row.live_probes.map((probe, index) => (
                    <div key={index} data-testid="consent-live-probe">
                      <p>
                        <strong>Live Probe</strong> ({assessment.live_probe_run?.target ?? "unknown target"} @ {assessment.live_probe_run?.commit?.slice(0, 12) ?? "unknown"}, {assessment.live_probe_run?.observed_at ?? "unknown time"}):{" "}
                        <span className={`chip ${probeClass(probe.status)}`}>{probe.status}</span> ({probe.meaning})
                      </p>
                      <p>{probe.assertion}: {probe.reason}</p>
                    </div>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
      {reasoning?.status === "assessed" && reasoning.value && (
        <div className="criteria" style={{ borderTop: "1px solid var(--line)" }}>
          <article data-testid="consent-llm-reasoning">
            <h3>LLM reasoning</h3>
            <p>{reasoning.value.assessment}</p>
            <LlmCitations ids={reasoning.value.citations} />
            {reasoning.value.criteria?.map((row) => (
              <div key={row.criterion}>
                <p>{row.criterion}: {row.reading} — {row.reason}</p>
                <LlmCitations ids={row.citations} />
              </div>
            ))}
          </article>
        </div>
      )}
    </section>
  );
}
