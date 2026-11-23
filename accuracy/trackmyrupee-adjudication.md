# TrackMyRupee reference: independent adjudication

- Pin: `47990e4f19d7debea70c5d56bab77e3c3f051546` (verified with `git -C targets/trackmyrupee rev-parse HEAD`).
- Scope: every entry of `accuracy/trackmyrupee.json` and every Issue Type the method note lists as absent. Each anchor was opened at the pin, evidence lines were compared with the source by script (every evidence line matches its source line; four long lines are truncated at 200 characters), every cited Provision was resolved against `auditor/registry/*.yaml` (all exist), and the Issue Type was checked against `docs/issue-types.md` (including the Tier A/B gate of SEC-02 as defined by the Risk Matrix in `docs/adr/0002-severity-model.md`).
- Isolation: only the Target source at the pin, `docs/issue-types.md`, `docs/adr/0002-severity-model.md`, `auditor/registry/*.yaml`, `CONTEXT.md`, `accuracy/README.md` and the two files under review were read. No Auditor output, Rules, corpus, reports, Target docs, Target-named tests, `dpdp-audit` or Semgrep.
- Counts: 46 entries reviewed; 42 upheld, 2 corrected, 2 rejected; 1 entry added for a disagreed absence. The file now holds 45 entries (39 confirmed, 6 not-determinable). The retired id REF-015 is not reused; the new entry is REF-048.

## Entries

| id | verdict | justification |
|---|---|---|
| REF-001 | upheld | `Expense.amount` and `description` are plain Decimal/Text fields linked to `user` (models.py:835-836), Financial Data is Tier A, and the repo contains no field-level encryption. |
| REF-002 | upheld | `Account.balance` is a plain DecimalField tied to the user (models.py:189); Financial Data, no field-level protection. |
| REF-003 | upheld | `Income.amount`, `description` and `source` are plain fields on a user-owned row (models.py:1275-1277). |
| REF-004 | upheld | `capitalUrl()` puts amount, date, note, account and category into a query string (expense_composer.js:159-163) that is then used as the link target. |
| REF-005 | upheld | `onSaved`/`finish` write the amount and category summary into sessionStorage (expense_composer.js:785-800); the expiry timestamp does not remove the storage. |
| REF-006 | upheld | The transactions consent checkbox is rendered `checked required` (signup.html:143) and the JS does not clear it, so the grant is default-true. |
| REF-007 | upheld | The device and browser consent checkbox is rendered `checked required` (signup.html:156). |
| REF-008 | upheld | The standalone consent page renders `consent_transactions` as `checked` (dpdp_consent.html:53); the POST handler records the grant (misc.py:438-455). |
| REF-009 | upheld | The standalone consent page renders `consent_device` as `checked` (dpdp_consent.html:66). |
| REF-010 | upheld | Email consent is a hidden `value="on"` input with a "Required" badge (signup.html:130), a default-true consent value the Data Principal cannot change; judgement call, but it fits "default-true consent". |
| REF-011 | upheld | Same hidden default-on `consent_email` input on the consent page (dpdp_consent.html:40). |
| REF-012 | corrected | The finding stands (PaymentHistory keeps email and username after erasure, settings.py:148, models.py:2252, contradicting the notice), but the rationale repeated one sentence twice; the duplicate was removed and nothing else changed. |
| REF-013 | upheld | `WithdrawConsentView` only dispatches local deletion plus Razorpay cancellation (settings.py:105-123, 257); Brevo receives the email address and PostHog a pseudonymous id, and the notice (privacy_policy.html:390) admits providers are not told. |
| REF-014 | upheld | The in-repo notice lists five DPDP rights (privacy_policy.html:335) and no nomination right appears anywhere in the notice, terms or security page, which meets the RIG-04 gate. |
| REF-016 | upheld | `Loan.name` and `initial_principal` are plain columns on a user-owned row (models.py:2675-2686); Financial Data. |
| REF-017 | upheld | `PhysicalAsset.policy_number`, `premium_amount` and `sum_assured` are plain columns (models.py:3505-3532); Financial Data. |
| REF-018 | upheld | `Holding.instrument_name`, `units` and `avg_cost` are plain columns tied to the user's account (models.py:3294-3306); Financial Data. |
| REF-019 | upheld | `SavingsGoal.name`, `target_amount` and `current_amount` are plain columns on a user-owned row (models.py:2392-2394). |
| REF-020 | upheld | `EmailLog` stores recipient, subject, text body and HTML body in plain fields (models.py:2650-2653) written at email_backends.py:69-79; the bodies carry monthly financial reports, so Tier A content is present. |
| REF-021 | rejected | The two TextFields hold free-text notes about where documents are and who to contact; the form rejects any digit run that looks like an account or card number (emergency.py:39, 62-67), so the fields hold neither Financial values nor Tier A/B Elements and the SEC-02 gate is not met. |
| REF-022 | upheld | `buildQueryString` writes search text, dates and filters into the URL via `history.replaceState` (tmr_filter.js:1488-1516); the analytics snippet itself acknowledges the addresses carry search text (analytics.html:26). Search text is treated as Financial Data, as the method note states. |
| REF-023 | upheld | The refund picker sends the typed transaction search as `?q=` on a GET (refund_picker.js:163), handled at expenses.py:359. |
| REF-024 | upheld | The manifest share target uses `"method": "GET"` with title/text/url (manifest.json:40-48), and `_prefill_text` reads `text` from `request.GET` (expenses.py:117-123), so shared message text sits in the URL. |
| REF-025 | upheld | `saveStateToStorage` writes search, dates and filters as JSON into sessionStorage (tmr_filter.js:150-159). |
| REF-026 | upheld | `capacitor.config.json` sets `"cleartext": true` for the remote app origin (lines 6-7); the server-side HTTPS redirect limits but does not remove the client allowance. |
| REF-027 | upheld | Gate is not clearly met: no `access_log`, `accesslog` or request logger exists in the repo, but nginx logs by default when the directive is absent and the production proxy config is not in the repo, so not-determinable is correct. |
| REF-028 | upheld | The repo contradicts itself (privacy_policy.html:363 and the deletion email say no backups; llms.txt:15 says automated backups) and the database is external (`DATABASE_URL`), so the gate cannot be settled from code. |
| REF-029 | upheld | The Dockerfile has no `USER` directive (lines 1-34) and compose mounts the project and `.env` into that root container; the container processes Financial Data. |
| REF-030 | upheld | Monitoring configuration exists (Sentry, settings.py:29-40) and covers errors and sampled traces only; `ACCOUNT_RATE_LIMITS` throttles but does not alert, which meets the MON-01 condition. |
| REF-031 | rejected | The welcome email is sent in direct response to the user's own signup to the address they supplied, which is a section 7 voluntary-provision use (the CON-01 gate excludes it), and for form signups the consent fields were validated in the same request before the user row was saved. |
| REF-032 | upheld | The recipient query filters only on `is_active`, tier, a non-empty and verified email (send_lifecycle_emails.py:35-52); `consent_granted` is never read and no drip opt-out exists; the upgrade and tips mail goes beyond the stated email Purpose (judgement call). |
| REF-033 | upheld | `users = User.objects.filter(is_active=True).exclude(email="")` (send_product_update.py:78) applies no consent or preference filter. |
| REF-034 | upheld | `users_qs` selects every active user and only the tier narrows the audience (send_announcements.py:46-53); consent and preference are never read. |
| REF-035 | upheld | Three consent BooleanFields are all `required=True` for three Purposes (forms.py:884-898) and `signup()` records a single grant, so none can be declined separately. |
| REF-036 | upheld | The consent view accepts only when email, transactions and device are all on, otherwise errors "agree to all data collection terms" (misc.py:438-465). |
| REF-037 | upheld | A withdrawal path exists but it is deleting the whole account (settings.py:246-263; notice at privacy_policy.html:335); whether that is harder than the grant is a legal reading, so not-determinable is correct. |
| REF-038 | upheld | `HouseholdInvitation.email` stays after accept, cancel or expiry (models.py:775; `cancel_invitation` only sets a timestamp, households.py:118-122) and no job purges concluded invitations. |
| REF-039 | upheld | `EmailLog` rows are created for every send (email_backends.py:69) and deleted only through the account holder's own erasure (settings.py:92-102); no retention purge exists for other recipients or contact messages. |
| REF-040 | upheld | `_delete_ledger` removes only JournalLine, JournalEntry and LedgerAccount (settings.py:83-89); `LedgerPostingFailure` has no user foreign key (models.py:531-547) and its payload keeps user id, amount and description (models.py:950-962). |
| REF-041 | upheld | `DeletionRequestAuditLog` (email, username) is created on every erasure and kept indefinitely per the notice (settings.py:55, privacy_policy.html:368-371); whether a proof-of-deletion record is a permitted retention is a legal judgement. |
| REF-042 | upheld | The Data Summary modal lists username, email, join date, plan and two counts (settings_home.html:436-477); loans, goals, holdings, insurance, family shares, emergency sheet and consent records are omitted, and the export list (export.py EXPORTS) also lacks holdings, assets and consent events. |
| REF-043 | upheld | `ReCaptchaField(widget=ReCaptchaV3)` is added on the contact form (forms.py:944, contact.html:73) and no captcha or Google service for it appears in the notice's provider table. |
| REF-044 | corrected | The finding stands, but evidence line 115 (`client.capture`, the actual transfer) lay outside the anchor 85-88; `end_line` was extended to 115 so the anchor covers both the US host setting and the send. |
| REF-045 | upheld | Mail is delivered through the Brevo backend (email_backends.py:38-39, settings.py:458-461) and the notice states "Region: United States" (privacy_policy.html:227); a disclosure per the catalogue. |
| REF-046 | upheld | `sentry_sdk.init` sends error and trace data (settings.py:29-40) containing page URLs and error text; the notice states "Region: United States" (privacy_policy.html:242). Local variables and default PII are off, so Personal Data is limited to URLs and messages; disclosure only. |
| REF-047 | upheld | Google Analytics loads on consent and receives IP, device and page data (analytics.html:17; privacy_policy.html:138), but no region is stated anywhere, so not-determinable is correct. |
| REF-048 | added (new) | New entry for the disagreed SEC-01 absence; see the row below. |

## Issue Types with no entries

| Issue Type | verdict | justification |
|---|---|---|
| SEC-01 | disagree | The method note says logger calls carry only ids and exception types, but `expenses/views/mixins.py:254` logs `rt.amount` (a recurring loan repayment amount) with the loan and schedule ids at ERROR level, which the default `expenses` logger (WARNING) emits; entry REF-048 added. A lesser site, `signals.py:160` (account name inside a warning), was not labelled because an account label is not clearly Personal Data. `ledger_read_compare` puts balances in `extra`, but the configured formatter does not print extras and the flag defaults to off. |
| SEC-03 | agree | No Aadhaar, PAN, passport, voter or ABHA field exists; the only Aadhaar mention is a digit-run guard in `expenses/family/emergency.py:39`. |
| SEC-04 | agree | No custom hasher in production; `MD5PasswordHasher` is set only under `IS_TESTING` (settings.py:78-79). |
| SEC-05 | agree | `SECRET_KEY` and the Razorpay, Brevo and reCAPTCHA keys come from the environment, no `.env`, key or keystore file is tracked, and a pattern search for provider key formats found only a test placeholder. |
| SEC-06 | agree | `DEBUG` defaults to False (settings.py:61); no verbose error output is configured. |
| SEC-07 | agree | List and detail views scope to `request.user`; ModelChoiceFields default to `none()` and are set per user; function views check `is_authenticated`; cron and webhook routes use a constant-time secret or signature (notifications.py:49-67). |
| SEC-08 | agree | No `model_to_dict`, serializer or `__all__` form was found; JSON responses are built field by field (for example `capital_event_loans_ajax` returns id, name, type). |
| SEC-13 | agree | Compose has size-based log rotation (docker-compose.yml:29-33) that states no time period, and the application logs carry little Personal Data, so the gate "a log retention setting exists" is not established. |
| SEC-15 | agree | No dumps, logs, statement files, ID images or real fixtures are tracked; seed data is demo (`demo_seed_extras.py`); the founder photo is published on purpose. |
| CON-06 | agree | `ConsentEvent` stores action, purpose, version and timestamp (models.py:3608-3615) and is written at both grant sites (forms.py:911, misc.py:448). |
| CON-07 | agree | The notice itemises what is collected and why (privacy_policy.html:41-82) and the app offers English, Hindi and Marathi. |
| CON-08 | agree | Collected elements match the Purposes the notice and consent page state; no unrelated element was found. |
| RET-03 | agree | Needs a Third Schedule class, which the code does not establish. |
| RIG-02 | agree | `ProfileUpdateForm` edits email, first and last name, salary date and reminder (forms.py:780-803), and account and transaction records are editable. |
| RIG-03 | agree | A Grievance Officer, an email contact and a 30-day response time are in the notice (privacy_policy.html:416-430). |
| CHI-01 | agree | No age or date of birth is collected; the 18+ tick is validated and not stored (forms.py:877-881), and the app does not target children. |
| CHI-02 | agree | Depends on the CHI-01 gate, which is not met. |
| TRF-01 (other than reCAPTCHA) | agree | The other outbound flows (Brevo, Razorpay, PostHog, Sentry, Google, CDNs, push services) are in the notice table; frankfurter, exchangerate-api, mfapi.in and AMFI receive currency codes and fund names, not Personal Data. |

Adjudication complete: yes
