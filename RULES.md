# Rules List

Generated from Rule metadata, the Issue Type catalogue, the Provision registry and the Labelled Corpus.

## SEC-01 — Personal Data written to logs

### SEC-01-nginx-query-logging — Personal Data route parameters written to nginx access logs

- Engine: config
- Languages / file kind: nginx
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-532
- CWE: CWE-532

Labelled Corpus example: `corpus/SEC-01-nginx-query-logging/positive/server.ts`

```
import express from "express"
import { lookup } from "./routes/users"
const app = express()
app.get("/api/users/:email", lookup())
```

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

### SEC-02-django-plain-fields — Django Personal Data Elements without field-level protection

- Engine: python-ast
- Languages / file kind: python
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 43A; CWE-311
- CWE: CWE-311

Labelled Corpus example: `corpus/SEC-02-django-plain-fields/positive/backend/records/models.py`

```
from django.db import models

class Record(models.Model):
    aadhaar_number = models.CharField(max_length=20)
```

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

### SEC-03-django-aadhaar-storage — Django Aadhaar number stored without field protection

- Engine: python-ast
- Languages / file kind: python
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 29; Aadhaar (Sharing of Information) Regulations 2016
- CWE: None

Labelled Corpus example: `corpus/SEC-03-django-aadhaar-storage/positive/backend/records/models.py`

```
from django.db import models

class DocumentType(models.TextChoices):
    AADHAAR = 'aadhaar', 'Aadhaar'
    PAN = 'pan', 'PAN'

class Document(models.Model):
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100)
```

### SEC-03-fastapi-aadhaar-response — FastAPI returns unmasked Aadhaar

- Engine: python-ast
- Languages / file kind: python
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 29; Aadhaar (Sharing of Information) Regulations 2016
- CWE: None

Labelled Corpus example: `corpus/SEC-03-fastapi-aadhaar-response/positive/main.py`

```
from fastapi import FastAPI

app = FastAPI()

class OCRService:
    def extract(self):
        data = {}
        data['aadhaar_number'] = 'synthetic'
        return data

ocr = OCRService()

```

### SEC-03-sequelize-aadhaar-storage — Aadhaar stored outside a vault

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: None
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 29; Aadhaar (Sharing of Information) Regulations 2016
- CWE: None

Labelled Corpus example: `corpus/SEC-03-sequelize-aadhaar-storage/positive/models/person.ts`

```
import { Model, DataTypes } from 'sequelize'
class Person extends Model {}
Person.init({ aadhaar: { type: DataTypes.STRING } }, { sequelize })
```

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

### SEC-06-express-error-disclosure — Verbose error response exposing Personal Data

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-489; CWE-209
- CWE: CWE-209, CWE-489

Labelled Corpus example: `corpus/SEC-06-express-error-disclosure/positive/server.ts`

```
import express from 'express'
const app = express()
app.get('/account', (req, res) => {
  try { throw new Error(req.body.email) } catch (error) { res.send(error.message) }
})
```

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

### SEC-11-fastapi-wildcard-cors — Wildcard CORS on FastAPI Personal Data routes

- Engine: python-ast
- Languages / file kind: python
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: CWE-319; CWE-614; CWE-942
- CWE: CWE-319, CWE-614, CWE-942

Labelled Corpus example: `corpus/SEC-11-fastapi-wildcard-cors/positive/main.py`

```
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])
@app.post('/face/match')
async def match(selfie_image: UploadFile = File(...)):
    content = await selfie_image.read()
    return face_service.match_faces(content)
```

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

### SEC-12-express-access-logging — Personal Data reads without access logging

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: compliance-gap
- Gate: no request or access logger configured anywhere
- Primary Provision: Rule 6(1)(c) (`DPDP-Rule-6(1)(c)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/SEC-12-express-access-logging/positive/server.ts`

```
import express from 'express'
import { User } from './models/user'
const app = express()
app.get('/accounts', async (req, res) => { const records = await User.findAll(); res.json(records) })
```

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

### SEC-14-terraform-store-backup — Persistent Personal Data store without configured backup

- Engine: config
- Languages / file kind: terraform
- Classification: compliance-gap
- Gate: deployment config for a persistent store exists and no backup is configured
- Primary Provision: Rule 6(1)(d) (`DPDP-Rule-6(1)(d)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/SEC-14-terraform-store-backup/positive/main.tf`

```
resource "aws_efs_file_system" "data" {
  encrypted = true
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ mountPoints = [{ sourceVolume = "data", containerPath = "/app/sqlite" }] }])
  volume {
    name = "data"
    efs_volume_configuration { file_system_id = aws_efs_file_system.data.id }
  }
}
```

## SEC-15 — Real Personal Data committed (fixtures, ID images, logs, DB dumps)

### SEC-15-committed-personal-data — Validated committed Personal Data

- Engine: config
- Languages / file kind: yaml, json, csv, sql, sqlite, log
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:L/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: values pass validators and are not seed or demo data (reserved or app-demo domains, placeholder names, documented test numbers); committed ID document images, logs and DB dumps always qualify
- Primary Provision: Rule 6(1)(a) (`DPDP-Rule-6(1)(a)`)
- Related Provisions: Section 29
- CWE: None

Labelled Corpus example: `corpus/SEC-15-committed-personal-data/positive/access.log`

```
login synthetic.person@acme-corp.com
```

## SEC-16 — Infrastructure misconfiguration exposing Personal Data stores (container as root, DB port public, public bucket)

### SEC-16-docker-root-container — Root container serving a Personal Data store

- Engine: config
- Languages / file kind: dockerfile, terraform
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-250
- CWE: CWE-250

Labelled Corpus example: `corpus/SEC-16-docker-root-container/positive/main.tf`

```
resource "null_resource" "build" {
  provisioner "local-exec" {
    command = "docker build -f ${path.module}/Dockerfile ."
  }
}
resource "aws_efs_file_system" "data" { encrypted = true }
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ mountPoints = [{ sourceVolume = "data", containerPath = "/app/sqlite" }] }])
  volume {
    name = "data"
    efs_volume_configuration { file_system_id = aws_efs_file_system.data.id }
  }
```

### SEC-16-kubernetes-privileged-store — Privileged or root workload mounting a Personal Data store

- Engine: config
- Languages / file kind: kubernetes
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-250
- CWE: CWE-250

Labelled Corpus example: `corpus/SEC-16-kubernetes-privileged-store/positive/k8s/app.yaml`

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: user-data
  namespace: app
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
```

### SEC-16-kubernetes-public-store — Public Service in front of a Personal Data store workload

- Engine: config
- Languages / file kind: kubernetes
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-250
- CWE: CWE-250

Labelled Corpus example: `corpus/SEC-16-kubernetes-public-store/positive/k8s/app.yaml`

```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: user-data
  namespace: app
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
```

### SEC-16-terraform-public-storage — Public Personal Data object store

- Engine: config
- Languages / file kind: terraform
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-250
- CWE: CWE-250

Labelled Corpus example: `corpus/SEC-16-terraform-public-storage/positive/main.tf`

```
resource "aws_s3_bucket" "records" {
  bucket = "records"
}
resource "aws_s3_bucket_acl" "records" {
  bucket = aws_s3_bucket.records.id
  acl = "public-read"
}
resource "aws_ecs_task_definition" "app" {
  container_definitions = jsonencode([{ name = "app", environment = [{ name = "RECORDS_BUCKET", value = aws_s3_bucket.records.id }] }])
}
```

### SEC-16-terraform-public-store — Public Personal Data store

- Engine: config
- Languages / file kind: terraform
- Classification: technical
- Base CVSS vector: CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N
- Gate: nexus
- Primary Provision: Rule 6(1)(b) (`DPDP-Rule-6(1)(b)`)
- Related Provisions: CWE-250
- CWE: CWE-250

Labelled Corpus example: `corpus/SEC-16-terraform-public-store/positive/main.tf`

```
resource "aws_db_instance" "accounts" {
  engine = "postgres"
  publicly_accessible = true
  vpc_security_group_ids = [aws_security_group.database.id]
}
resource "aws_security_group" "database" {
  ingress {
    from_port = 5432
    to_port = 5432
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
```

## CON-01 — Processing without an Enforcement Point, or with client-side gating only

### CON-01-express-enforcement — Processing without an Enforcement Point

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: processing not covered by a §7 legitimate use
- Primary Provision: Section 4(1) (`DPDP-Act-4(1)`)
- Related Provisions: Section 6(1); Section 7
- CWE: None

Labelled Corpus example: `corpus/CON-01-express-enforcement/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { User.create({ email: req.body.email }); res.send('ok') })
```

## CON-02 — Consent bundled across Purposes

### CON-02-angular-bundled-purposes — Consent bundled across Purposes

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: more than one Purpose found
- Primary Provision: Section 6(1) (`DPDP-Act-6(1)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-02-angular-bundled-purposes/positive/frontend/src/index.html`

```
<form><label><input name="consent" type="checkbox"> I agree to marketing and analytics</label></form>
```

## CON-03 — Pre-ticked or default-true consent

### CON-03-angular-default-true — Consent selected by default

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: a consent control exists
- Primary Provision: Section 6(1) (`DPDP-Act-6(1)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-03-angular-default-true/positive/frontend/src/index.html`

```
<form><input name="consent" type="checkbox" checked></form>
```

### CON-03-django-default-selected — Django consent selected by default

- Engine: config
- Languages / file kind: python, html
- Classification: compliance-gap
- Gate: a consent control exists
- Primary Provision: Section 6(1) (`DPDP-Act-6(1)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-03-django-default-selected/positive/app.py`

```
# Django Target Application marker.
```

## CON-04 — No Withdrawal Path, or one harder than the grant

### CON-04-django-comparable-paths — Django Withdrawal Path harder than grant

- Engine: config
- Languages / file kind: python, html
- Classification: compliance-gap
- Gate: a consent grant exists
- Primary Provision: Section 6(4) (`DPDP-Act-6(4)`)
- Related Provisions: Rule 3(c)(i)
- CWE: None

Labelled Corpus example: `corpus/CON-04-django-comparable-paths/positive/app.py`

```
class ConsentEvent(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField()
    purpose = models.CharField()
    consent_version = models.CharField()
    timestamp = models.DateTimeField(auto_now_add=True)

class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages", consent_version="v1")

```

### CON-04-express-withdrawal-path — Missing or harder Withdrawal Path

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: a consent grant exists
- Primary Provision: Section 6(4) (`DPDP-Act-6(4)`)
- Related Provisions: Rule 3(c)(i)
- CWE: None

Labelled Corpus example: `corpus/CON-04-express-withdrawal-path/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/consent', (req, res) => { Consent.create({ granted: true }); res.send('ok') })
```

## CON-05 — Withdrawal not propagated to Data Processors

### CON-05-express-processor-withdrawal — Withdrawal not propagated to a Data Processor

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: a Data Processor receives Personal Data
- Primary Provision: Section 6(6) (`DPDP-Act-6(6)`)
- Related Provisions: Section 8(7)(b)
- CWE: None

Labelled Corpus example: `corpus/CON-05-express-processor-withdrawal/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/marketing', (req, res) => { fetch('https://processor.example/send', { body: req.body.email }); res.send('ok') })
app.delete('/consent', (req, res) => { Consent.update({ granted: false }); res.send('ok') })
```

## CON-06 — Consent Record missing, or without Purpose, notice reference or time

### CON-06-django-incomplete-record — Django Consent Record missing required fields

- Engine: config
- Languages / file kind: python, html
- Classification: compliance-gap
- Gate: a consent grant exists
- Primary Provision: Section 6(10) (`DPDP-Act-6(10)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-06-django-incomplete-record/positive/app.py`

```
class ConsentEvent(models.Model):
    user = models.ForeignKey(User)
    action = models.CharField()
    purpose = models.CharField()
    timestamp = models.DateTimeField(auto_now_add=True)

class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages")

urlpatterns = [path("grant/", GrantView.as_view(), name="grant")]
```

### CON-06-sequelize-consent-record — Incomplete Consent Record

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: a consent grant exists
- Primary Provision: Section 6(10) (`DPDP-Act-6(10)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-06-sequelize-consent-record/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/consent', (req, res) => { Consent.create({ granted: true }); res.send('ok') })
```

## CON-07 — Notice not itemised, or no English/Eighth Schedule language option

### CON-07-angular-consent-notice — Incomplete consent notice

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: consent is requested
- Primary Provision: Section 5(1) (`DPDP-Act-5(1)`)
- Related Provisions: Section 5(3); Section 6(3); Rule 3(a); Rule 3(b)
- CWE: None

Labelled Corpus example: `corpus/CON-07-angular-consent-notice/positive/frontend/src/index.html`

```
<form><input name="consent" type="checkbox"></form>
```

### CON-07-django-unitemised-notice — Django consent notice not itemised

- Engine: config
- Languages / file kind: python, html
- Classification: compliance-gap
- Gate: consent is requested
- Primary Provision: Section 5(1) (`DPDP-Act-5(1)`)
- Related Provisions: Section 5(3); Section 6(3); Rule 3(a); Rule 3(b)
- CWE: None

Labelled Corpus example: `corpus/CON-07-django-unitemised-notice/positive/app.py`

```
class GrantView(View):
    template_name = "grant.html"
    def post(self, request):
        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages")

urlpatterns = [path("grant/", GrantView.as_view(), name="grant")]
```

## CON-08 — Personal Data Elements collected beyond the Purpose

### CON-08-angular-excess-elements — Personal Data Elements beyond the stated Purpose

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: a Purpose is stated
- Primary Provision: Section 6(1) (`DPDP-Act-6(1)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/CON-08-angular-excess-elements/positive/frontend/src/index.html`

```
<form><p>To send the newsletter we only need your email</p><input name="email" type="email"><input name="phone" type="tel"></form>
```

## RET-01 — No erasure once the Purpose is served

### RET-01-express-purpose-end — No erasure at the end of a Purpose

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: an account-closure or end-of-purpose event exists
- Primary Provision: Section 8(7)(a) (`DPDP-Act-8(7)(a)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/RET-01-express-purpose-end/positive/server.ts`

```
import express from 'express'
const app = express()
app.post('/account/close', async (req, res) => { await User.update({ closed: true }); res.send('closed') })
```

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

### RET-03-express-erasure-notice — No 48-hour notice before erasure

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: Third Schedule class (conditional; not assumed)
- Primary Provision: Rule 8(2) (`DPDP-Rule-8(2)`)
- Related Provisions: Rule 8(1); Third Schedule
- CWE: None

Labelled Corpus example: `corpus/RET-03-express-erasure-notice/positive/server.ts`

```
import express from 'express'
const app = express()
app.delete('/account/delete', async (req, res) => { await User.destroy({ where: { id: req.body.id } }); res.send('deleted') })
```

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

### RIG-03-express-grievance — No grievance mechanism or contact

- Engine: ts-ast
- Languages / file kind: typescript
- Classification: compliance-gap
- Gate: user accounts exist
- Primary Provision: Section 8(10) (`DPDP-Act-8(10)`)
- Related Provisions: Section 8(9); Section 13; Rule 9; Rule 14(3)
- CWE: None

Labelled Corpus example: `corpus/RIG-03-express-grievance/positive/models/user.ts`

```
import { Model, DataTypes } from 'sequelize'
class User extends Model {}
User.init({ email: { type: DataTypes.STRING } }, { sequelize })
```

## RIG-04 — No nomination

### RIG-04-rights-notice — DPDP rights notice omits nomination

- Engine: config
- Languages / file kind: json, html, markdown
- Classification: compliance-gap
- Gate: an in-repo notice or rights page lists Data Principal rights under the DPDP Act and omits nomination; otherwise not determinable
- Primary Provision: Section 14 (`DPDP-Act-14`)
- Related Provisions: Rule 14(4)
- CWE: None

Labelled Corpus example: `corpus/RIG-04-rights-notice/positive/notice.html`

```
<p>Under the Digital Personal Data Protection Act, your rights include access, correction and erasure.</p>
```

## CHI-01 — No age gate or verifiable parental consent

### CHI-01-age-parental-consent — Age gate or verifiable parental consent not evidenced

- Engine: ts-ast
- Languages / file kind: typescript, html
- Classification: compliance-gap
- Gate: the app collects age or DOB, or targets children (education, school, games)
- Primary Provision: Section 9(1) (`DPDP-Act-9(1)`)
- Related Provisions: Rule 10
- CWE: None

Labelled Corpus example: `corpus/CHI-01-age-parental-consent/positive/audience.html`

```
<p>This service is designed for children.</p>
```

## CHI-02 — Tracking, behavioural monitoring or targeted ads with no exclusion for Child Data

### CHI-02-child-tracking — Tracking without excluding Child Data

- Engine: ts-ast
- Languages / file kind: typescript, javascript, html
- Classification: compliance-gap
- Gate: CHI-01 gate met and tracking present
- Primary Provision: Section 9(3) (`DPDP-Act-9(3)`)
- Related Provisions: Rule 12; Fourth Schedule
- CWE: None

Labelled Corpus example: `corpus/CHI-02-child-tracking/positive/audience.html`

```
<p>This service is designed for children.</p>
<script>analytics.track('view');</script>
```

## TRF-01 — Personal Data shared with an SDK or API operated by a Data Processor without disclosure to the Data Principal (disclosure; capped at Medium)

### TRF-01-undisclosed-processor-transfer — Undisclosed Personal Data Transfer to a Data Processor

- Engine: ts-ast
- Languages / file kind: typescript, javascript
- Classification: disclosure
- Gate: an outbound flow of Personal Data exists
- Primary Provision: Section 11(1)(b) (`DPDP-Act-11(1)(b)`)
- Related Provisions: Section 8(2)
- CWE: None

Labelled Corpus example: `corpus/TRF-01-undisclosed-processor-transfer/positive/models/user.ts`

```
import { Model, DataTypes } from 'sequelize'
class User extends Model {}
User.init({ email: { type: DataTypes.STRING } }, { sequelize })
```

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

### MON-01-monitoring-coverage — Monitoring omits access and authentication events

- Engine: config
- Languages / file kind: json, yaml
- Classification: compliance-gap
- Gate: in-repo monitoring or alerting config exists and covers no access-log or authentication events; otherwise not determinable
- Primary Provision: Rule 6(1)(c) (`DPDP-Rule-6(1)(c)`)
- Related Provisions: None
- CWE: None

Labelled Corpus example: `corpus/MON-01-monitoring-coverage/positive/dashboard.json`

```
{"panels":[{"title":"HTTP Requests", "targets":[{"expr":"http_requests_count"}]}]}
```
