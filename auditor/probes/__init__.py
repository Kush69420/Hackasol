"""Bounded, value-free Live Probe observations for dedicated instances."""
from __future__ import annotations

import ipaddress
import json
import os
import subprocess
from urllib.parse import urlsplit
import secrets

import httpx
from auditor.probes.assessments import cookie_flags, transport

PIN = "c9f99228d9d56afb5f5ca7925376292f7fa44b13"


def image_metadata() -> dict:
    """When an image is claimed, reject missing or mismatched source revision."""
    image = os.environ.get("JUICE_SHOP_IMAGE")
    if not image:
        return {}
    try:
        result = subprocess.run(["docker", "image", "inspect", image], check=True, capture_output=True, text=True)
        inspected = json.loads(result.stdout)[0]
        revision = (inspected.get("Config", {}).get("Labels") or {}).get("org.opencontainers.image.revision")
        digest = inspected.get("Id")
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ValueError("unable to inspect claimed Juice Shop image") from exc
    if revision not in (PIN, PIN[:8]) or not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise ValueError("claimed Juice Shop image has missing or mismatched revision or digest")
    return {"image_revision": revision, "image_digest": digest}




def origin(value: str) -> str:
    url = urlsplit(value)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.path not in ("", "/") or url.query or url.fragment:
        raise ValueError("target must be an HTTP origin without credentials or a path")
    host = url.hostname.lower()
    try:
        host = ipaddress.ip_address(host).compressed
    except ValueError:
        pass
    port = url.port or (443 if url.scheme == "https" else 80)
    return f"{url.scheme}://{'[' + host + ']' if ':' in host else host}:{port}"


def authorize(target: str, allowed_origins: tuple[str, ...] = ()) -> str:
    normalized = origin(target)
    host = urlsplit(normalized).hostname
    try:
        loopback = ipaddress.ip_address(host).is_loopback
    except ValueError:
        loopback = host == "localhost"
    if not loopback and normalized not in {origin(item) for item in allowed_origins}:
        raise ValueError("target origin is not allowlisted")
    return normalized


class ProbeClient:
    """Only fixed routes may be requested; redirects and environment proxies are disabled."""
    ROUTES = {("GET", "/rest/memories"), ("POST", "/rest/memories"), ("POST", "/api/Users"),
              ("GET", "/api/SecurityQuestions"), ("POST", "/api/SecurityAnswers"),
              ("POST", "/rest/user/login"), ("GET", "/dataerasure"), ("POST", "/dataerasure")}

    def __init__(self, target: str, allowed_origins: tuple[str, ...] = (), limit: int = 16):
        self.target = authorize(target, allowed_origins)
        self.limit = limit
        self.count = 0
        self.accounts: dict[str, dict] = {}
        self.client = httpx.Client(follow_redirects=False, trust_env=False, timeout=5)

    def request(self, method: str, route: str, *, account: str | None = None, **kwargs):
        if (method, route) not in self.ROUTES:
            raise ValueError("route is not a registered Live Probe")
        if ((method != "GET" and route != "/api/Users") or route == "/dataerasure") and account not in self.accounts:
            raise ValueError("account was not created by this Auditor run")
        if account is not None and account in self.accounts:
            owner = self.accounts[account]
            if route == "/rest/user/login" and kwargs.get("json") != {"email": owner["email"], "password": owner["password"]}:
                raise ValueError("login does not belong to an Auditor-created account")
            if route == "/api/SecurityAnswers" and str(kwargs.get("json", {}).get("UserId")) != account:
                raise ValueError("security answer does not belong to an Auditor-created account")
            if route == "/dataerasure" and (not owner.get("token") or kwargs.get("headers", {}).get("Cookie") != "token=" + owner["token"]):
                raise ValueError("erasure session does not belong to an Auditor-created account")
            if method == "POST" and route == "/rest/memories" and (not owner.get("token") or kwargs.get("headers", {}).get("Authorization") != "Bearer " + owner["token"]):
                raise ValueError("memory session does not belong to an Auditor-created account")
        if self.count >= self.limit:
            raise ValueError("Live Probe request limit reached")
        self.count += 1
        response = self.client.request(method, self.target + route, **kwargs)
        if response.is_redirect:
            raise ValueError("redirects are not followed")
        return response

    def close(self):
        self.client.close()


def _result(result: str, route: str, reason: str, response: str) -> dict:
    return {"result": result, "method": "GET", "route": route, "reason": reason,
            "request": "Origin: [synthetic origin]", "response": response}


def _cross_account(client: ProbeClient, caption: str) -> str:
    """Read only the first created account's canary as a second created account."""
    email = f"dpdp-{secrets.token_hex(16)}@example.invalid"
    password = secrets.token_urlsafe(24)
    try:
        created = client.request("POST", "/api/Users", json={"email": email, "password": password, "passwordRepeat": password})
        data = created.json().get("data", {})
        account_id = data.get("id")
        if created.status_code not in (200, 201) or not isinstance(account_id, int) or data.get("email") != email:
            return "inconclusive"
        account = str(account_id)
        client.accounts[account] = {"email": email, "password": password}
        login = client.request("POST", "/rest/user/login", account=account, json={"email": email, "password": password})
        token = login.json().get("authentication", {}).get("token")
        if login.status_code != 200 or not isinstance(token, str) or not token:
            return "inconclusive"
        client.accounts[account]["token"] = token
        client.client.cookies.clear()
        response = client.request("GET", "/rest/memories", headers={"Authorization": "Bearer " + token})
        if response.status_code in (401, 403):
            return "Refuted"
        if response.status_code != 200:
            return "inconclusive"
        records = response.json().get("data")
        if not isinstance(records, list):
            return "inconclusive"
        return "Confirmed" if any(isinstance(record, dict) and record.get("caption") == caption for record in records) else "Refuted"
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return "inconclusive"


def _account_probes(client: ProbeClient) -> list[tuple]:
    """Use only an account and memory created by this run; discard response values."""
    email = f"dpdp-{secrets.token_hex(16)}@example.invalid"
    password = secrets.token_urlsafe(24)
    caption = secrets.token_hex(16)
    observations = []
    try:
        created = client.request("POST", "/api/Users", json={"email": email, "password": password, "passwordRepeat": password})
        data = created.json().get("data", {})
        account_id = data.get("id")
        if created.status_code not in (200, 201) or not isinstance(account_id, int) or data.get("email") != email:
            return []
        account = str(account_id)
        client.accounts[account] = {"email": email, "password": password}
        login = client.request("POST", "/rest/user/login", account=account, json={"email": email, "password": password})
        cookie_result, cookie_reason = cookie_flags(login.headers.get_list("set-cookie"))
        observations.append(("cookie-flags", "", 0, {"result": cookie_result, "method": "POST",
            "route": "/rest/user/login", "reason": cookie_reason,
            "request": "Authentication values: [masked]", "response": "Session cookie values: [masked]"}))
        token = login.json().get("authentication", {}).get("token")
        if login.status_code != 200 or not isinstance(token, str) or not token:
            return observations
        client.accounts[account]["token"] = token
        auth = {"Authorization": "Bearer " + token}
        upload = client.request("POST", "/rest/memories", account=account, headers=auth,
                                data={"caption": caption},
                                files={"image": ("canary.png", b"\x89PNG\r\n\x1a\n", "image/png")})
        if upload.status_code != 200:
            return observations
        client.client.cookies.clear()
        response = client.request("GET", "/rest/memories")
        records = response.json().get("data", []) if response.status_code == 200 else []
        own = next((item for item in records if isinstance(item, dict) and item.get("caption") == caption), None) if isinstance(records, list) else None
        if response.status_code == 200 and own:
            observations.append(("SEC-07", "routes/memory.ts", 24, _result(
                "Confirmed", "/rest/memories", "The Auditor-created memory was returned without authentication",
                "HTTP 200; Auditor-created record present; values: [masked]")))
            user = own.get("User")
            if isinstance(user, dict) and user.get("email") == email:
                observations.append(("SEC-08", "routes/memory.ts", 24, _result(
                    "Confirmed", "/rest/memories", "Nested account Personal Data was returned with the Auditor-created memory",
                    "HTTP 200; nested account email present; values: [masked]")))
            elif user is None or (isinstance(user, dict) and not any(key in user for key in ("email", "password", "totpSecret"))):
                observations.append(("SEC-08", "routes/memory.ts", 24, _result(
                    "Refuted", "/rest/memories", "The Auditor-created memory did not expose the checked account fields",
                    "HTTP 200; checked nested account fields absent; values: [masked]")))
        elif response.status_code in (401, 403):
            observations.append(("SEC-07", "routes/memory.ts", 24, _result(
                "Refuted", "/rest/memories", "Anonymous request was denied after successful setup",
                f"HTTP {response.status_code}; body: [masked]")))
        cross = _cross_account(client, caption)
        if cross != "inconclusive":
            existing = next((item for item in observations if item[0] == "SEC-07"), None)
            if cross == "Confirmed" and (not existing or existing[3]["result"] != "Confirmed"):
                if existing:
                    observations.remove(existing)
                observations.append(("SEC-07", "routes/memory.ts", 24, _result(
                    "Confirmed", "/rest/memories", "A second Auditor-created account received the first account's memory",
                    "Cross-account GET returned the first account's synthetic record; values: [masked]")))
            elif existing:
                existing[3]["response"] += f"; cross-account assertion: {cross}"
        elif any(item[0] == "SEC-07" and item[3]["result"] == "Refuted" for item in observations):
            observations = [item for item in observations if item[0] != "SEC-07"]
        # A cookie-clearing response alone is not evidence of erasure. The same
        # account must still authenticate after the ordinary erasure request.
        questions = client.request("GET", "/api/SecurityQuestions")
        choices = questions.json().get("data", [])
        if questions.status_code != 200 or not choices or not isinstance(choices[0].get("id"), int):
            return observations
        answer = secrets.token_hex(16)
        created_answer = client.request("POST", "/api/SecurityAnswers", account=account,
            json={"UserId": account_id, "SecurityQuestionId": choices[0]["id"], "answer": answer})
        if created_answer.status_code not in (200, 201):
            return observations
        form = client.request("GET", "/dataerasure", account=account, headers={"Cookie": "token=" + token})
        if form.status_code != 200:
            return observations
        erased = client.request("POST", "/dataerasure", account=account,
                                headers={"Cookie": "token=" + token}, data={"email": email, "securityAnswer": answer})
        if erased.status_code == 200:
            again = client.request("POST", "/rest/user/login", account=account, json={"email": email, "password": password})
            if again.status_code == 200 and again.json().get("authentication", {}).get("token"):
                observations.append(("RET-02", "routes/dataErasure.ts", 85,
                                     {"result": "Confirmed", "method": "POST", "route": "/dataerasure",
                                      "reason": "The Auditor-created account remained readable after its erasure request",
                                      "request": "Cookie and account values: [masked]",
                                      "response": "HTTP 200; subsequent account authentication succeeded; values: [masked]"}))
        return observations
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        return observations


def run(report: dict, target: str, allowed_origins: tuple[str, ...] = ()) -> list[dict]:
    """Evaluate observations with exact Evidence identities, without retaining values."""
    identity = report.get("target", {})
    if identity.get("name") == "trackmyrupee":
        from auditor.probes.trackmyrupee import PIN as CONSENT_PIN, run_browser
        if identity.get("commit") != CONSENT_PIN:
            raise ValueError("TrackMyRupee Report does not match the supported source revision")
        return run_browser(authorize(target, allowed_origins))
    if identity.get("name") != "juice-shop" or identity.get("commit") != PIN:
        raise ValueError("no registered Live Probe suite for this Target Application revision")
    metadata = image_metadata()
    client = ProbeClient(target, allowed_origins)
    observations = []
    responded = False
    # Never retain a previous run's outcome when this run cannot reproduce it.
    for finding in report.get("findings", []):
        if (finding.get("live_probe") or {}).get("route") in ("/rest/memories", "/dataerasure"):
            finding["live_probe"] = None
    try:
        try:
            response = client.request("GET", "/rest/memories", headers={"Origin": "https://probe.invalid"})
            responded = True
            if response.status_code < 500:
                cors = response.headers.get("access-control-allow-origin")
                result = "Confirmed" if cors == "*" else "Refuted"
                observations.append(("SEC-11", "server.ts", 185, _result(
                    result, "/rest/memories", "Wildcard CORS on the Personal Data route" if cors == "*" else "Wildcard CORS was not returned for the synthetic Origin",
                    f"HTTP {response.status_code}; Access-Control-Allow-Origin: {'*' if cors == '*' else '[not wildcard]'}; body: [masked]")))
        except (httpx.HTTPError, ValueError):
            pass
        observations.extend(_account_probes(client))
    finally:
        client.close()
    matched = []
    for issue, file, line, outcome in observations:
        if issue in ("SEC-07", "SEC-08"):
            outcome["request"] += "; setup: POST /api/Users (finale-generated; server.ts:540-543)"
        candidates = [f for f in report.get("findings", []) if f.get("issue_type") == issue and any(
            e.get("file") == file and e.get("start_line", 0) <= line <= e.get("end_line", 0)
            for e in f.get("evidence", []))]
        if issue == "SEC-11":
            candidates = [f for f in candidates if any(e.get("file") == "server.ts" and e.get("start_line") == 670 for e in f.get("evidence", []))]
        if not candidates and issue == "SEC-08" and outcome["result"] == "Confirmed":
            # The static mapper may merge both Rules into the SEC-07 Finding.
            # Re-enter the normal assembler with the shared source Evidence.
            from auditor.exposure import ExposureDecision
            from auditor.mapping import Match, assemble
            source = next((f for f in report.get("findings", []) if f.get("issue_type") == "SEC-07"
                           and "SEC-08-ts-nested-records" in f.get("rules_fired", [])
                           and any(e.get("file") == file and e.get("start_line") == line for e in f.get("evidence", []))
                           and any(e.get("file") == "server.ts" and e.get("start_line") == 670 for e in f.get("evidence", []))), None)
            if source:
                assembled = assemble([Match(rule_id="SEC-08-ts-nested-records", issue_type="SEC-08",
                    evidence=source["evidence"], classification=source["classification"],
                    base_vector=source["cvss"]["vector"].rsplit("/CR:", 1)[0],
                    element=source["personal_data_element"], data_category=source["data_category"],
                    protected_categories=(), processing_operation=source["processing_operation"],
                    data_flow=source["data_flow"], exposure=ExposureDecision(source["exposure"]["level"], source["exposure"]["derived_from"]))])
                report["observations"].extend(assembled.observations)
                report["findings"].extend(assembled.findings)
                candidates = assembled.findings
        outcome.update(metadata)
        if len(candidates) == 1 and outcome["result"] != "inconclusive":
            candidates[0]["live_probe"] = outcome
            matched.append({"finding_id": candidates[0]["id"], "assertion": issue, **outcome})
        else:
            matched.append({"finding_id": None, "assertion": issue, **outcome})
    for issue, route in (("SEC-07", "/rest/memories"), ("SEC-08", "/rest/memories"),
                         ("SEC-11", "/rest/memories"), ("RET-02", "/dataerasure"),
                         ("cookie-flags", "/rest/user/login")):
        if not any(item["assertion"] == issue for item in matched):
            matched.append({"finding_id": None, "assertion": issue,
                            **_result("inconclusive", route, "Setup or sufficient Evidence was unavailable", "No outcome established")})
    transport_result, transport_reason = transport(target) if responded else ("inconclusive", "Target did not respond")
    matched.append({"finding_id": None, "assertion": "transport",
                    **_result(transport_result, "/rest/memories", transport_reason, "Transport assessed for this instance only")})
    for assertion in ("consent-after-withdrawal", "comparable-ease"):
        matched.append({"finding_id": None, "assertion": assertion,
                        **_result("inconclusive", "/", "No supported Purpose-specific grant and Withdrawal Path was exercised", "Not exercised")})
    return matched


def probe_report(path, target: str, allowed_origins: tuple[str, ...] = ()) -> list[dict]:
    from auditor.report import write_reports
    report = json.loads(path.read_text(encoding="utf-8"))
    results = run(report, target, allowed_origins)
    write_reports(report, path)
    return results
