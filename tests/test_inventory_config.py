"""Tests for the configuration and infrastructure inventory in auditor.analysers.config."""

import json
import shutil
from pathlib import Path

import pytest

from auditor.analysers.config import analyse_config
from auditor.exclusions import iter_target_files

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "inventory_config"
PINNED = REPO / "targets" / "juice-shop"
SECRET = "«SECRET»"
COOKIE_SECRET = "fixture-cookie-secret-0123456789"
JWT_SECRET = "fake-jwt-secret-for-fixture-only"
# .env is gitignored, so the test writes it into a copy of the fixture tree instead of shipping it.
ENV_TEXT = (
    "# fixture environment\n"
    "APP_NAME=fixture\n"
    f'JWT_SECRET="{JWT_SECRET}"\n'
    "export DATABASE_NAME=fixture_db  # inline comment\n"
)


def _run(root: Path) -> dict:
    paths, _ = iter_target_files(root, "juice-shop")
    return analyse_config(root, [path.relative_to(root).as_posix() for path in paths])


def _span(coord: dict) -> tuple[str, int, int]:
    return coord["file"], coord["start_line"], coord["end_line"]


def _by_type(records: list[dict], rtype: str, name: str) -> list[dict]:
    return [record for record in records if (record["type"], record["name"]) == (rtype, name)]


def _leaf_keys(value, prefix: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _leaf_keys(item, prefix + (key,))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _leaf_keys(item, prefix + (str(index),))
    else:
        yield ".".join(prefix)


@pytest.fixture
def fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "target"
    shutil.copytree(FIXTURE, root)
    (root / ".env").write_text(ENV_TEXT, encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def pinned() -> dict:
    if not PINNED.is_dir():
        pytest.skip("targets/juice-shop is not checked out")
    return _run(PINNED)


def test_dockerfile_final_stage_user_and_ports(fixture_root):
    [dockerfile] = _run(fixture_root)["docker"]
    assert [(s["name"], s["base_image"], _span(s["source"])) for s in dockerfile["stages"]] == [
        ("installer", "node:24", ("Dockerfile", 2, 2)),
        ("1", "gcr.io/distroless/nodejs24-debian13", ("Dockerfile", 9, 9)),
    ]
    assert dockerfile["final_user"] == "65532"
    assert _span(dockerfile["final_user_source"]) == ("Dockerfile", 14, 14)
    assert dockerfile["expose"] == ["3000", "8080/tcp"]
    assert [_span(s) for s in dockerfile["expose_sources"]] == [("Dockerfile", 12, 12), ("Dockerfile", 13, 13)]
    assert _span(dockerfile["source"]) == ("Dockerfile", 1, 15)


def test_config_leaves_use_dotted_keys_and_mask_secrets(fixture_root):
    leaves = _run(fixture_root)["config_files"]
    assert {(r["key"], r["value"], _span(r["source"])) for r in leaves} == {
        ("application.domain", "example.test", ("config/app.yml", 3, 3)),
        ("application.port", "3000", ("config/app.yml", 4, 4)),
        ("application.cookie.secret", SECRET, ("config/app.yml", 6, 6)),
        ("application.features.0.name", "alpha", ("config/app.yml", 8, 8)),
        ("application.features.0.enabled", "true", ("config/app.yml", 9, 9)),
    }


def test_app_json_leaves_use_dotted_keys(fixture_root):
    leaves = _run(fixture_root)["app_json"]
    assert {r["file"] for r in leaves} == {"app.json"}
    assert {(r["key"], r["value"], r["source"]["start_line"]) for r in leaves} == {
        ("name", "fixture-app", 2),
        ("engines.node", "24.x", 4),
        ("keywords.0", "fixture", 7),
        ("keywords.1", "inventory", 8),
    }


def test_env_entries_mask_secret_values(fixture_root):
    entries = _run(fixture_root)["env_files"]
    assert {(r["key"], r["value_masked"], r["source"]["start_line"]) for r in entries} == {
        ("APP_NAME", "fixture", 2),
        ("JWT_SECRET", SECRET, 3),
        ("DATABASE_NAME", "fixture_db", 4),
    }


def test_terraform_records_merge_identical_declarations(fixture_root):
    records = _run(fixture_root)["terraform"]
    assert len(records) == 6

    [provider] = _by_type(records, "provider", "aws")
    assert provider["attributes"] == {"region": "var.aws_region"}
    assert provider["facts"] == {"region": "eu-west-1"}
    assert sorted(_span(s) for s in provider["sources"]) == [
        ("infrastructure/terraform/main.tf", 1, 3),
        ("terraform/main.tf", 1, 3),
    ]

    [variable] = _by_type(records, "variable", "aws_region")
    assert variable["attributes"] == {"type": "string", "default": "eu-west-1"}
    assert variable["facts"] == {}
    assert sorted(_span(s) for s in variable["sources"]) == [
        ("infrastructure/terraform/variables.tf", 1, 4),
        ("terraform/variables.tf", 1, 4),
    ]

    docker_builds = _by_type(records, "null_resource", "docker_build")
    assert len(docker_builds) == 2
    assert all(len(r["sources"]) == 1 for r in docker_builds)
    assert sorted(_span(r["sources"][0]) for r in docker_builds) == [
        ("infrastructure/terraform/main.tf", 5, 15),
        ("terraform/main.tf", 5, 13),
    ]

    [log_group] = _by_type(records, "aws_cloudwatch_log_group", "app")
    assert log_group["facts"] == {"region": "eu-west-1", "log_group": "/ecs/fixture", "retention_in_days": 30}
    assert sorted(_span(s) for s in log_group["sources"]) == [
        ("infrastructure/terraform/main.tf", 17, 20),
        ("terraform/main.tf", 15, 18),
    ]

    [security_group] = _by_type(records, "aws_security_group", "ecs")
    assert security_group["facts"] == {
        "region": "eu-west-1",
        "ingress": [
            {
                "from_port": 3000,
                "to_port": 3000,
                "protocol": "tcp",
                "source_security_group": ["aws_security_group.alb.id"],
            }
        ],
        "egress": [{"from_port": 0, "to_port": 0, "protocol": "-1", "cidr_blocks": ["0.0.0.0/0"]}],
    }
    assert sorted(_span(s) for s in security_group["sources"]) == [
        ("infrastructure/terraform/main.tf", 22, 39),
        ("terraform/main.tf", 20, 37),
    ]


def test_excluded_files_never_populate_a_collection(tmp_path):
    root = tmp_path / "target"
    shutil.copytree(FIXTURE, root)
    sentinel = root / "data" / "static" / "codefixes" / "iacLeakedKeyChallenge_x.tf"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text(
        'resource "aws_iam_access_key" "sentinel" {\n  user = "sentinel-user"\n}\n',
        encoding="utf-8",
    )
    dumped = json.dumps(_run(root))
    assert "codefixes" not in dumped
    assert "sentinel" not in dumped


def test_secret_values_never_reach_the_output(fixture_root):
    dumped = json.dumps(_run(fixture_root))
    assert COOKIE_SECRET not in dumped
    assert JWT_SECRET not in dumped


def test_pinned_dockerfile_runs_as_nonroot_on_distroless(pinned):
    [dockerfile] = [d for d in pinned["docker"] if d["file"] == "Dockerfile"]
    assert dockerfile["final_user"] == "65532"
    assert dockerfile["expose"] == ["3000"]
    assert dockerfile["stages"][-1]["base_image"].startswith("gcr.io/distroless/nodejs24")


def test_pinned_docker_build_appears_in_both_trees(pinned):
    docker_builds = _by_type(pinned["terraform"], "null_resource", "docker_build")
    assert len(docker_builds) == 2
    assert all(_span(s)[1] == 5 for r in docker_builds for s in r["sources"])


def test_pinned_ecs_service_merges_across_trees(pinned):
    [service] = _by_type(pinned["terraform"], "aws_ecs_service", "juice_shop")
    assert len(service["sources"]) == 2
    assert service["facts"]["assign_public_ip"] is True


def test_pinned_networking_resources_appear_in_both_trees(pinned):
    networking = [
        record
        for record in pinned["terraform"]
        if any(s["file"] == "terraform/networking.tf" for s in record["sources"])
    ]
    assert networking
    assert all(len(record["sources"]) == 2 for record in networking)


def test_pinned_private_key_is_masked(pinned):
    [certificate] = _by_type(pinned["terraform"], "aws_iam_server_certificate", "juice_shop_tls")
    assert certificate["attributes"]["private_key"] == SECRET
    dumped = json.dumps(pinned)
    assert "PRIVATE KEY-----" not in dumped
    assert "MIICXAIBAAK" not in dumped


def test_pinned_config_files_cover_every_config_yaml(pinned):
    expected = {
        path.relative_to(PINNED).as_posix()
        for path in (PINNED / "config").iterdir()
        if path.suffix in (".yml", ".yaml")
    }
    assert {r["file"] for r in pinned["config_files"]} == expected


def test_pinned_app_json_keys_match_the_document(pinned):
    document = json.loads((PINNED / "app.json").read_text(encoding="utf-8"))
    assert {r["key"] for r in pinned["app_json"]} == set(_leaf_keys(document))


def test_pinned_env_files_are_empty_and_codefixes_are_absent(pinned):
    assert pinned["env_files"] == []
    assert "data/static/codefixes" not in json.dumps(pinned)
