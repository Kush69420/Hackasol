# Live Probes

Run only against an authorized, dedicated instance containing synthetic records. The Juice Shop suite creates two random accounts and one memory and submits the first account's ordinary erasure request. These records can persist: dispose of the instance after the run. Never point it at a production instance.

## Pinned Juice Shop instance

With the Reference Target clone at `c9f99228d9d56afb5f5ca7925376292f7fa44b13`:

```sh
docker build -t dpdp/juice-shop:c9f99228 --build-arg VCS_REF=c9f99228d9d56afb5f5ca7925376292f7fa44b13 targets/juice-shop
docker image inspect --format '{{.Id}} {{index .Config.Labels "org.opencontainers.image.revision"}}' dpdp/juice-shop:c9f99228
docker run -d --rm --name dpdp-juice -p 127.0.0.1:3000:3000 dpdp/juice-shop:c9f99228
JUICE_SHOP_IMAGE=dpdp/juice-shop:c9f99228 dpdp-audit probe --target http://127.0.0.1:3000 --report reports/juice-shop/report.json
docker stop dpdp-juice
```

When `JUICE_SHOP_IMAGE` is set the Auditor inspects its image ID and revision label, rejects absent or mismatched metadata before sending requests, and records the image ID and revision with each matched outcome. The operator must ensure the instance is actually running that image; an image label alone cannot establish this. This is a local build, not a claim about an official published image digest. The dashboard requires a completed live Report and explicit authorization; Replay Mode cannot be modified by a Live Probe.

The dashboard Playwright suite starts its own disposable loopback fixture at an ephemeral port; it does not require Docker or port 3000. The pinned-container steps above remain a separate manual smoke against the actual Target Application.

## Boundaries and interpretation

Only HTTP(S) loopback origins are allowed by default. CLI `--allow-origin` adds an exact scheme, host and port; it does not authorize mutation of existing accounts. HTTP redirects are never followed, environment proxies are disabled, methods and routes are fixed, and Juice Shop requests are capped at 16. Account-bound writes require an account created in the same run and its associated session. Raw response bodies, cookies, Authentication Secrets and synthetic values are not retained; Evidence records only method, route, status and fixed behavioural descriptions.

The Juice Shop suite observes wildcard CORS on `GET /rest/memories`, anonymous and cross-account access to an Auditor-created memory, the presence of the created account's nested email, and whether that same account can still authenticate after its ordinary `POST /dataerasure` workflow. It also evaluates the flags of any session cookie issued by login. Successful authentication after the request establishes continued retention; cookie clearing by itself does not establish erasure. Failed setup and unsupported behaviour are inconclusive, not Confirmed. A non-wildcard CORS response Refutes only that specific wildcard assertion, not every transport or cookie concern. Loopback HTTP does not establish production transport posture.

The account setup uses the finale-generated `POST /api/Users` identity at `server.ts:520-545`; the memory route is mounted at `server.ts:670` and serialises a nested account at `routes/memory.ts:22-25`. The static scan emits a separate SEC-08 Finding (`SEC-08-cefb92be21c6`, `SEC-08-ts-whole-model-serialisation`) at the memory route, which the suite matches by Evidence; it adds no Finding to the recorded Report. If the static scan emitted none, the suite would pass the existing source Evidence through normal Finding assembly for SEC-08, rather than associating the observation with the unrelated account-list or review Finding. Erasure is mounted at `server.ts:695-696`; its request handler is `routes/dataErasure.ts:74-88`.

Observed run against the pinned image `dpdp/juice-shop:c9f99228` (disposable local container, removed afterwards) on the 52-Finding Report: SEC-07 (`SEC-07-2d4f025671b7`), SEC-08 (`SEC-08-cefb92be21c6`), SEC-11 (`SEC-11-ad5b2106f4e8`) and RET-02 (`RET-02-4696497b9137`) Confirmed; the session-cookie flags check, transport and the two consent assertions inconclusive. The other 48 Findings carry no Live Probe outcome.

Run details list unmatched and inconclusive observations separately; they do not change a static Finding. Cookie and transport observations are not attached to the CORS Finding merely because they share an Issue Type. The suite does not infer erasure merely from failed authentication, and does not provide a Refuted erasure result without an independent account-data assertion. Juice Shop has no supported Purpose-specific Withdrawal Path, so consent and comparable ease are not exercised there.

The separately registered TrackMyRupee adapter is limited to revision `47990e4f19d7debea70c5d56bab77e3c3f051546`. It uses a fresh Playwright browser, creates its own account through the pinned signup form, and checks that account's profile immediately before sending the withdrawal POST. It compares profile access before and after withdrawal. The browser allows at most 160 action requests and 320 static asset reads on separate budgets, so styles, scripts and fonts cannot exhaust the action budget. Off-origin requests and unsupported methods and routes are blocked. No browser trace or raw traffic is retained. The browser counts clicks and checkbox changes, excluding text entry; comparable ease remains Inconclusive even when both counts are known if they do not establish a common starting point or Purpose link.

### TrackMyRupee Purpose-specific consent enforcement

After the browser Withdrawal Path, the adapter runs HTTP Live Probes through the pinned signup, login, cookie-choice, consent, profile and withdrawal routes (no redirects followed, at most 40 requests per session). When the Target Application requires email verification, set `DPDP_TMR_MAIL_DIR` to the dedicated loopback instance's file mailbox. Both probes accept only a matching verification link for their own synthetic email and the same loopback origin. They reauthenticate after verification and complete the required consent form if the profile redirects there. The HTTP probe checks that the authenticated profile's `auth_email` field exactly matches its synthetic account immediately before it submits the withdrawal form. A cookie alone is not sufficient: if the profile cannot establish ownership, the outcome is Inconclusive and no withdrawal POST is sent.

| Assertion | Exercise | Confirmed when | Refuted when |
|---|---|---|---|
| `consent-declined:<purpose>` | Signup omitting one mandatory consent, beside a control signup supplying all | An account is created although the consent was declined | The form is rejected and the control succeeded |
| `analytics-declined` | Signup and login carrying `tmr_consent=declined`, compared with a granted login | PostHog events for the verified account are observed in the decline windows | No scoped event is observed while the granted control produced an event |
| `analytics-withdrawn` | Record acceptance, then record decline and log in with the declined cookie | PostHog events for the verified account are observed in the withdrawn login window | No scoped event is observed while the granted control produced an event |
| `withdrawal-data-removal` | The verified account's Withdrawal Path, then re-login and a read-only SQLite row count | The account still authenticates or linked rows remain | It does not authenticate and no linked rows remain |

`DPDP_TMR_SINK_URL` points to a loopback PostHog receiver that supports scoped observation. Configure the dedicated Target's PostHog host to use this receiver. The Auditor reads the PostHog identifier only from the verified synthetic profile; it never includes that identifier in the Report. The receiver must implement `GET /` with `X-DPDP-Distinct-Id`, `X-DPDP-Since` and `X-DPDP-Until` headers. Return a JSON object echoing those exact strings as `distinct_id`, `since`, `until`, plus a non-negative integer `count`. Count only PostHog events for the supplied identifier with producer timestamps in the half-open UTC interval `[since, until)`. The Target and Auditor clocks must agree. Use only the event identifier and producer timestamp for counting, not receipt time or other properties; delayed delivery of an earlier event must not inflate a later count.

An unscoped counter, malformed response, failed comparable login, unverified account, or unsuccessful cookie choice makes the dependent analytics outcome Inconclusive. With a valid scoped observation the Auditor waits `DPDP_TMR_SETTLE` seconds (default 3) for asynchronous delivery. Silence without a non-zero granted control is Inconclusive and a Refuted outcome describes only this bounded observation, not all analytics channels. `DPDP_TMR_DB` is the Target's SQLite file, opened `mode=ro` for account-linked row counts; without it, failed authentication alone does not establish data removal.

Evidence contains fixed descriptions and counts, not synthetic account values or raw payloads. Outcomes are unmatched run details (`finding_id: null`) and create no Finding. Each names the Consent Assessment criterion it bears on, and the run stores them as dynamic Evidence there:

| Probe assertion | Consent Assessment criterion |
|---|---|
| `consent-declined:<purpose>`, `analytics-declined`, `analytics-withdrawn`, `withdrawal-data-removal`, `consent-after-withdrawal` | enforced server-side |
| `comparable-ease` | withdrawable with comparable ease |

On a TrackMyRupee Report with a Consent Assessment, `auditor.consent.criteria.attach_live_probes` adds an optional `live_probes` list to the matching criterion row, and an optional `live_probe_run` (`target`, `commit`, `observed_at`) to the assessment. Each entry carries `status` (Confirmed: violation observed; Not Confirmed: enforcement observed; Inconclusive: not run, no effect), the assertion, route, reason and masked request/response. The static `applicability`, `assessment`, linked identifiers and Evidence are never rewritten and static figures stay the headline; the Report prints the Live Probe beside them, labelled as such with the target commit and run time. A Confirmed result is a violation observed in that run, not a Finding. A rerun replaces the earlier entries; a Report with no probe run (or a run with no attachable outcome) is unchanged. Juice Shop outcomes carry no criterion and are not attached.

The recorded A4000 run used a fresh SQLite database and a clean copy of the pinned revision outside `targets/`. The disposable Django instance ran in debug mode on loopback HTTP with a throwaway signing key. It raised the signup limit from 3/h per IP (`finance_tracker/settings.py:419–425`) to 100/h so one run could create its accounts; rate limiting was not under test. It required email verification with a file mailbox so the Auditor could verify its own accounts without sending mail. It used PostHog SDK 3.25.0, which satisfies the pin's `posthog>=3.5.0` requirement; 8.1.0 changed the capture signature and removed module-level identify. A synthetic PostHog key and a run-scoped loopback sink kept analytics local and limited the counts to this run.

Seven assertions were Not Confirmed: each declined-consent signup was rejected; neither analytics decline window produced an outbound event while the granted control produced two; after the HTTP withdrawal the account no longer authenticated and no account-linked rows remained in the measured tables; and `consent-after-withdrawal` was Not Confirmed: The Processing Operation was unavailable after withdrawal. `comparable-ease` was Inconclusive: Grant recorded 3 interactions and withdrawal 2; the Report does not establish a common starting point or Purpose link. These single-run observations do not establish deletion at Data Processors. Recorded-behaviour tests live in `tests/test_live_probes.py`, with loopback fixtures in `tests/fixtures/probes/`.
