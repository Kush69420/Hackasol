# Primary Target is OWASP Juice Shop, as-is

The Primary Target is OWASP Juice Shop, unmodified and pinned to commit `c9f99228`. Judges know it, nobody can say we planted its bugs, and its challenge list gives outside hints for building a hand-checked ground truth. It spans every surface the problem statement names: an Angular front end, an Express/TypeScript back end and API routes (including finale-rest generated ones), Sequelize schemas, a Dockerfile, `app.json`, YAML config and two Terraform trees. It also has real DPDP-relevant behaviour: unauthenticated exposure of user records, passwords logged through the URL, two-day access log retention, and an erasure request that does not erase. ai-kyc-platform (Aadhaar, PAN and biometrics; Next.js and FastAPI) is the only other Target before the Juice Shop Report is done. TrackMyRupee (real DPDP consent, withdrawal, export and erasure code in Django) serves Consent Assessment. singharya-btech/ML-Based-E-KYC-Fraud-Detection-System (a Data Processor integration, Kubernetes, committed ID images and logs) comes after the bonus features.

Supersedes the earlier choice of TrackMyRupee as Primary.

## Considered Options

- TrackMyRupee as Primary: the richest consent code, but unknown to judges, with no outside reference for accuracy and almost no Government Identifiers. It remains the Secondary Target for Consent Assessment.
- An India-specific overlay on Juice Shop (Aadhaar, PAN, phone and UPI fields): rejected. It modifies the Primary Target, and Government Identifiers are already shown through the Labelled Corpus and ai-kyc-platform.
- Build our own seeded India-native app: exact ground truth, but open to the "you planted the bugs" objection.
- NHA-ABDM/ABDM-wrapper: official health-consent stack, but Java-only with no front end. It would add a Java Rule set for a single target; revisit once the four chosen Targets are complete.
- youpi-pg/YouPI-PG: deep UPI coverage, but 76k LOC of JS that exercises no Issue Type the chosen set misses.

## Consequences

Juice Shop holds no Indian identifiers, so Government Identifier Findings come from ai-kyc-platform and the Labelled Corpus. No chosen target processes Child Data, so §9 and Rule 10 Rules will not fire on any real target. They are exercised only by the Labelled Corpus, and the Coverage Matrix marks them "covered, not exercised on a real Target".
