"""Before/after comparison of two Report JSON files (demo step 8). Reads files only."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def finding_key(finding: dict) -> tuple:
    """Identity that survives line shifts: Issue Type, Rules fired, Element and Evidence files."""
    element = (finding["personal_data_element"] or {}).get("name")
    return (finding["issue_type"], tuple(sorted(finding["rules_fired"])), element,
            tuple(sorted({e["file"] for e in finding["evidence"]})))


def compare(before: dict, after: dict) -> dict:
    old, new = ({finding_key(f): f["id"] for f in report["findings"]} for report in (before, after))
    for report, keyed in ((before, old), (after, new)):
        if len(keyed) != len(report["findings"]):
            raise ValueError("Findings are not uniquely identifiable for comparison")
    return {
        "before_revision": before["target"]["commit"], "after_revision": after["target"]["commit"],
        "gone": sorted(old[k] for k in old.keys() - new.keys()),
        "new": sorted(new[k] for k in new.keys() - old.keys()),
        "persisting": sorted(f"{old[k]} -> {new[k]}" for k in old.keys() & new.keys()),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: compare_reports.py BEFORE.json AFTER.json", file=sys.stderr)
        return 2
    result = compare(*(json.loads(Path(p).read_text(encoding="utf-8")) for p in argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
