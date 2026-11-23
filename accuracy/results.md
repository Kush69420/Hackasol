# Measured accuracy

- Target: juice-shop pinned at `c9f99228d9d56afb5f5ca7925376292f7fa44b13`
- Reference: `accuracy/juice-shop.json` (47 confirmed, 5 not-determinable and excluded from scoring)
- Command: `dpdp-audit accuracy targets/juice-shop --cache-only --cache-dir accuracy/cache --reference accuracy/juice-shop.json --results accuracy/results.md --provider omp --model anthropic/claude-opus-5-5`
- Rules digest: `16c6f1df4175e43ee048dd0ee52eb36634b6740fefc8a67a204c6ad9e371f858`

## Static scoring (Reference Target)

Static figures count only deterministic Findings. Live Probe outcomes are never added to them.

| Issue Type | TP | FP | FN | Precision | Recall | F1 | Live Probe confirmations |
|---|---|---|---|---|---|---|---|
| MON-01 | 0 | 1 | 1 | 0.0000 | 0.0000 | 0.0000 | not run |
| RET-01 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| RET-02 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| RET-03 | 0 | 1 | 0 | 0.0000 | N/A | 0.0000 | not run |
| RIG-01 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| RIG-02 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-01 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-02 | 2 | 3 | 0 | 0.4000 | 1.0000 | 0.5714 | not run |
| SEC-04 | 3 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-05 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-07 | 10 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-08 | 6 | 2 | 1 | 0.7500 | 0.8571 | 0.8000 | not run |
| SEC-09 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-10 | 5 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-11 | 5 | 1 | 0 | 0.8333 | 1.0000 | 0.9091 | not run |
| SEC-13 | 1 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| SEC-14 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| TRF-02 | 2 | 0 | 0 | 1.0000 | 1.0000 | 1.0000 | not run |
| **Overall** | 45 | 8 | 2 | 0.8491 | 0.9574 | 0.9000 | not run |

## Reference entries

- Matched (45): REF-045, REF-046, REF-047, REF-048, REF-001, REF-003, REF-002, REF-005, REF-004, REF-006, REF-008, REF-007, REF-015, REF-016, REF-018, REF-011, REF-014, REF-013, REF-019, REF-010, REF-017, REF-012, REF-023, REF-026, REF-027, REF-022, REF-024, REF-025, REF-028, REF-029, REF-034, REF-033, REF-032, REF-031, REF-030, REF-038, REF-039, REF-037, REF-035, REF-036, REF-040, REF-042, REF-041, REF-052, REF-051
- Missed (2): REF-021, REF-044
- Not-determinable, excluded (5): REF-009, REF-020, REF-043, REF-049, REF-050
- Unmatched predictions (8): MON-01-8c5728dfea11 (no reference entry with this Issue Type at this anchor), RET-03-41bffe4101f9 (no reference entry with this Issue Type at this anchor), SEC-02-0a13729d5971 (no reference entry with this Issue Type at this anchor), SEC-02-0f4631e6a05d (no reference entry with this Issue Type at this anchor), SEC-02-e0994a7481e3 (no reference entry with this Issue Type at this anchor), SEC-08-5b7f92b613ca (no reference entry with this Issue Type at this anchor), SEC-08-ca532d12729b (no reference entry with this Issue Type at this anchor), SEC-11-5a71594e3942 (no reference entry with this Issue Type at this anchor)
- Excluded predictions (0): none

## Live Probe confirmations

not run: no Finding in this Report carries a Live Probe outcome.

## Labelled Corpus

65 Rules, one positive and one near-miss negative each (Rule emissions on fixtures).

| | TP | FP | FN | TN | Precision | Recall |
|---|---|---|---|---|---|---|
| **Total** | 65 | 0 | 0 | 65 | 1.0000 | 1.0000 |

Rules with a corpus FP or FN: none

## LLM replay

- Mode: cache-only (omp/anthropic/claude-opus-5-5); prompts: classification: classification-v1, consent: consent-v2, fix: fix-v1, triage: triage-v2
- Cache: 208 hit(s), 0 miss(es), 0 not assessed
- Reproduces published run: yes

## Method

Reference Target: each canonical Finding is one prediction. It matches a confirmed reference entry when the Issue Type and normalised file path are equal and any Finding Evidence range overlaps the entry's reviewed anchor range. Matching is one-to-one, in Finding id order, each prediction taking the lowest-id unmatched entry; a second prediction for a matched entry is a false positive. A Finding that merges several Rules is one prediction. Labelled Corpus: for each Rule, the positive counts as a true positive if the Rule emits there (else a false negative) and the negative counts as a false positive if the Rule emits there (else a true negative); Rule emissions are counted, not merged Findings. Precision = TP/(TP+FP); recall = TP/(TP+FN); a zero denominator is N/A.

## Limitations

- The Reference Target reference list covers one Target Application at one pinned revision; the figures say nothing about any Secondary Target.
- The reference list is hand-checked by the authors, so omissions and judgement calls bias recall and precision; entries that could not be determined are excluded, not scored.
- A Finding whose only overlapping same-Issue-Type reference entries are not-determinable is neither a true nor a false positive; it is listed as an excluded prediction.
- Labelled Corpus cases are small designed fixtures: one pair per Rule shows the Rule works on that pair, not how often it is right on real code.
- LLM verdicts are replayed from a versioned cache and never change which Findings exist; a cache miss is 'not assessed' and the run does not reproduce the published figures.
