# Juice Shop mismatch adjudication

> **Historical record.** This adjudication covers the run published at commit `7fb1236` (16 TP / 6 FP / 31 FN). The recall Rules added afterwards were built from the gaps listed here, so most of these misses are now matched; the current figures and remaining misses (REF-021, REF-044) are in `accuracy/README.md` and `accuracy/results.md`.

Reviewed against the pinned target and `docs/issue-types.md`. IDs below are the original unmatched predictions and references in `/tmp/acc/report.json`; a C can describe both sides of one disagreement. C does not by itself justify changing a valid reference anchor.

| id | verdict | reason (target code) |
|---|---|---|
| MON-01-8c5728dfea11 | C | Same missing access-log review as REF-044: `monitoring/grafana-dashboard.json:114` queries challenge progress, whereas `server.ts:370` writes the access log. The reference identifies the affected log operation; leave its anchor intact. |
| RET-03-41bffe4101f9 | B | `routes/dataErasure.ts:83-86` records an individual request, not scheduled inactivity erasure; it neither performs erasure nor establishes the Third Schedule class. RET-03's conditional gate cannot be inferred from this request. RET-02 covers the unfulfilled request. |
| SEC-02-0a13729d5971 | B | `models/securityAnswer.ts:33-35` is `SecurityQuestionId`, a question identifier, not the security answer or an Authentication Secret. SEC-02 requires Tier A/B Personal Data. |
| SEC-02-0f4631e6a05d | B | `routes/deluxe.ts:43` stores `security.deluxeToken(user.email)`; `lib/insecurity.ts:149-151` derives it by HMAC and `:165-167` checks membership after JWT verification. It relates to an identifiable individual, but the evidence does not establish an unprotected Tier A/B Authentication Secret: it is a derived membership entitlement, not the session token proving identity. |
| SEC-02-e0994a7481e3 | B | `models/securityAnswer.ts:44-45` stores `security.hmac(answer)`, not an unprotected answer. The constant-key, fast verifier is a weak-hashing problem (SEC-04, REF-005), not a second cleartext-storage label. |
| SEC-08-177006878772 | C | `routes/authenticatedUsers.ts:12` fetches all users; `:24-27` spreads their fields into the response while masking two. This is REF-021's SEC-08 issue at the query rather than its valid response anchor. REF-011 separately concerns missing ownership checks (SEC-07), not a second SEC-08 match. |
| REF-005 | A | SEC-04 should detect `models/securityAnswer.ts:45` using `security.hmac(answer)` with the constant-key HMAC at `lib/insecurity.ts:42`: fast deterministic hashing makes answers guessable. |
| REF-006 | A | SEC-04 should catch `routes/login.ts:34`, where the password comparison calls the unsalted MD5 `security.hash` (`lib/insecurity.ts:41`). |
| REF-008 | A | SEC-05 should catch the hard-coded HMAC key in `lib/insecurity.ts:42`, used to protect security answers (`models/securityAnswer.ts:45`). |
| REF-010 | A | SEC-07 should detect `server.ts:395-397`: list and individual User reads have `isAuthorized()` but no ownership check. |
| REF-011 | A | SEC-07 should detect `routes/authenticatedUsers.ts:12` `UserModel.findAll()` without ownership filtering; `server.ts:430` supplies only session authorization. |
| REF-012 | A | SEC-07 should detect `server.ts:413` authorizing complaint-list access without an ownership filter; complaints contain a UserId and message. |
| REF-013 | A | SEC-07 should detect `routes/recycles.ts:12-17` returning records selected only by requested id; `server.ts:420` exposes the route without authentication. |
| REF-015 | A | SEC-07 should catch `routes/orderHistory.ts:15-17`: vowel masking makes distinct emails share the order lookup key, defeating ownership isolation. |
| REF-016 | A | SEC-07 should catch the same cross-account key collision in `routes/dataExport.ts:22,33`: masked email selects exported orders. |
| REF-017 | A | SEC-07 should catch `routes/order.ts:45,65`: an invoice containing customer email is written to publicly served `ftp/` (`server.ts:294-295`). |
| REF-018 | A | SEC-07 should catch `server.ts:294-295` public ftp listing and download, which expose invoices written by `routes/order.ts:45,65`. The reference already includes the actual route; no anchor correction. |
| REF-019 | A | SEC-07 should catch `server.ts:306,308`, unauthenticated listing and serving of access logs containing Personal Data. The reference includes the routes despite its comment start. |
| REF-021 | C | Same SEC-08 exposure as SEC-08-177006878772: `routes/authenticatedUsers.ts:25` spreads the row; its valid response anchor does not overlap the Finding's query at `:12`. Do not widen it. |
| REF-022 | A | SEC-08 should catch `routes/memory.ts:24-25`: `include: [UserModel]` returns nested user rows without an attribute filter. |
| REF-023 | A | SEC-08 should catch `server.ts:523`: the User resource excludes only password and TOTP secret rather than allow-listing response fields. |
| REF-024 | A | SEC-08 should catch `routes/currentUser.ts:29-31`, which copies requester-selected user fields into the response without an allow-list. |
| REF-025 | A | SEC-08 should catch `routes/login.ts:23-24`, where the whole user object enters the session JWT payload. |
| REF-026 | A | SEC-08 should catch `routes/saveLoginIp.ts:32-33`, returning the full updated user model rather than a limited response. |
| REF-028 | A | SEC-09 should catch `routes/changePassword.ts:14-17`, where current and replacement passwords come from query parameters. |
| REF-029 | A | SEC-09 should catch `routes/securityQuestion.ts:12-13`, which takes the account email from `query.email`. |
| REF-032 | A | SEC-10 should catch `frontend/src/app/oauth/oauth.component.ts:52`, `localStorage.setItem('token', authentication.token)`. |
| REF-033 | A | SEC-10 should catch `frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:54`, storing the session token in localStorage. |
| REF-034 | A | SEC-10 should catch `frontend/src/app/payment/payment.component.ts:233`, storing the renewed token in localStorage. |
| REF-036 | A | SEC-11 should catch `lib/insecurity.ts:192`, `res.cookie('token', token)` without Secure, HttpOnly or SameSite options. |
| REF-037 | A | SEC-11 should catch `routes/currentUser.ts:54-58`, which serves the Personal Data response as JSONP when a callback is supplied. |
| REF-038 | A | SEC-11 should catch `terraform/networking.tf:157-164`, an HTTP port 80 listener forwarding rather than redirecting traffic. |
| REF-039 | A | SEC-11 should also catch the separate deployment tree's `infrastructure/terraform/networking.tf:157-164`, which likewise forwards HTTP. |
| REF-042 | A | SEC-14 should examine `infrastructure/terraform/main.tf:82-87`, the persistent EFS volume, with the deployment's lack of backup configuration. |
| REF-044 | C | Same MON-01 gap as MON-01-8c5728dfea11: `server.ts:362-370` identifies access logging needing review, while `monitoring/grafana-dashboard.json:114` shows challenge-only monitoring. The access-log anchor is meaningful and remains unchanged. |
| REF-045 | A | RET-01 should examine `models/user.ts:119-120` (`paranoid: true`) with the account erasure event at `routes/dataErasure.ts:83-85`; retained rows are not erased. The original range includes the operative setting. |
| REF-052 | A | TRF-02 should catch the separate deployment tree's `infrastructure/terraform/variables.tf:1-4` default `eu-west-1`; this is a conditional location disclosure, not proof of a prohibited transfer. |

## Label changes

None. The reference ranges already include the operative code; neither anchor disagreement warrants widening an otherwise valid range. No independent code-and-catalogue basis was established for adding or changing a label. In particular, the membership token is Personal Data in context but its Tier A/B status and lack of field-level protection are not established; a user-initiated erasure request does not establish RET-03's Third Schedule/inactivity conditions.

## Recall gaps

- **SEC-04:** REF-005, REF-006 — weak verifier and password hashing.
- **SEC-05:** REF-008 — committed key protecting an answer verifier.
- **SEC-07:** REF-010, REF-011, REF-012, REF-013, REF-015, REF-016, REF-017, REF-018, REF-019 — missing authentication or ownership enforcement.
- **SEC-08:** REF-022, REF-023, REF-024, REF-025, REF-026 — over-exposed model or response fields.
- **SEC-09:** REF-028, REF-029 — Personal Data or Authentication Secrets in queries.
- **SEC-10:** REF-032, REF-033, REF-034 — session tokens in browser storage.
- **SEC-11:** REF-036, REF-037, REF-038, REF-039 — cookie, cross-origin response and transport safeguards.
- **SEC-14:** REF-042 — backup gap in the second deployment tree.
- **RET-01:** REF-045 — retained user rows after the end-of-purpose event.
- **TRF-02:** REF-052 — foreign-region default in the second deployment tree.
