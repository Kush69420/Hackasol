# TrackMyRupee Consent Assessment

Secondary Target Application: `OmkarPathak/TrackMyRupee`, revision `47990e4f19d7debea70c5d56bab77e3c3f051546`. Target Application code is not part of this repository. Reproduce with:

```sh
git clone https://github.com/OmkarPathak/TrackMyRupee.git targets/trackmyrupee
git -C targets/trackmyrupee checkout 47990e4f19d7debea70c5d56bab77e3c3f051546
.venv/bin/dpdp-audit scan targets/trackmyrupee --provider ollama
.venv/bin/dpdp-audit scan targets/juice-shop --provider ollama
```

The scan excludes `expenses/tests/**`, bytecode and cache directories. Other source, templates and migrations remain in scope. Evidence below describes this pinned code, not runtime behaviour:

- `expenses/forms.py:876–918` defines age confirmation and consent controls, writes a profile boolean and creates an event for `Signup Data Collection`. `expenses/models.py:3608–3615` defines the event's Data Principal, action, Purpose, version and time fields. A boolean alone is not a Consent Record, and the code's version field does not by itself establish which notice was displayed.
- `expenses/views/misc.py:417–467` checks the submitted controls, updates the profile and creates an event for `Terms and Data Collection`. `expenses/urls.py:153` binds the view, and `templates/expenses/dpdp_consent.html:17–18` submits to that name. The controls for financial transactions and device information are initially checked (`templates/expenses/dpdp_consent.html:51–65`); an age self-declaration is at lines 69–75.
- `finance_tracker/settings.py:145–146` configures analytics and DPDPA middleware in that order. `expenses/middleware.py:124–150` exempts several named routes and redirects authenticated non-demo principals without the profile boolean; it is not proof that every individual Processing Operation is Purpose-specifically enforced.
- `expenses/urls.py:154` binds `WithdrawConsentView`; `expenses/views/settings.py:246–263` dispatches account deletion and logs out. The settings link appears at `templates/expenses/settings_home.html:196`, and `templates/expenses/withdraw_consent_confirm.html:30–38` contains the confirmation form. Dispatch is not Evidence that deletion actually completed or was propagated to a Data Processor.
- `expenses/middleware.py:243–259` sets request-local analytics consent from the `tmr_consent` cookie. `expenses/posthog_utils.py:99–115,120–135` checks that state before PostHog capture and identify calls. `templates/components/analytics.html:40–67` mirrors the browser choice and attempts local opt-out on decline. These code paths do not establish deletion of earlier Data Processor data or the terms of any contract.

Static step comparison counts each evidenced navigation link, required unselected checkbox and form submission as one action; text entry is excluded. Counts are comparable only from the same statically resolved starting template, and remain unknown when either path or its starting point cannot be resolved. Static Evidence does not substitute for Live Probes. The Juice Shop cookie banner (`frontend/src/index.html:19`) is Evidence of a banner only, not a consent grant.

## Live consent enforcement observation

A Live Probe run against the pinned revision on a local instance (loopback, Auditor-created accounts) did not confirm any consent-enforcement violation. Signup with any of the three optional consents declined was rejected, so those Purposes are enforced at signup (they are mandatory in the form rather than optional). Analytics requests did not follow a declined or withdrawn cookie choice while a granted control did produce a request, and account withdrawal left no authenticating account or linked rows. These are single-run observations of one local instance and do not establish deletion at Data Processors. The Report shows these as Live Probe entries beside the static Consent Assessment criteria without changing the static verdicts or creating Findings. See `docs/live-probes.md`.

The TrackMyRupee Replay Mode recording (`dashboard/recordings/trackmyrupee/`) carries that run: seven outcomes on "enforced server-side" (six Not Confirmed; `consent-after-withdrawal` Inconclusive) and one on "withdrawable with comparable ease" (`comparable-ease`, Inconclusive). The two browser checks were inconclusive because the adapter is redirected to `/consent/` after signup (the Target's middleware leaves `consent_granted` false). The deliverable Report under `reports/trackmyrupee/` is the static scan alone; the manifest's `live_probe_overlay` lists the run time, commit and every outcome.
