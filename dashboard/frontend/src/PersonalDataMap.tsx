import { useMemo, useState } from "react";
import type { Report } from "./types";

const OPERATIONS = ["Collect", "Store", "Log", "Transfer", "Expose", "Erase"];

function opsOf(entry: Report["personal_data_map"][number]): string[] {
  return [...new Set(entry.operations.map((o) => o.operation))];
}

export function PersonalDataMap({ report }: { report: Report }) {
  const [cell, setCell] = useState<{ category: string; op: string } | null>(null);
  const [onlyFindings, setOnlyFindings] = useState(false);

  const withFinding = useMemo(
    () => new Set(report.findings.flatMap((f) => (f.personal_data_element ? [f.personal_data_element.name] : []))),
    [report.findings],
  );
  const categories = useMemo(() => [...new Set(report.personal_data_map.map((m) => m.element.data_category))].sort(), [report.personal_data_map]);
  const knownOps = useMemo(() => {
    const extra = new Set(report.personal_data_map.flatMap((m) => opsOf(m)).filter((o) => !OPERATIONS.includes(o)));
    return [...OPERATIONS, ...extra];
  }, [report.personal_data_map]);

  const grid = useMemo(() => {
    const g = new Map<string, { n: number; hit: number }>();
    for (const m of report.personal_data_map) {
      for (const op of opsOf(m)) {
        const key = `${m.element.data_category}|${op}`;
        const c = g.get(key) ?? { n: 0, hit: 0 };
        c.n += 1;
        if (withFinding.has(m.element.name)) c.hit += 1;
        g.set(key, c);
      }
    }
    return g;
  }, [report.personal_data_map, withFinding]);

  const rows = report.personal_data_map.filter((m) => {
    if (onlyFindings && !withFinding.has(m.element.name)) return false;
    if (!cell) return true;
    return m.element.data_category === cell.category && opsOf(m).includes(cell.op);
  });

  return (
    <section id="personal-data-map" aria-label="Personal Data Map" className="panel">
      <header className="panel-head">
        <h2>Personal Data Map</h2>
        <p>Every Personal Data Element against the Processing Operations applied to it, whether or not a Finding arises.</p>
      </header>
      {categories.length > 0 && (
        <div className="matrix-wrap">
        <div
          className="matrix"
          style={{ gridTemplateColumns: `minmax(8rem, 11rem) repeat(${knownOps.length}, minmax(3rem, 1fr))` }}
          role="group"
          aria-label="Elements by Data Category and Processing Operation"
        >
          <span />
          {knownOps.map((op) => <span className="mx-h" key={op}>{op}</span>)}
          {categories.map((category) => (
            <MatrixRow key={category} category={category} ops={knownOps} grid={grid} cell={cell} onCell={setCell} />
          ))}
        </div>
        </div>
      )}
      <div className="map-tools">
        <label className="check" style={{ alignItems: "center" }}>
          <input type="checkbox" checked={onlyFindings} onChange={(e) => setOnlyFindings(e.target.checked)} />
          Only Elements with a Finding
        </label>
        <span className="key-note"><span className="swatch" style={{ background: "var(--accent-bg)", border: "1px solid var(--line-strong)" }} /> Elements, no Finding</span>
        <span className="key-note"><span className="swatch" style={{ background: "var(--sev-high-bg)", border: "1px solid var(--line-strong)" }} /> At least one Finding</span>
        {cell ? (
          <button type="button" className="btn btn-sm" onClick={() => setCell(null)}>
            Clear: {cell.category} · {cell.op}
          </button>
        ) : <span className="muted">Select a cell to filter the table.</span>}
        <span className="muted" style={{ marginLeft: "auto" }}>{rows.length} of {report.personal_data_map.length} Elements</span>
      </div>
      <div className="table-wrap">
        <table data-testid="personal-data-map">
          <thead>
            <tr>
              <th>Element</th>
              <th>Data Category</th>
              <th>Processing Operations</th>
              <th>Finding</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((m) => (
              <tr key={m.element.name} data-testid="map-row">
                <td className="mono">{m.element.name}</td>
                <td>{m.element.data_category}</td>
                <td>
                  <div className="chips">
                    {opsOf(m).length ? opsOf(m).map((o) => <span className="chip" key={o}>{o}</span>) : <span className="muted">—</span>}
                  </div>
                </td>
                <td>{withFinding.has(m.element.name) ? <span className="chip chip-bad">Yes</span> : <span className="muted">No Finding</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="empty">No Elements match the current filter.</p>}
      </div>
    </section>
  );
}

function MatrixRow(props: {
  category: string;
  ops: string[];
  grid: Map<string, { n: number; hit: number }>;
  cell: { category: string; op: string } | null;
  onCell: (c: { category: string; op: string } | null) => void;
}) {
  return (
    <>
      <span className="mx-r">{props.category}</span>
      {props.ops.map((op) => {
        const c = props.grid.get(`${props.category}|${op}`);
        const on = props.cell?.category === props.category && props.cell.op === op;
        return (
          <button
            key={op}
            type="button"
            disabled={!c}
            aria-pressed={on}
            aria-label={`${props.category}, ${op}: ${c ? `${c.n} Elements, ${c.hit} with a Finding` : "none"}`}
            className={`mx-c${c ? (c.hit ? " hit" : " has") : ""}`}
            onClick={() => props.onCell(on ? null : { category: props.category, op })}
          >
            {c ? c.n : ""}
          </button>
        );
      })}
    </>
  );
}
