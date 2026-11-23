# Live Probes

Run only against an authorized, dedicated instance containing synthetic records. The Juice Shop suite creates two random accounts and one memory and submits the first account's ordinary erasure request. These records can persist: dispose of the instance after the run. Never point it at a production instance.

## Pinned Juice Shop instance

With the Primary Target clone at `c9f99228d9d56afb5f5ca7925376292f7fa44b13`:

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

The account setup uses the finale-generated `POST /api/Users` identity at `server.ts:520-545`; the memory route is mounted at `server.ts:670` and serialises a nested account at `routes/memory.ts:22-25`. The static scan currently merges the SEC-08 nested-record Rule into the SEC-07 Finding at this anchor rather than emitting a separate SEC-08 Finding. On observed nested Personal Data the suite passes the existing source Evidence through normal Finding assembly for SEC-08, rather than associating the observation with the unrelated account-list or review Finding. Erasure is mounted at `server.ts:695-696`; its request handler is `routes/dataErasure.ts:74-88`.

Run details list unmatched and inconclusive observations separately; they do not change a static Finding. Cookie and transport observations are not attached to the CORS Finding merely because they share an Issue Type. The suite does not infer erasure merely from failed authentication, and does not provide a Refuted erasure result without an independent account-data assertion. Juice Shop has no supported Purpose-specific Withdrawal Path, so consent and comparable ease are not exercised there.

The separately registered TrackMyRupee adapter is limited to revision `47990e4f19d7debea70c5d56bab77e3c3f051546`. It uses a fresh Playwright browser and creates its own account through the pinned signup form, confirms that account's profile before withdrawing, and compares profile access after withdrawal. Browser requests are bounded to 160, off-origin requests and unsupported methods/routes are blocked, and no browser trace or raw traffic is retained. Its observations remain unmatched run details, not new Findings. It counts clicks and checkbox changes, excluding text entry; the Report does not establish a common starting point or Purpose link for the measured grant and withdrawal paths, so comparable ease remains inconclusive even when both counts are available. Browser setup failures and unavailable paths are inconclusive.
