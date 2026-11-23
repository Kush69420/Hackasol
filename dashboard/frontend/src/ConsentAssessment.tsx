import type { ConsentAssessmentData } from "./types";
import { LlmCitations } from "./ProvisionView";

export function ConsentAssessment({ assessment, replay }: { assessment: ConsentAssessmentData | null; replay: boolean }) {
  const reasoning = assessment?.llm_reasoning;
  return (
    <section aria-label="Consent Assessment" data-testid="consent-assessment">
      <h2>Consent Assessment</h2>
      {!assessment ? <p>Not assessed.</p> : assessment.criteria.map((row) => (
        <article key={row.criterion} data-testid="consent-criterion">
          <h3>{row.criterion}</h3>
          <p>Applicability: {row.applicability} — {row.reason}</p>
          <p><strong>Assessment: {row.assessment}</strong></p>
          <p>Issue Types: {row.issue_types.join(", ") || "none"}</p>
          <p>Linked identifiers: {row.linked_identifiers.join(", ") || "none"}</p>
          {row.step_counts && <p>Static step counts: {JSON.stringify(row.step_counts)}</p>}
          {row.evidence.map((ev, index) => (
            <figure className="evidence" key={`${ev.file}:${ev.start_line}:${index}`}>
              <figcaption>{ev.file}:{ev.start_line}{ev.end_line !== ev.start_line ? `-${ev.end_line}` : ""}</figcaption>
              <pre>{ev.excerpt}</pre>
            </figure>
          ))}
          {row.live_probes && row.live_probes.length > 0 && (
            <blockquote data-testid="consent-live-probes">
              {replay && <p>Past Live Probe results (Replay Mode); static assessments above are unchanged.</p>}
              {row.live_probes.map((probe, index) => (
                <div key={index} data-testid="consent-live-probe">
                  <p><strong>Live Probe</strong> ({assessment.live_probe_run?.target ?? "unknown target"} @ {assessment.live_probe_run?.commit?.slice(0, 12) ?? "unknown"}, {assessment.live_probe_run?.observed_at ?? "unknown time"}): {probe.status} ({probe.meaning})</p>
                  <p>{probe.assertion}: {probe.reason}</p>
                </div>
              ))}
            </blockquote>
          )}
        </article>
      ))}
      {reasoning?.status === "assessed" && reasoning.value && (
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
      )}
    </section>
  );
}
