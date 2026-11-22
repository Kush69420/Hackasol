"""ScanContext: everything a Rule may read, built once per scan (or per Labelled Corpus fixture)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from auditor.analysers.log_flows import log_operations
from auditor.classify import classify, extract_elements
from auditor.datamap import build_personal_data_map
from auditor.evidence import evidence as _evidence
from auditor.exclusions import iter_target_files
from auditor.exposure import ExposureDecision, decide_exposure
from auditor.flows import trace_flows
from auditor.inventory import build_inventory
from auditor.semgrep import operation_steps, run_semgrep

REPO_ROOT = Path(__file__).resolve().parents[2]
SEMGREP_DIR = REPO_ROOT / "rules" / "semgrep"

# The model that represents a Data Principal's account; a POST creating it without an
# authentication middleware is open self-registration (Exposure: Public, ADR 0002 / issue #3).
PRINCIPAL_MODELS = ("User",)


@dataclass
class ScanContext:
    root: Path
    files: list[Path]
    inventory: dict
    elements: list[dict]
    flows: list[dict]
    semgrep: list[dict]
    steps_by_element: dict[str, list[dict]]
    personal_data_map: list[dict]
    llm: object | None = None
    _elements_by_id: dict[str, dict] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._elements_by_id = {e["id"]: e for e in self.elements}

    # ---- lookups -------------------------------------------------------------------------
    @property
    def rel_files(self) -> list[str]:
        return [p.relative_to(self.root).as_posix() for p in self.files]

    def evidence(self, coord: dict) -> dict:
        return _evidence(self.root, coord)

    def element(self, element_id: str) -> dict | None:
        return self._elements_by_id.get(element_id)

    def classified(self) -> list[dict]:
        return [e for e in self.elements if e["data_category"]]

    def steps(self, element_id: str) -> list[dict]:
        return self.steps_by_element.get(element_id, [])

    def semgrep_matches(self, rule_id: str) -> list[dict]:
        return [m for m in self.semgrep if m["rule_id"].split(".")[-1] == rule_id]

    def routes(self, method: str | None = None, path: str | None = None) -> list[dict]:
        return [r for r in self.inventory["routes"]
                if (method is None or r["method"] == method)
                and (path is None or r["normalised_path"] == path)]

    def model(self, name: str) -> dict | None:
        return next((m for m in self.inventory["models"] if m["name"] == name), None)

    def schema_element(self, element_id: str) -> dict | None:
        """Element in the Report schema shape ({name, data_category, evidence})."""
        e = self.element(element_id)
        if not e or not e["data_category"]:
            return None
        return {"name": e["id"], "data_category": e["data_category"], "evidence": self.evidence(e["source"])}

    def flow_steps(self, element_id: str) -> list[dict]:
        """Ordered schema Data Flow steps for an Element."""
        return [{"operation": s["operation"], "evidence": self.evidence(s["source"]),
                 "note": f"{s['stage']}; {s['origin']}; {s['relation']}" + (f"; {s['note']}" if s.get("note") else "")}
                for s in self.steps(element_id)]

    # ---- Exposure ------------------------------------------------------------------------
    def open_registration(self) -> list[dict]:
        """Evidence of open self-registration: POST creating a principal model with no authentication."""
        out = []
        for r in self.routes("POST"):
            principal = r.get("model") in PRINCIPAL_MODELS or any(
                r["normalised_path"] == f"/api/{m}s" for m in PRINCIPAL_MODELS)
            if principal and not self.is_authenticated(r):
                out.append(self.evidence(r["registration"]))
        return out

    @staticmethod
    def is_authenticated(route: dict) -> bool:
        return any(m["role"] == "authentication" for m in route["middleware"])

    def route_exposure(self, route: dict) -> ExposureDecision:
        """Exposure of a route's response, from its middleware chain and open registration."""
        reg = self.evidence(route["registration"])
        if not self.is_authenticated(route):
            return decide_exposure(authenticated=False, route_evidence=[reg])
        auth = [self.evidence(m["source"]) for m in route["middleware"] if m["role"] == "authentication"]
        opened = self.open_registration()
        if opened:
            return decide_exposure(authenticated=True, open_registration_evidence=[reg, *auth[:1], *opened])
        return decide_exposure(authenticated=True, closed_membership=[reg, *auth[:1]])


def build_context(root: Path, profile: str, llm=None) -> ScanContext:
    """Run the deterministic core (inventory, Elements, Data Flows, Semgrep) for one Target."""
    files, _ = iter_target_files(root, profile)
    inventory = build_inventory(root, files, None)
    elements = classify(extract_elements(inventory), llm=llm)
    flows = trace_flows(root, files, inventory)
    rel = [p.relative_to(root).as_posix() for p in files]
    semgrep = run_semgrep(root, rel, [SEMGREP_DIR])
    steps = log_operations(inventory, elements) + operation_steps(
        [m for m in semgrep if m["metadata"].get("kind") == "operation"], elements)
    pdm, ordered = build_personal_data_map(root, elements, flows, steps)
    return ScanContext(root=root, files=files, inventory=inventory, elements=elements, flows=flows,
                       semgrep=semgrep, steps_by_element=ordered, personal_data_map=pdm, llm=llm)
