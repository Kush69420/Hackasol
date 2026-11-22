# Primary Target is TrackMyRupee, not a KYC app

The Primary Target is OmkarPathak/TrackMyRupee, a maintained Indian personal-finance app (Django) that already implements DPDP consent, withdrawal, export and erasure flows. Auditing whether those flows actually hold up exercises the consent-flow checks on code we did not write, so its Findings cannot be dismissed as planted. It has almost no Government Identifiers, so three Secondary Targets cover what it lacks: OWASP Juice Shop (third-party credibility and a public answer key for accuracy), JhashankKumar/ai-kyc-platform (Aadhaar, PAN and biometrics; Next.js and FastAPI), and singharya-btech/ML-Based-E-KYC-Fraud-Detection-System (a Data Processor integration, Kubernetes, committed ID images and logs).

## Considered Options

- Build our own seeded India-native app: exact ground truth, but open to the "you planted the bugs" objection, and it costs build time.
- A KYC app as Primary (ai-kyc-platform, singharya): dense Aadhaar/PAN, but toy-sized with almost no consent code to audit.
- NHA-ABDM/ABDM-wrapper: official health-consent stack, but Java-only with no front end. It would force a third language Rule set for a single target.
- youpi-pg/YouPI-PG: deep UPI coverage, but 76k LOC of JS that exercises no Issue Type the chosen set misses.

## Consequences

No chosen target processes Child Data, so §9 and Rule 10 Rules will not fire on any real target.
