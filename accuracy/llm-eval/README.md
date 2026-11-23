# Held-out LLM evaluation labels

These four Report Targets are evaluation-only. Do not distill on any of their Elements or Findings.

## Classification (`classification-v1`)

`classification.jsonl` contains the masked prompts the Auditor generates for unresolved Personal Data Element candidates, with relative declaration anchors. Labels are **agent-adjudicated, not human-checked**. The adjudicating agent read each Target Application declaration and checked nearby usage where the declaration was ambiguous. `label` is the adjudicated Data Category, `teacher_label` and `teacher_value` are the category and full response from `omp:anthropic/claude-opus-5-5`, and `adjudication_note` explains the assignment. The file does not contain the raw declaration excerpts used for adjudication.

A null `label` means the declaration does not support treating the candidate as a Personal Data Element in the classification-v1 taxonomy. Classification-v1 cannot express null. Exclude these rows from Data Category macro-F1; report teacher/model over-classification on them separately. The teacher assigned a category to all 32 null-gold rows and agreed with 90 of the 104 in-taxonomy labels. All 136 teacher responses satisfied `valid_value`.

| Report Target (pinned revision) | Rows |
| --- | ---: |
| Juice Shop (`c9f99228d9d56afb5f5ca7925376292f7fa44b13`) | 101 |
| ai-kyc-platform (`70a821487c193be445810d836dd9b9b9ae22eb18`) | 13 |
| TrackMyRupee (`47990e4f19d7debea70c5d56bab77e3c3f051546`) | 19 |
| singharya-e-kyc (`e6e78d53edd30fd5be88dcd82d5afc1a2010d025`) | 3 |

Gold distribution: Profile 92, Contact 5, Financial 5, Government Identifier 1, Authentication Secret 1, null 32. No examples were adjudicated as Biometric, Health or Child Data. Profile dominates the in-taxonomy rows; the held-out set alone cannot establish breadth across Data Categories.

To recapture prompts without contacting an LLM:

```sh
python -m training.capture targets/{juice-shop,ai-kyc-platform,trackmyrupee,singharya-e-kyc}
```

## Triage

`triage-labels.json` labels Finding ids in `reports/juice-shop/report.json` using `auditor.accuracy.score_findings` against `accuracy/juice-shop.json`. A matched Finding is `true-positive` (45); an unmatched prediction, including a duplicate, is `false-positive` (7). Findings overlapping only not-determinable entries are excluded (0 in this Report). These are labels relative to the reviewed reference, not independent judgments of the triage prompt or its Provision citations.

Regenerate with `python -m training.dataset triage-gold` and review the output before replacing the committed file.
