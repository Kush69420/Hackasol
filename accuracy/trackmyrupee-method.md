# TrackMyRupee held-out reference: method note

- Labelled by: single reviewer (Claude subagent), 2026-11-24, completing the earlier partial draft by `LabelTrackMyRupee`.
- Pin: `47990e4f19d7debea70c5d56bab77e3c3f051546`, verified with `git -C targets/trackmyrupee rev-parse HEAD`.
- Isolation: only the Target source at the pin, `docs/issue-types.md`, `auditor/registry/*.yaml`, `CONTEXT.md`, the Review procedure and Anchor policy of `accuracy/README.md`, and the field structure of `accuracy/juice-shop.json` were used. No Auditor output, Rules, corpus, reports, Target docs, Target-named tests, `dpdp-audit` or Semgrep. No Live Probes, builds or tests.
- Entry fields: the juice-shop fields plus `personal_data`, `provisions` (registry ids) and `evidence` (`file:line: text` copied from the source by script). Anchors are 1-based lines at the pin. No Personal Data values or secrets are reproduced.
- Excluded by contract: `static/vendor/**`, `staticfiles/**`, migrations, minified JS, lockfiles.
- Changes from the earlier draft: REF-013 (CON-05) and the PostHog TRF-02 entry (old REF-015, now REF-044) changed from not-determinable to confirmed because the privacy notice in the repository itself states that deletion does not reach processors and names the United States region; anchors of REF-004, REF-005 and REF-014 corrected; REF-015 id retired.

## Files reviewed

Read in full or in the relevant region: `finance_tracker/settings.py`, `finance_tracker/urls.py`, `finance_tracker/csrf.py`, `finance_tracker/context_processors.py`, `expenses/middleware.py`, `expenses/email_backends.py`, `expenses/posthog_utils.py`, `expenses/signals.py`, `expenses/adapters.py` (send path), `expenses/forms.py` (consent and contact), `expenses/views/settings.py`, `expenses/views/misc.py`, `expenses/views/export.py`, `expenses/views/notifications.py`, `expenses/views/expenses.py` (search and share), `expenses/family/households.py` and `emergency.py` (invitation, deletion, guard), `expenses/insights/views.py` (cron, unsubscribe), `expenses/management/commands/send_*.py`, `reset_ledger.py`, `retry_ledger_shadow_failures.py`, `expenses/models.py` (every model class and its relation `on_delete`), `static/js/tmr_filter.js`, `expense_composer.js`, `refund_picker.js`, `templates/components/analytics.html`, `cookie_consent.html`, `templates/account/signup.html`, `templates/expenses/dpdp_consent.html`, `settings_home.html`, `templates/privacy_policy.html`, `templates/contact.html`, `templates/manifest.json`, `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `gunicorn.conf.py`, `nginx.conf`, `mobile/capacitor.config.json`, `mobile/android/app/src/main/AndroidManifest.xml`, `mobile/package.json`, `.github/workflows` (secret scan).

Covered by tree-wide searches rather than line-by-line reading: every other tracked `.py`, `.js`, `.html`, `.yml`, `.json`, `.gradle`, `.xml`, `.sh`, `.css` and `.md` outside the exclusions (including `expenses/views/*`, `expenses/importing/*`, `expenses/insights/*`, `expenses/flows/*`, `expenses/analytics/*`, `expenses/tests/*`, `e2e/*`, `blog/*`, `guide-src/*`, `docs/*`, `locale/*.po`, `scripts/*`, `mobile/ios/*`). Searches: logging calls, outbound HTTP hosts, secrets and key patterns, tracked `.env`/dump/log/key files, cookies and browser storage, CORS and `csrf_exempt`, every `get_queryset` and `get_object_or_404` in views (all filter by owner), `on_delete` options, Government Identifier and biometric terms, backup and retention terms, consent and recaptcha usage, query-string builders in JS. Binary images were sampled (`misc/upload.png`, `misc/dashboard1.png`): marketing and demo screens, no real Personal Data.

## Issue Types with no entries

- SEC-01: logger calls log user ids, rule ids and exception types, not Personal Data values (grep of all `logger.*` calls; `expenses/adapters.py:46`, `expenses/signals.py:124`). `finance_tracker/csrf.py:36` logs a truncated user agent only.
- SEC-03, CHI-01, CHI-02: no Aadhaar, PAN, passport, DOB or child fields exist (tree-wide search; `expenses/family/emergency.py:39` even blocks long digit runs). The only age control is an unstored 18+ tick (`expenses/forms.py:878`), so the CHI gates are not met.
- SEC-04: passwords use Django's default hasher; MD5 is set only under `IS_TESTING` (`finance_tracker/settings.py:78`).
- SEC-05: no `.env` or key material is tracked; matches are placeholders (`SETUP.md:27`) or CI values (`.github/workflows/tests.yml:24`). The GA measurement id in `mkdocs.yml:144` is public by design.
- SEC-06: `DEBUG` defaults to False (`settings.py:61`); only CI turns it on.
- SEC-07 and SEC-08: every list, detail and write view scopes its queryset or `get_object_or_404` to `request.user`, `account__user` or `goal__user`; cron routes check a constant-time secret (`expenses/views/notifications.py:49-67`); JSON responses are built field by field.
- SEC-13: no log retention setting beyond container log rotation by size (`docker-compose.yml:29-33`), which does not state a time period; the gate (a retention setting for Personal Data processing logs) is not established.
- SEC-15: no dumps, logs, ID images or real fixtures are tracked; seed data is demo (`expenses/management/commands/setup_demo_user.py`). The founder photo `static/img/founder-omkar-pathak.jpg` is published on purpose.
- CON-06: `ConsentEvent` holds purpose, version and time (`expenses/models.py:3608-3615`).
- CON-07: the notice is itemised (`templates/privacy_policy.html:41-82`) and the app offers English, Hindi and Marathi (`settings.py:245-249`).
- CON-08: collected elements match the stated Purposes in the notice; no unrelated element was found.
- RET-03: needs a Third Schedule class, not shown.
- RIG-02: email, username, salary date and currency are editable (`expenses/forms.py` profile form).
- RIG-03: the notice names a Grievance Officer and a 30-day response (`templates/privacy_policy.html:416-430`).
- TRF-01 other than reCAPTCHA: all other outbound services are in the notice table; mfapi.in, AMFI and exchange-rate APIs receive no Personal Data (currency codes and fund names).

Out of catalogue, not labelled: `ALLOWED_HOSTS = ['*']` (`settings.py:82`), `android:allowBackup="true"` (`AndroidManifest.xml:5`), CSRF-exempt DNS-over-HTTPS handler (`expenses/views/misc.py:470`), consent bypass keyed on `sys.argv` containing `test` (`expenses/signals.py:84`).

## Judgement calls

- MON-01 treats the Sentry setup as monitoring configuration that covers no access or authentication events.
- SEC-16 treats the missing `USER` in the application Dockerfile as the root-container condition although the container is not a datastore.
- CON-01 entries rest on the absence of a consent check in background senders; whether drip or announcement mail is within the signup email Purpose is a legal reading.
- SEC-09 entries for search text treat transaction search terms as Financial Data.
- TRF-02 entries are disclosures; the notice already states the regions.

## Limitations

Single reviewer, static review only. Files listed under tree-wide searches were not opened one by one, so an absent entry is a negative adjudication on the searches named above, not proof of absence.

Review complete: yes
