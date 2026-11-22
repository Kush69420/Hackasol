# Rules List

Generated from Rule metadata, the Issue Type catalogue, the Provision registry and the Labelled Corpus.

## SEC-01 — Personal Data written to logs

### SEC-01-ts-morgan-query-secrets — Authentication Secrets in access logs

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-532
- CWE: CWE-532

Labelled Corpus example: `corpus/SEC-01-ts-morgan-query-secrets/positive/server.ts`

```
import { change } from './routes/account'
const app = express()
const accessLogStream = getStream({ filename: 'access.log', frequency: 'daily', max_logs: '2d' })
app.use(morgan('combined', { stream: accessLogStream }))
app.get('/password', change())
```

## SEC-02 — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

### SEC-02-sequelize-plain-fields — Personal Data Elements without field-level protection

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 43A; CWE-311
- CWE: CWE-311

Labelled Corpus example: `corpus/SEC-02-sequelize-plain-fields/positive/models/card.ts`

```
import { Model, DataTypes } from 'sequelize'
class Card extends Model {}
Card.init({ cardNum: { type: DataTypes.INTEGER } }, { sequelize })
```

## SEC-03 — Aadhaar number stored outside a vault or displayed unmasked

No Rule implemented at this slice.

## SEC-04 — Weak or missing password hashing

### SEC-04-ts-md5-password-hash — MD5 password hashing

- Engine: semgrep
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-916
- CWE: CWE-916

Labelled Corpus example: `corpus/SEC-04-ts-md5-password-hash/positive/models/account.ts`

```
User.init({ «SECRET» type: DataTypes.STRING, set («SECRET») { this.setDataValue('password', hash(password)) } } }, { sequelize })
const hash = (value: string) => crypto.createHash('md5').update(value).digest('hex')
```

## SEC-05 — Hard-coded secret or committed .env protecting Personal Data

### SEC-05-ts-hardcoded-jwt-key — Hard-coded JWT signing material

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-798
- CWE: CWE-798

Labelled Corpus example: `corpus/SEC-05-ts-hardcoded-jwt-key/positive/models/account.ts`

```
User.init({ «SECRET» type: DataTypes.STRING } }, { sequelize })
const signingKey = 'fixture-signing-material'
export const authorize = (account: object) => jwt.sign(account, signingKey)
```

## SEC-06 — Debug mode or verbose errors exposing Personal Data

No Rule implemented at this slice.

## SEC-07 — Missing authentication or ownership check on a route returning Personal Data

### SEC-07-ts-unchecked-nested-records — Unauthenticated nested Personal Data records

- Engine: semgrep
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-639; API1:2023
- CWE: CWE-639

Labelled Corpus example: `corpus/SEC-07-ts-unchecked-nested-records/positive/server.ts`

```
import express from 'express'
import cors from 'cors'
import { listMemories } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', listMemories())
```

## SEC-08 — Over-exposed responses (whole model or nested records serialised)

### SEC-08-ts-account-list — Account list serializes Personal Data

- Engine: semgrep
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: Section 6(1); CWE-213; API3:2023
- CWE: CWE-213

Labelled Corpus example: `corpus/SEC-08-ts-account-list/positive/server.ts`

```
import express from 'express'
import cors from 'cors'
import { listAccounts } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', security.isAuthorized(), listAccounts())
```

### SEC-08-ts-nested-records — Nested Personal Data records in responses

- Engine: semgrep
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: Section 6(1); CWE-213; API3:2023
- CWE: CWE-213

Labelled Corpus example: `corpus/SEC-08-ts-nested-records/positive/server.ts`

```
import express from 'express'
import cors from 'cors'
import { listMemories } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', listMemories())
```

### SEC-08-ts-review-author — Review author Personal Data exposed

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: Section 6(1); CWE-213; API3:2023
- CWE: CWE-213

Labelled Corpus example: `corpus/SEC-08-ts-review-author/positive/server.ts`

```
import express from 'express'
import { writeReview, readReviews } from './routes/reviews'
import { account } from './routes/account'
const app = express()
app.get('/account', account())
app.get('/reviews', readReviews())
app.put('/reviews', writeReview())
```

## SEC-09 — Personal Data or Authentication Secrets in URLs or query strings

### SEC-09-ts-query-authentication-secret — Authentication Secrets in query strings

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-598
- CWE: CWE-598

Labelled Corpus example: `corpus/SEC-09-ts-query-authentication-secret/positive/server.ts`

```
import { change } from './routes/account'
const app = express()
const accessLogStream = getStream({ filename: 'access.log', frequency: 'daily', max_logs: '2d' })
app.use(morgan('combined', { stream: accessLogStream }))
app.get('/password', change())
```

## SEC-10 — Personal Data in localStorage, sessionStorage, cookies or outbound headers

### SEC-10-ts-storage-header — Personal Data stored and attached to intercepted requests

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-922
- CWE: CWE-922

Labelled Corpus example: `corpus/SEC-10-ts-storage-header/positive/frontend/src/app/Services/request.interceptor.ts`

```
class Login { login(account: any) { localStorage.setItem('email', account.email) } }
class RequestInterceptor implements HttpInterceptor {
 intercept(req: HttpRequest<any>, next: HttpHandler) {
  req = req.clone({ setHeaders: { 'X-User-Email': String(localStorage.getItem('email')) } })
  return next.handle(req)
 }
}
```

## SEC-11 — Insecure transport, cookie flags or CORS wildcard on Personal Data routes

### SEC-11-ts-wildcard-cors — Wildcard CORS on Personal Data response routes

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-319; CWE-614; CWE-942
- CWE: CWE-319, CWE-614, CWE-942

Labelled Corpus example: `corpus/SEC-11-ts-wildcard-cors/positive/server.ts`

```
import express from 'express'
import cors from 'cors'
import { listMemories } from './routes/list'
const app = express()
app.use(cors())
app.get('/records', listMemories())
```

## SEC-12 — No access logging on reads of Personal Data

No Rule implemented at this slice.

## SEC-13 — Logs of Personal Data processing kept under one year

### SEC-13-ts-access-log-retention — Short Personal Data access-log retention

- Engine: config
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: a log retention setting exists
- Primary Provision: Rule 6(1)(e) (`DPDP-Rule-6(1)(e)`)
- Related Provisions: Rule 8(3)
- CWE: None

Labelled Corpus example: `corpus/SEC-13-ts-access-log-retention/positive/server.ts`

```
import { change } from './routes/account'
const app = express()
const accessLogStream = getStream({ filename: 'access.log', frequency: 'daily', max_logs: '2d' })
app.use(morgan('combined', { stream: accessLogStream }))
app.get('/password', change())
```

## SEC-14 — No backup for Personal Data stores

No Rule implemented at this slice.

## SEC-15 — Real Personal Data committed (fixtures, ID images, logs, DB dumps)

No Rule implemented at this slice.

## SEC-16 — Infrastructure misconfiguration exposing Personal Data stores (container as root, DB port public, public bucket)

No Rule implemented at this slice.

## CON-01 — Processing without an Enforcement Point, or with client-side gating only

No Rule implemented at this slice.

## CON-02 — Consent bundled across Purposes

No Rule implemented at this slice.

## CON-03 — Pre-ticked or default-true consent

No Rule implemented at this slice.

## CON-04 — No Withdrawal Path, or one harder than the grant

No Rule implemented at this slice.

## CON-05 — Withdrawal not propagated to Data Processors

No Rule implemented at this slice.

## CON-06 — Consent Record missing, or without Purpose, notice reference or time

No Rule implemented at this slice.

## CON-07 — Notice not itemised, or no English/Eighth Schedule language option

No Rule implemented at this slice.

## CON-08 — Personal Data Elements collected beyond the Purpose

No Rule implemented at this slice.

## RET-01 — No erasure once the Purpose is served

No Rule implemented at this slice.

## RET-02 — Erasure request that does not erase (flag only, soft delete, Elements or Data Processors skipped)

### RET-02-express-erasure-request — Erasure request records a flag without erasure

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: an erasure route or request exists
- Primary Provision: Section 12(3) (`DPDP-Act-12(3)`)
- Related Provisions: Section 8(7); Section 8(7)(b)
- CWE: None

Labelled Corpus example: `corpus/RET-02-express-erasure-request/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/dataerasure', async (req, res) => { await PrivacyRequestModel.create({ deletionRequested: true }); res.send('received') })
```

## RET-03 — No 48-hour notice before erasure

No Rule implemented at this slice.

## RIG-01 — Access summary missing, or omitting Personal Data Elements the app processes for that Data Principal; omitting the Data Fiduciaries and Data Processors it shared data with counts only where a sharing flow is evidenced

### RIG-01-express-incomplete-export — Access summary omits Personal Data Elements

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: user accounts holding Personal Data exist
- Primary Provision: Section 11(1)(a) (`DPDP-Act-11(1)(a)`)
- Related Provisions: Section 11(1)(b); Rule 14
- CWE: None

Labelled Corpus example: `corpus/RIG-01-express-incomplete-export/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/data-export', (req, res) => { res.send({ email: req.user.email }) })
```

## RIG-02 — No route to correct, complete or update Personal Data Elements

### RIG-02-express-email-correction — No evidenced email correction path

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: user-editable Personal Data Elements exist
- Primary Provision: Section 12(2) (`DPDP-Act-12(2)`)
- Related Provisions: Rule 14
- CWE: None

Labelled Corpus example: `corpus/RIG-02-express-email-correction/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/profile', async (req, res) => { await user.update({ username: req.body.username }); res.send('ok') })
```

## RIG-03 — No grievance mechanism or contact for Personal Data queries

No Rule implemented at this slice.

## RIG-04 — No nomination

No Rule implemented at this slice.

## CHI-01 — No age gate or verifiable parental consent

No Rule implemented at this slice.

## CHI-02 — Tracking, behavioural monitoring or targeted ads with no exclusion for Child Data

No Rule implemented at this slice.

## TRF-01 — Personal Data shared with an SDK or API operated by a Data Processor without disclosure to the Data Principal (disclosure; capped at Medium)

No Rule implemented at this slice.

## TRF-02 — Personal Data sent or stored outside India (disclosure, capped at Medium; Needs Legal Review unless the destination is restricted under §16)

### TRF-02-terraform-storage-region — Storage configured outside India

- Engine: config
- Languages / file kind: terraform
- Classification: disclosure
- Gate: None
- Primary Provision: Section 16(1) (`DPDP-Act-16(1)`)
- Related Provisions: Rule 15; Rule 13(4)
- CWE: None

Labelled Corpus example: `corpus/TRF-02-terraform-storage-region/positive/main.tf`

```
provider "aws" {
  region = var.aws_region
}
variable "aws_region" {
  default = "eu-west-1"
}
resource "aws_efs_file_system" "data" {
  encrypted = true
}
```

## MON-01 — No monitoring or review of access logs to detect unauthorised access

No Rule implemented at this slice.
