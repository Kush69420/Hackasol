"""accuracy/results.md renderer and the cache-only no-network guarantee."""
from auditor import accuracy as acc

REFERENCE = {"target": {"name": "t", "commit": "a" * 40}, "entries": [
    {"id": "REF-001", "issue_type": "SEC-01", "status": "confirmed", "file": "a", "start_line": 1, "end_line": 2},
    {"id": "REF-002", "issue_type": "SEC-01", "status": "confirmed", "file": "a", "start_line": 5, "end_line": 6},
    {"id": "REF-003", "issue_type": "SEC-08", "status": "confirmed", "file": "b", "start_line": 1, "end_line": 2},
    {"id": "REF-004", "issue_type": "SEC-08", "status": "not-determinable", "reason": "x", "file": "b",
     "start_line": 9, "end_line": 9}]}


def report(live_probe=None):
    row = {"tp": 1, "fp": 0, "fn": 0, "tn": 1, "precision": 1.0, "recall": 1.0}
    return {
        "target": {"name": "t", "commit": "a" * 40},
        "findings": [{"id": "SEC-01-x", "issue_type": "SEC-01", "live_probe": live_probe}],
        "accuracy": {
            "primary_target": {
                "target": "t", "commit": "a" * 40, "reference": "ref.json", "tp": 2, "fp": 1, "fn": 1,
                "precision": 0.6667, "recall": 0.6667,
                "matches": [{"finding_id": "SEC-01-x", "reference_id": "REF-001"},
                            {"finding_id": "SEC-08-y", "reference_id": "REF-003"}],
                "unmatched_predictions": [{"finding_id": "SEC-01-z", "issue_type": "SEC-01", "reason": "dup"}],
                "excluded_predictions": [], "unmatched_references": ["REF-002"], "excluded": []},
            "labelled_corpus": {"rules": [{"rule_id": "SEC-01-r", **row}], "totals": row},
            "llm": {"mode": "cache-only", "provider": "p", "model": "m", "prompt_version": "v1", "cache_hits": 3,
                    "cache_misses": 1, "not_assessed": 1, "reproduces_published_run": False,
                    "replay_problems": ["1 cache miss(es)"]},
            "method": "METHOD", "limitations": ["LIM"]}}


def test_results_markdown_numbers_ids_and_reproducibility():
    text = acc.render_results_markdown(report(), REFERENCE, command="dpdp-audit accuracy t", digest="d" * 64)
    assert "`dpdp-audit accuracy t`" in text and "d" * 64 in text and "pinned at `" + "a" * 40 in text
    assert "| SEC-01 | 1 | 1 | 1 | 0.5000 | 0.5000 | 0.5000 | not run |" in text
    assert "| SEC-08 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |" in text
    assert "| **Overall** | 2 | 1 | 1 | 0.6667 | 0.6667 | 0.6667 | not run |" in text
    assert "Matched (2): REF-001, REF-003" in text and "Missed (1): REF-002" in text
    assert "3 hit(s), 1 miss(es), 1 not assessed" in text and "Reproduces published run: no" in text
    assert "2 confirmed, 1 not-determinable" not in text and "(3 confirmed, 1 not-determinable" in text


def test_live_probe_column_is_separate_from_static_figures():
    probe = {"result": "Confirmed", "method": "GET", "route": "/", "reason": "r", "request": "q", "response": "s"}
    text = acc.render_results_markdown(report(probe), REFERENCE, command="c", digest="d")
    assert "| SEC-01 | 1 | 1 | 1 | 0.5000 | 0.5000 | 0.5000 | 1 confirmed, 0 refuted, 0 inconclusive |" in text
    assert "| **Overall** | 2 | 1 | 1 |" in text  # static counts unchanged by the probe


def test_cache_only_scan_never_contacts_a_provider(tmp_path):
    from auditor.llm import LLMSession

    class Network:
        name, model = "omp", "m"

        def available(self):
            raise AssertionError("provider probed in cache-only mode")

        def complete(self, *args):
            raise AssertionError("network provider called in cache-only mode")

    session = LLMSession(tmp_path, Network())
    with acc.forced_cache_only():
        session.probe()
    result = session.ask("triage", "def f(): pass")
    assert session.mode == "cache-only"
    assert result["status"] == "not assessed"  # a miss is never fabricated
    assert (session.cache_misses, session.not_assessed) == (1, 1)


def test_accuracy_records_public_reproducible_command(tmp_path, monkeypatch):
    from auditor import cli

    result = report()
    result["target"].update(kind="git", source="https://host/repo.git")
    result["llm"] = {"provider": "ollama", "model": "actual-model"}
    captured = {}
    monkeypatch.setattr(cli, "run_accuracy", lambda *a, **kw: result)
    monkeypatch.setattr(cli, "write_reports", lambda *a: None)
    monkeypatch.setattr(cli, "load_reference", lambda *a: REFERENCE)
    monkeypatch.setattr(cli, "write_results", lambda *a, **kw: captured.update(kw))
    url = "https://user:synthetic-token@host/repo.git"
    assert cli.main(["accuracy", url, "--results", str(tmp_path / "results.md")]) == 0
    command = captured["command"]
    assert "user:" not in command and "synthetic-token" not in command and "@host" not in command
    assert "https://host/repo.git" in command
    assert "--commit " + "a" * 40 in command
    assert "--provider ollama --model actual-model" in command
