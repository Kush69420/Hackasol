# Semgrep benchmark

Plain Semgrep registry rulesets, run over the four pinned Target Applications and compared with the committed HEAD Auditor reports. juice-shop is the Primary Target and has a reference list (`accuracy/juice-shop.json`); the three Secondary Targets have none, so they get run counts only.

## Method

- **Targets**: the pinned revisions that the committed HEAD reports were produced from (`Commit = HEAD report` is yes for all four): juice-shop `c9f99228d`, ai-kyc-platform `70a821487`, trackmyrupee `47990e4f1`, singharya-e-kyc `e6e78d53e`. Checkouts were clean.
- **Semgrep 1.186.0**: configs `p/default`, `p/secrets`, `p/owasp-top-ten`, fetched from the registry at run time. Flags: `--json --metrics=off --no-git-ignore --disable-version-check`. Semgrep does not use `.gitignore`; path filters are the exclusions below plus Semgrep's own `.semgrepignore`.
- **Exclusions**: the Auditor's `exclusions_for` globs are passed as `--exclude`, so both tools apply the same exclusion globs. Semgrep also applies `.semgrepignore` and a 1.0 MB size limit; those skips are counted below.
- **Masking**: `semgrep.json` is not raw output. String values under `results[]` and `errors[]` go through `auditor.masking.mask_for_report`; `path`, `check_id` and `fingerprint` are kept. Matched text is not a Finding, so scoring is unaffected, and the masked files contain no secret-pattern matches. The masker is a safeguard. `semgrep.log` is unmodified.
- **Scoring**: `auditor.accuracy.score_findings`, unchanged. A prediction is one Semgrep group, one per (file, start line, end line). Two modes:
  - *Location only*: Issue Type is `*` on both sides, so only the place is compared.
  - *Issue Type and location*: each Semgrep group maps to Issue Types through the catalogue's CWE links, giving one prediction per mapped Issue Type.
- **Auditor side**: read from `git show HEAD:reports/<target>/report.json`, not the working tree.
- **Checks**: the script cross-checks rule, file and result counts against the JSON and exits on mismatch.

Outputs: `benchmark/results/<target>/semgrep.json`, `benchmark/results/<target>/semgrep.log`, `benchmark/results/run.json`, and `benchmark/results/summary.json`.

## Semgrep run

| Target | Semgrep rules run | Files scanned | Skipped: `--exclude` | Skipped: over 1.0 MB | Skipped: `.semgrepignore` |
|---|---|---|---|---|---|
| juice-shop | 431 | 923 | 295 | 2 | 7 |
| ai-kyc-platform | 533 | 84 | 42 | 0 | 0 |
| trackmyrupee | 674 | 1063 | 0 | 7 | 249 |
| singharya-e-kyc | 362 | 33 | 14 | 0 | 2 |

`0` means Semgrep reported none in that category.

| Target | Errors | PartialParsing | Timeout | Syntax error |
|---|---|---|---|---|
| juice-shop | 53 | 50 | 3 | 0 |
| ai-kyc-platform | 1 | 1 | 0 | 0 |
| trackmyrupee | 166 | 161 | 0 | 5 |
| singharya-e-kyc | 0 | 0 | 0 | 0 |

A Timeout means Semgrep did not finish that analysis, so juice-shop has 3 incomplete analyses.

## Results

### Primary Target reference (juice-shop: 47 confirmed, 5 not determinable)

| Scoring | Tool | TP | FP | FN | Excluded | Precision | Recall |
|---|---|---|---|---|---|---|---|
| location only | Auditor | 44 | 8 | 3 | 0 | 0.85 | 0.94 |
| location only | Semgrep | 7 | 45 | 40 | 0 | 0.13 | 0.15 |
| Issue Type and location | Auditor | 45 | 7 | 2 | 0 | 0.87 | 0.96 |
| Issue Type and location | Semgrep | 1 | 3 | 46 | 0 | 0.25 | 0.02 |

- For Semgrep, FP means "no matching reference entry". The reference covers DPDP-scope Issue Types only, so these are off-reference hits, not verified false positives.
- Excluded counts predictions that overlap only not-determinable entries. They are neither TP nor FP. None occurred here.
- The Issue Type and location route leaves Semgrep 4 predictions in total (1 TP, 3 FP), because only some Semgrep groups carry a CWE that links to a DPDP Issue Type.
- The Auditor figures follow the recall Rules added after the first benchmark (then: location-only 0.81 / 0.36, Issue Type and location 0.76 / 0.34). Those Rules were written from the gaps on this same reference, so the Auditor's juice-shop figures are not held-out; see `accuracy/README.md`. The Semgrep side is unchanged (same version, configs and results).

### Overlap with Auditor Evidence (location only)

| Target | Semgrep groups | Groups on Auditor Evidence | Auditor Findings | Findings on Semgrep groups | Semgrep cross-file results | Auditor multi-file Findings |
|---|---|---|---|---|---|---|
| juice-shop | 52 | 8 | 52 | 10 | 0 | 44 |
| ai-kyc-platform | 9 | 1 | 7 | 1 | 0 | 2 |
| trackmyrupee | 452 | 0 | 5 | 0 | 0 | 0 |
| singharya-e-kyc | 0 | 0 | 0 | 0 | 0 | 0 |

- The two tools still flag mostly different places: 10 of 52 juice-shop Findings overlap a Semgrep group (8 of 52 Semgrep groups), and 1 of 7 in ai-kyc-platform.
- Auditor multi-file Findings are Findings whose Evidence spans more than one file. 44 of 52 juice-shop Findings do. Semgrep ran its OSS engine (`engine_kind` OSS on every result) and had no result with a trace into another file, so it has no counterpart.

### Primary Provisions and consent/erasure

| Target | Auditor Primary Provisions | Semgrep Primary Provisions (CWE route) | Auditor CON/RET Findings | Semgrep CON/RET predictions |
|---|---|---|---|---|
| juice-shop | 11 | 1 | 3 | 0 |
| ai-kyc-platform | 3 | 2 | 0 | 0 |
| trackmyrupee | 2 | 1 | 4 | 0 |
| singharya-e-kyc | 0 | 0 | 0 | 0 |

- The catalogue has 22 distinct Primary Provisions.
- The CWE route can only predict Issue Types that have a CWE link: SEC-01, SEC-02, SEC-04 to SEC-11, and SEC-16. CON, RET, RIG, CHI, TRF, MON and SEC-03, SEC-12 to SEC-15 have none, so Semgrep predicts 0 CON/RET findings by construction.

### File sets

| Target | Auditor walker files | Auditor excluded | Semgrep scanned | Both | Auditor only | Semgrep only |
|---|---|---|---|---|---|---|
| juice-shop | 1042 | 484 | 923 | 923 | 119 | 0 |
| ai-kyc-platform | 85 | 9598 | 84 | 84 | 1 | 0 |
| trackmyrupee | 1676 | 290 | 1063 | 1063 | 613 | 0 |
| singharya-e-kyc | 41 | 45 | 33 | 33 | 8 | 0 |

- The committed HEAD report file counts equal the walker counts for all four Targets.
- Semgrep scanned no file outside the Auditor's walker set.
- juice-shop's 119 Auditor-only files are 117 images, video or icons, plus 2 minified `.js` files under `frontend/src/assets/private/`.
- trackmyrupee's 613 Auditor-only files include 454 `.gz`, `.webp`, `.png`, `.woff2` or `.jpg` files and 134 `.js` files. The `.js` files are not explained. [INFERENCE] Semgrep's `paths.scanned` lists only files it analysed, which would omit binary and media files.

### Severity

| Auditor band | ERROR | WARNING |
|---|---|---|
| high | 2 | 9 |

- Eleven Auditor Findings overlap a Semgrep group (10 in juice-shop, 1 in ai-kyc-platform), all in the Auditor's high band; the highest overlapping Semgrep severity is ERROR for 2 and WARNING for 9. Semgrep severity is a rule-author label, not a DPDP Severity, so this shows only that the overlapping sites are ones Semgrep also ranks above INFO.
- Semgrep also emitted MEDIUM severity on juice-shop results. The overlap comparison ranks MEDIUM below INFO, and no Finding's highest overlapping Semgrep severity was MEDIUM.

## Limits

- The reference covers one Target at one revision. The Secondary Targets have no precision or recall here.
- Semgrep registry rulesets are not pinned. Rerunning later can change rule counts and results.
- Coverage is incomplete: juice-shop has 3 Timeouts and trackmyrupee has 166 errors (see the errors table).
- Semgrep ran its OSS engine only, so Auditor multi-file Evidence has no Semgrep counterpart in this run.
- The severity comparison rests on eleven overlaps on two Targets and supports no general conclusion.
- The masked `semgrep.json` departs from raw Semgrep output (see Method).

## Reproduce

```bash
bash benchmark/run_semgrep.sh          # uses .venv/bin/semgrep (1.186.0); fetches registry rules
.venv/bin/python benchmark/compare.py  # writes benchmark/results/summary.json and prints the tables
.venv/bin/python -m pytest tests/test_benchmark_compare.py -q
```
