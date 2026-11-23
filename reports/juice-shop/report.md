# Report

## Applicability Assumptions

- AA-1: The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India. Provisions: DPDP-Act-3 — Section 3. Dependent Findings: SEC-07-2d4f025671b7, SEC-08-a535cd15b04b, SEC-01-d85a743d0415, SEC-04-bebc3e7f55ae, SEC-10-d70f56f17198, SEC-10-d0971bb44714, SEC-08-177006878772, TRF-02-56fc1119eb9b, SEC-02-03b1356ecc57, SEC-02-0f4631e6a05d, SEC-02-b6efa0cd2309, SEC-02-e0994a7481e3, SEC-13-394d3dbca514, MON-01-8c5728dfea11, SEC-14-c5e9ac6a126d, RET-02-4696497b9137, RET-03-41bffe4101f9, RIG-01-a9383e4db278, RIG-02-f7117cbcde8b

- AA-2: The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional. Provisions: DPDP-Act-10 — Section 10. Dependent Findings: TRF-02-56fc1119eb9b

- AA-3: The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional. Provisions: DPDP-Rule-8(1) — Rule 8(1), DPDP-Rules-Schedule-Third — Third Schedule. Dependent Findings: RET-03-41bffe4101f9

- AA-4: Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed. Provisions: DPDP-Act-7 — Section 7. Dependent Findings: SEC-07-2d4f025671b7, SEC-08-a535cd15b04b, SEC-08-177006878772

## Executive summary

| Severity | DPDP obligation | security dependent on Personal Data | Safeguard |
| --- | --- | --- | --- |
| critical | 0 | 0 | 0 |
| high | 0 | 6 | 2 |
| medium | 1 | 6 | 0 |
| low | 4 | 2 | 0 |

Penalty Ceilings: ₹250 crore, ₹50 crore; statutory maximum under the Schedule; the Board sets any amount.

### Fix before 14 May 2027

- SEC-07-2d4f025671b7 — Enforceable From 2027-05-14
- SEC-08-a535cd15b04b — Enforceable From 2027-05-14
- SEC-11-ad5b2106f4e8 — Enforceable From 2027-05-14
- SEC-01-d85a743d0415 — Enforceable From 2027-05-14
- SEC-04-bebc3e7f55ae — Enforceable From 2027-05-14
- SEC-05-c695dda06010 — Enforceable From 2027-05-14
- SEC-10-d70f56f17198 — Enforceable From 2027-05-14
- SEC-10-d0971bb44714 — Enforceable From 2027-05-14
- SEC-08-177006878772 — Enforceable From 2027-05-14
- TRF-02-56fc1119eb9b — Enforceable From 2027-05-14
- SEC-02-03b1356ecc57 — Enforceable From 2027-05-14
- SEC-02-0f4631e6a05d — Enforceable From 2027-05-14
- SEC-02-b6efa0cd2309 — Enforceable From 2027-05-14
- SEC-02-e0994a7481e3 — Enforceable From 2027-05-14
- SEC-13-394d3dbca514 — Enforceable From 2027-05-14
- MON-01-8c5728dfea11 — Enforceable From 2027-05-14
- SEC-14-c5e9ac6a126d — Enforceable From 2027-05-14
- RET-02-4696497b9137 — Enforceable From 2027-05-14
- RET-03-41bffe4101f9 — Enforceable From 2027-05-14
- RIG-01-a9383e4db278 — Enforceable From 2027-05-14
- RIG-02-f7117cbcde8b — Enforceable From 2027-05-14

## Personal Data Map

| Element | Data Category | Processing Operations (Evidence) |
| --- | --- | --- |
| collection:reviewsCollection.author | Profile | Collect (frontend/src/app/product-details/product-details.component.ts:80–80); Collect (frontend/src/app/product-details/product-details.component.ts:91–91); Collect (frontend/src/app/Services/product-review.service.ts:29–29); Collect (server.ts:673–673); Collect (routes/createProductReviews.ts:26–26); Store (routes/createProductReviews.ts:26–26); Expose (routes/showProductReviews.ts:45–45) |
| collection:ordersCollection.email | Contact | None recorded |
| header:Authorization | Authentication Secret | None recorded |
| storage:localStorage.email | Contact | Store (frontend/src/app/login/login.component.ts:106–106) |
| header:X-User-Email | Contact | None recorded |
| storage:localStorage.totp_tmp_token | Authentication Secret | Store (frontend/src/app/login/login.component.ts:118–118) |
| storage:sessionStorage.addressId | Contact | Store (frontend/src/app/address/address.component.ts:89–89) |
| storage:localStorage.token | Authentication Secret | Store (frontend/src/app/login/login.component.ts:150–150); Store (frontend/src/app/oauth/oauth.component.ts:52–52); Store (frontend/src/app/payment/payment.component.ts:233–233); Store (frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:54–54) |
| form:frontend/src/app/change-password/change-password.component.html#currentPassword | Authentication Secret | None recorded |
| form:frontend/src/app/change-password/change-password.component.html#newPassword | Authentication Secret | None recorded |
| form:frontend/src/app/change-password/change-password.component.html#repeatNewPassword | Authentication Secret | None recorded |
| form:frontend/src/app/contact/contact.component.html#authorControl | Profile | None recorded |
| form:frontend/src/app/forgot-password/forgot-password.component.html#email | Contact | None recorded |
| form:frontend/src/app/forgot-password/forgot-password.component.html#securityQuestion | Authentication Secret | None recorded |
| form:frontend/src/app/forgot-password/forgot-password.component.html#password | Authentication Secret | None recorded |
| form:frontend/src/app/forgot-password/forgot-password.component.html#repeatPassword | Authentication Secret | None recorded |
| form:frontend/src/app/login/login.component.html#email | Contact | None recorded |
| form:frontend/src/app/login/login.component.html#password | Authentication Secret | None recorded |
| storage:cookie.token | Authentication Secret | Store (frontend/src/app/login/login.component.ts:153–153); Store (frontend/src/app/oauth/oauth.component.ts:51–51); Store (frontend/src/app/payment/payment.component.ts:234–234); Store (frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:57–57) |
| storage:sessionStorage.walletTotal | Financial | Store (frontend/src/app/wallet/wallet.component.ts:45–45) |
| form:frontend/src/app/register/register.component.html#repeatPassword | Authentication Secret | None recorded |
| form:frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.html#token | Authentication Secret | None recorded |
| form:frontend/src/app/two-factor-auth/two-factor-auth.component.html#passwordControl | Authentication Secret | None recorded |
| form:frontend/src/app/two-factor-auth/two-factor-auth.component.html#initialTokenControl | Authentication Secret | None recorded |
| form:frontend/src/app/wallet/wallet.component.html#balanceControl | Financial | None recorded |
| form:frontend/src/app/web3-sandbox/web3-sandbox.component.html#selectedContractName | Profile | None recorded |
| model:Address.fullName | Profile | Collect (frontend/src/app/address-create/address-create.component.html:14–14); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:41–43); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Address.mobileNum | Contact | Collect (frontend/src/app/address-create/address-create.component.html:30–30); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:44–51); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Address.zipCode | Contact | Collect (frontend/src/app/address-create/address-create.component.html:41–41); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:52–57); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Address.streetAddress | Contact | Collect (frontend/src/app/address-create/address-create.component.html:53–55); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:58–63); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Address.city | Contact | Collect (frontend/src/app/address-create/address-create.component.html:71–71); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:64–64); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Address.state | Contact | Collect (frontend/src/app/address-create/address-create.component.html:79–79); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:65–65); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262); Store (frontend/src/app/web3-sandbox/web3-sandbox.component.ts:89–102) |
| model:Address.country | Contact | Collect (frontend/src/app/address-create/address-create.component.html:22–22); Collect (frontend/src/app/address-create/address-create.component.ts:91–91); Collect (frontend/src/app/Services/address.service.ts:35–35); Collect (server.ts:540–546); Collect (server.ts:482–482); Store (models/address.ts:66–66); Expose (routes/address.ts:12–12); Expose (routes/address.ts:20–20); Collect (frontend/src/app/Services/address.service.ts:30–30); Collect (server.ts:480–480); Store (data/datacreator.ts:253–262) |
| model:Card.fullName | Profile | Collect (frontend/src/app/payment-method/payment-method.component.html:53–53); Collect (frontend/src/app/payment-method/payment-method.component.ts:77–77); Collect (frontend/src/app/Services/payment.service.ts:30–30); Collect (server.ts:540–546); Collect (server.ts:470–470); Store (models/card.ts:37–37); Expose (routes/payment.ts:26–26); Expose (routes/payment.ts:53–53); Store (data/datacreator.ts:271–277) |
| model:Card.cardNum | Financial | Collect (frontend/src/app/payment-method/payment-method.component.html:62–62); Collect (frontend/src/app/payment-method/payment-method.component.ts:78–78); Collect (frontend/src/app/Services/payment.service.ts:30–30); Collect (server.ts:540–546); Collect (server.ts:470–470); Store (models/card.ts:38–45); Expose (routes/payment.ts:32–32); Expose (routes/payment.ts:58–58); Store (data/datacreator.ts:271–277) |
| model:Card.expMonth | Financial | Collect (frontend/src/app/payment-method/payment-method.component.html:77–77); Collect (frontend/src/app/payment-method/payment-method.component.ts:79–79); Collect (frontend/src/app/Services/payment.service.ts:30–30); Collect (server.ts:540–546); Collect (server.ts:470–470); Store (models/card.ts:46–53); Expose (routes/payment.ts:28–28); Expose (routes/payment.ts:54–54); Store (data/datacreator.ts:271–277) |
| model:Card.expYear | Financial | Collect (frontend/src/app/payment-method/payment-method.component.html:90–90); Collect (frontend/src/app/payment-method/payment-method.component.ts:80–80); Collect (frontend/src/app/Services/payment.service.ts:30–30); Collect (server.ts:540–546); Collect (server.ts:470–470); Store (models/card.ts:54–61); Expose (routes/payment.ts:29–29); Expose (routes/payment.ts:55–55); Store (data/datacreator.ts:271–277) |
| model:Recycle.AddressId | Contact | Store (data/datacreator.ts:681–687) |
| model:SecurityAnswer.answer | Authentication Secret | Collect (frontend/src/app/register/register.component.html:93–95); Collect (frontend/src/app/register/register.component.ts:109–109); Collect (frontend/src/app/Services/security-answer.service.ts:21–21); Collect (server.ts:540–546); Store (models/securityAnswer.ts:42–47); Expose (server.ts:625–631); Store (data/datacreator.ts:707–707); Log (data/datacreator.ts:708–708) |
| model:User.username | Profile | Store (data/datacreator.ts:192–201); Store (routes/updateUserProfile.ts:38–38) |
| model:User.email | Contact | Collect (frontend/src/app/register/register.component.html:16–17); Collect (frontend/src/app/register/register.component.ts:98–98); Collect (frontend/src/app/Services/user.service.ts:38–38); Collect (server.ts:540–546); Collect (server.ts:440–451); Collect (server.ts:452–452); Collect (server.ts:453–453); Collect (server.ts:454–454); Store (models/user.ts:56–69); Expose (routes/changePassword.ts:56–56); Expose (routes/saveLoginIp.ts:33–33); Expose (server.ts:625–631); Store (data/datacreator.ts:192–201); Store (data/datacreator.ts:326–329) |
| model:User.password | Authentication Secret | Collect (frontend/src/app/register/register.component.html:28–29); Collect (frontend/src/app/register/register.component.ts:99–99); Collect (frontend/src/app/Services/user.service.ts:38–38); Collect (server.ts:540–546); Collect (server.ts:440–451); Collect (server.ts:452–452); Collect (server.ts:453–453); Collect (server.ts:454–454); Store (models/user.ts:70–75); Expose (routes/changePassword.ts:56–56); Expose (routes/saveLoginIp.ts:33–33); Store (data/datacreator.ts:192–201); Store (data/datacreator.ts:326–329); Expose (routes/authenticatedUsers.ts:14–31); Store (routes/changePassword.ts:51–51); Store (routes/resetPassword.ts:44–44) |
| model:User.deluxeToken | Authentication Secret | Store (data/datacreator.ts:192–201); Store (routes/deluxe.ts:43–43) |
| model:User.lastLoginIp | Profile | Store (data/datacreator.ts:192–201); Store (routes/saveLoginIp.ts:32–32) |
| model:User.profileImage | Profile | Store (data/datacreator.ts:192–201); Store (routes/profileImageFileUpload.ts:50–50); Store (routes/profileImageUrlUpload.ts:32–32); Store (routes/profileImageUrlUpload.ts:36–36) |
| model:User.totpSecret | Authentication Secret | Store (data/datacreator.ts:192–201); Expose (routes/authenticatedUsers.ts:14–31) |
| model:Wallet.balance | Financial | Store (data/datacreator.ts:220–223); Log (frontend/src/app/faucet/faucet.component.ts:132–132); Log (frontend/src/app/faucet/faucet.component.ts:150–150); Log (frontend/src/app/faucet/faucet.component.ts:226–226); Expose (routes/wallet.ts:14–14); Expose (routes/wallet.ts:28–28) |
| param:POST /rest/2fa/verify#body.tmpToken | Authentication Secret | None recorded |
| param:POST /rest/2fa/verify#body.totpToken | Authentication Secret | None recorded |
| param:POST /rest/2fa/setup#body.initialToken | Authentication Secret | None recorded |
| param:POST /rest/2fa/setup#body.password | Authentication Secret | None recorded |
| param:POST /rest/2fa/setup#body.setupToken | Authentication Secret | None recorded |
| param:POST /rest/2fa/disable#body.password | Authentication Secret | None recorded |
| param:GET /rest/user/change-password?current | Authentication Secret | Collect (frontend/src/app/Services/user.service.ts:54–55); Log (server.ts:370–370) |
| param:GET /rest/user/change-password?new | Authentication Secret | Collect (frontend/src/app/Services/user.service.ts:54–55); Log (server.ts:370–370) |
| param:GET /rest/user/change-password?repeat | Authentication Secret | Collect (frontend/src/app/Services/user.service.ts:54–55); Log (server.ts:370–370) |
| param:PUT /rest/products/{id}/reviews#body.author | Profile | None recorded |
| param:POST /rest/user/login#body.email | Contact | None recorded |
| param:POST /rest/user/login#body.password | Authentication Secret | None recorded |
| param:POST /rest/web3/walletNFTVerify#body.walletAddress | Financial | None recorded |
| collection:ordersCollection.addressId | Contact | Store (frontend/src/app/address/address.component.ts:89–89) |
| param:POST /rest/passkey/register-verify#body.regToken | Authentication Secret | None recorded |
| param:POST /rest/passkey/login-options#body.email | Contact | None recorded |
| param:POST /rest/passkey/login-verify#body.authToken | Authentication Secret | None recorded |
| param:POST /rest/user/reset-password#body.email | Contact | None recorded |
| param:POST /rest/user/reset-password#body.answer | Authentication Secret | None recorded |
| param:POST /rest/user/reset-password#body.new | Authentication Secret | None recorded |
| param:POST /rest/user/reset-password#body.repeat | Authentication Secret | None recorded |
| param:GET /rest/user/security-question?email | Contact | Collect (frontend/src/app/Services/security-question.service.ts:25–25); Log (server.ts:370–370) |
| param:POST /profile#body.username | Profile | None recorded |
| param:POST /rest/web3/walletExploitAddress#body.walletAddress | Financial | None recorded |
| param:POST /api/Users#body.email | Contact | None recorded |
| param:POST /api/Users#body.password | Authentication Secret | None recorded |
| param:POST /api/Users#body.passwordRepeat | Authentication Secret | None recorded |
| form:views/dataErasureForm.hbs#email | Contact | None recorded |
| form:views/dataErasureForm.hbs#securityAnswer | Authentication Secret | None recorded |

## Findings

### SEC-07-2d4f025671b7 — Missing authentication or ownership check on a route returning Personal Data

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L, score 7.9. model:User.username (Profile) has Public Exposure based on Evidence at server.ts:670; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L scores 7.9. Primary Provision Rule 6(1)(b) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Public; Evidence: server.ts:670–670

Primary Provision: DPDP-Rule-6(1)(b) — Rule 6(1)(b)

Other Provisions: CWE-639 — CWE-639, OWASP-API1-2023 — API1:2023, DPDP-Act-6(1) — Section 6(1), CWE-213 — CWE-213, OWASP-API3-2023 — API3:2023

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/memory.ts:24–24

```
    const memories = await MemoryModel.findAll({ include: [UserModel] })
```

server.ts:670–670

```
  app.get('/rest/memories', utils.asyncHandler(getMemories()))
```

models/user.ts:44–55

```
      username: {
        type: DataTypes.STRING,
        defaultValue: '',
        set (username: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            username = security.sanitizeLegacy(username)
          } else {
            username = security.sanitizeSecure(username)
          }
          this.setDataValue('username', username)
        }
      },
```

models/user.ts:56–69

```
      email: {
        type: DataTypes.STRING,
        unique: true,
        set (email: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            challengeUtils.solveIf(challenges.persistedXssUserChallenge, () => {
              return email?.includes('<iframe src="javascript:alert(`xss`)">') ?? false
            })
          } else {
            email = security.sanitizeSecure(email)
          }
          this.setDataValue('email', email)
…
```

models/user.ts:70–75

```
      «SECRET»
        type: DataTypes.STRING,
        set (clearTextPassword: string) {
          this.setDataValue('password', security.hash(clearTextPassword)) // vuln-code-snippet vuln-line weakPasswordChallenge
        }
      }, // vuln-code-snippet end weakPasswordChallenge
```

models/user.ts:97–100

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

models/user.ts:101–104

```
      lastLoginIp: {
        type: DataTypes.STRING,
        defaultValue: '0.0.0.0'
      },
```

models/user.ts:105–108

```
      profileImage: {
        type: DataTypes.STRING,
        defaultValue:«SECRET».svg'
      },
```

models/user.ts:109–112

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

Data Flow:

- None recorded.

Recommended fix: Require authentication on every route that returns Personal Data, and check on each request that the authenticated Data Principal owns the record or holds a role authorised for it. Do not let an identifier supplied in the path or body decide ownership. Apply the check to every method on the route, because Rule 6(1)(b) requires access to the resources holding Personal Data to be controlled. Tailored: not assessed

LLM triage: not assessed; cache key: 06d0b7dcb4cb545f26a85a9a86a9b7919c19ebcea9dadc40e0850476dc97913a

### SEC-08-a535cd15b04b — Over-exposed responses (whole model or nested records serialised)

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L, score 7.9. collection:reviewsCollection.author (Profile) has Public Exposure based on Evidence at server.ts:672; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L scores 7.9. Primary Provision Rule 6(1)(b) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Public; Evidence: server.ts:672–672

Primary Provision: DPDP-Rule-6(1)(b) — Rule 6(1)(b)

Other Provisions: DPDP-Act-6(1) — Section 6(1), CWE-213 — CWE-213, OWASP-API3-2023 — API3:2023

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/showProductReviews.ts:45–45

```
      res.json(utils.queryResultToJson(reviews))
```

server.ts:672–672

```
  app.get('/rest/products/:id/reviews', showProductReviews())
```

routes/createProductReviews.ts:26–26

```
        author: req.body.author,
```

Data Flow:

- Collect — frontend/src/app/product-details/product-details.component.ts:80–80; component; ts-join; inferred; Account email, or an anonymous fallback; model identity inferred from account response
- Collect — frontend/src/app/product-details/product-details.component.ts:91–91; component; ts-join; evidenced
- Collect — frontend/src/app/Services/product-review.service.ts:29–29; service; ts-join; evidenced
- Collect — server.ts:673–673; route; ts-join; evidenced; PUT /rest/products/:id/reviews
- Collect — routes/createProductReviews.ts:26–26; handler; ts-join; evidenced
- Store — routes/createProductReviews.ts:26–26; storage; ts-join; evidenced; insert into reviewsCollection
- Expose — routes/showProductReviews.ts:45–45; response; ts-join; evidenced; author not projected out; GET /rest/products/:id/reviews

Recommended fix: Serialise only the fields a response needs, using explicit allow-lists or response shapes rather than whole models or nested records. Remove Personal Data Elements the requester is not entitled to see, so each response stays within the Purpose for which the data was collected under §6(1). Apply the same field limits on every route that returns the same record, as Rule 6(1)(b) requires for access control. Tailored: not assessed

LLM triage: not assessed; cache key: a2bcf5d674f635a26899a39150b2abc8246f3e3f8d8507c08a933df068fd36e1

### SEC-11-ad5b2106f4e8 — Insecure transport, cookie flags or CORS wildcard on Personal Data routes

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L, score 7.9. model:User.username (Profile) has Public Exposure based on Evidence at server.ts:640; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L scores 7.9. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Public; Evidence: server.ts:640–640, server.ts:430–430, server.ts:440–451, server.ts:452–452, server.ts:453–453, server.ts:454–454, server.ts:540–546

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-319 — CWE-319, CWE-614 — CWE-614, CWE-942 — CWE-942

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

server.ts:185–185

```
  app.use(cors())
```

server.ts:640–640

```
  app.get('/rest/user/authentication-details', utils.asyncHandler(authenticatedUsers()))
```

server.ts:670–670

```
  app.get('/rest/memories', utils.asyncHandler(getMemories()))
```

server.ts:672–672

```
  app.get('/rest/products/:id/reviews', showProductReviews())
```

server.ts:430–430

```
  app.use('/rest/user/authentication-details', security.isAuthorized())
```

server.ts:440–451

```
  app.post('/api/Users', (req: Request, res: Response, next: NextFunction) => {
    if (req.body.email !== undefined && req.body.password !== undefined && req.body.passwordRepeat !== undefined) {
      if (req.body.email.length !== 0 && req.body.password.length !== 0) {
        req.body.email = req.body.email.trim()
        req.body.password = req.body.password.trim()
        req.body.passwordRepeat = req.body.passwordRepeat.trim()
      } else {
        res.status(400).send(res.__('Invalid email/password cannot be empty'))
      }
    }
    next()
  })
```

server.ts:452–452

```
  app.post('/api/Users', verify.registerAdminChallenge())
```

server.ts:453–453

```
  app.post('/api/Users', verify.passwordRepeatChallenge()) // vuln-code-snippet hide-end
```

server.ts:454–454

```
  app.post('/api/Users', verify.emptyUserRegistration())
```

server.ts:540–546

```
    const resource = finale.resource({
      model,
      endpoints: [`/api/${name}s`, `/api/${name}s/:id`],
      excludeAttributes: exclude,
      pagination: false,
      include
    })
```

Data Flow:

- None recorded.

Recommended fix: Serve every route that carries Personal Data over TLS only, and set Secure, HttpOnly and SameSite attributes on session cookies. Replace wildcard cross-origin rules with an explicit list of trusted origins. These transport and session controls are part of the safeguards Rule 6(1)(a) requires for the Personal Data they carry. Tailored: not assessed

LLM triage: not assessed; cache key: 7e11e87b1a870e44f1c616f5efa493e58d2640ffa2abfa88a8295e0e24c0574f

### SEC-01-d85a743d0415 — Personal Data written to logs

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 7.9. param:GET /rest/user/change-password?current (Authentication Secret) has Internal-Restricted Exposure based on Evidence at frontend/src/app/Services/user.service.ts:54; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 7.9. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: frontend/src/app/Services/user.service.ts:54–55, server.ts:370–370

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-532 — CWE-532, CWE-598 — CWE-598

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

frontend/src/app/Services/user.service.ts:54–55

```
    return this.http.get(this.hostServer + '/rest/user/change-password?current=' + passwords.current + '&new=' +
    passwords.new + '&repeat=' + passwords.repeat).pipe(map((response: any) => response.user), catchError((err) => { throw err.error }))
```

server.ts:370–370

```
  app.use(morgan('combined', { stream: accessLogStream }))
```

Data Flow:

- Collect — frontend/src/app/Services/user.service.ts:54–55; service; ts-join; evidenced; Query parameter appended to the request URL.
- Log — server.ts:370–370; log; config; evidenced; Morgan combined logs the request URL including its query; file pattern: logs/access.log.%DATE%; retention: 2 days.

Recommended fix: Keep Personal Data out of application, access and error logs. Write an opaque identifier or a masked form in place of each value, and strip request bodies and query strings before a log line is written. Where a value must be recorded, apply a protection that Rule 6(1)(a) names, such as encryption, obfuscation, masking or a virtual token. Apply the same rule to logging middleware and to any external log sink. Tailored: not assessed

LLM triage: not assessed; cache key: fb88f45f4822295d6f36f4f289b2d1e9bf748e1c0b5d41de8e7ce13962734677

### SEC-04-bebc3e7f55ae — Weak or missing password hashing

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 7.9. model:User.password (Authentication Secret) has Internal-Restricted Exposure based on Evidence at models/user.ts:70; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 7.9. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: models/user.ts:70–75, lib/insecurity.ts:41–41

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-916 — CWE-916

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

models/user.ts:70–75

```
      «SECRET»
        type: DataTypes.STRING,
        set (clearTextPassword: string) {
          this.setDataValue('password', security.hash(clearTextPassword)) // vuln-code-snippet vuln-line weakPasswordChallenge
        }
      }, // vuln-code-snippet end weakPasswordChallenge
```

lib/insecurity.ts:41–41

```
export const hash = (data: string) => crypto.createHash('md5').update(data).digest('hex')
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:28–29; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:99–99; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:70–75; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; password referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; password referenced in $VAR
- Expose — routes/authenticatedUsers.ts:14–31; response; semgrep:op-expose-response-json; evidenced; password referenced in $VAR
- Store — routes/changePassword.ts:51–51; model; semgrep:op-store-sequelize-update; evidenced; password referenced in $VAR
- Store — routes/resetPassword.ts:44–44; model; semgrep:op-store-sequelize-update; evidenced; password referenced in $VAR

Recommended fix: Store Authentication Secrets with a current, salted, deliberately slow password hashing function, never with a plain or fast unsalted digest. Re-hash each existing record with the new function the next time the Data Principal authenticates. Rule 6(1)(a) requires protection of the Personal Data these secrets guard, and a weak hash removes that protection once the store is read. Tailored: not assessed

LLM triage: not assessed; cache key: b0f84242fcd9123e2247cfb5c5daf48c29514c2d92adf609c43389ec01f8be7c

### SEC-05-c695dda06010 — Hard-coded secret or committed .env protecting Personal Data

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 7.9. protected Data Category Authentication Secret has Internal-Restricted Exposure based on Evidence at lib/insecurity.ts:21; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 7.9. Primary Provision Rule 6(1)(b) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: lib/insecurity.ts:21–21, lib/insecurity.ts:54–54

Primary Provision: DPDP-Rule-6(1)(b) — Rule 6(1)(b)

Other Provisions: CWE-798 — CWE-798

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

lib/insecurity.ts:21–21

```
[hard-coded signing material masked]
```

lib/insecurity.ts:54–54

```
export const authorize = (user = {}) => jwt.sign(user, privateKey, { expiresIn: '6h', algorithm: 'RS256' })
```

Data Flow:

- None recorded.

Recommended fix: Move credentials and keys that protect Personal Data out of source files and configuration into a secret store or the runtime environment. Rotate any value that has already been committed, and exclude .env and key files from version control and build context. Restrict the secret store to the identities that need it, as Rule 6(1)(b) requires for the systems that hold Personal Data. Tailored: not assessed

LLM triage: not assessed; cache key: b47dd25f565fe450e15e2be653162e5aaeab4a3c2cfc71a1a65513bc711aaf7d

### SEC-10-d70f56f17198 — Personal Data in localStorage, sessionStorage, cookies or outbound headers

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 7.9. storage:localStorage.token (Authentication Secret) has Internal-Restricted Exposure based on Evidence at frontend/src/app/login/login.component.ts:150; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 7.9. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: frontend/src/app/login/login.component.ts:150–150, frontend/src/app/oauth/oauth.component.ts:52–52, frontend/src/app/payment/payment.component.ts:233–233, frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:54–54, frontend/src/app/Services/request.interceptor.ts:16–16

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-922 — CWE-922

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

frontend/src/app/login/login.component.ts:150–150

```
    localStorage.setItem('token', authentication.token)
```

frontend/src/app/oauth/oauth.component.ts:52–52

```
        localStorage.setItem('token', authentication.token)
```

frontend/src/app/payment/payment.component.ts:233–233

```
          localStorage.setItem('token', data.token)
```

frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:54–54

```
        localStorage.setItem('token', authentication.token)
```

frontend/src/app/Services/request.interceptor.ts:16–16

```
          Authorization: `Bearer ${localStorage.getItem('token')}`
```

Data Flow:

- Store — frontend/src/app/login/login.component.ts:150–150; storage; semgrep:op-store-localstorage-set; evidenced; localStorage key token
- Store — frontend/src/app/oauth/oauth.component.ts:52–52; storage; semgrep:op-store-localstorage-set; evidenced; localStorage key token
- Store — frontend/src/app/payment/payment.component.ts:233–233; storage; semgrep:op-store-localstorage-set; evidenced; localStorage key token
- Store — frontend/src/app/two-factor-auth-enter/two-factor-auth-enter.component.ts:54–54; storage; semgrep:op-store-localstorage-set; evidenced; localStorage key token

Recommended fix: Do not write Personal Data or Authentication Secrets to localStorage, sessionStorage, cookies or outbound headers beyond what the session strictly needs. Keep identity in an opaque session identifier held server-side, and keep only non-Personal Data preferences in the browser. Where a value must be held client-side, protect it as Rule 6(1)(a) requires. Tailored: not assessed

LLM triage: not assessed; cache key: e2fdbc2769d3a837477c845efe6a42ecc948dc935a7e469a7556df7284577042

### SEC-10-d0971bb44714 — Personal Data in localStorage, sessionStorage, cookies or outbound headers

Severity: high; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 7.9. storage:localStorage.email (Contact) has Internal-Restricted Exposure based on Evidence at frontend/src/app/login/login.component.ts:106; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 7.9. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: frontend/src/app/login/login.component.ts:106–106, frontend/src/app/Services/request.interceptor.ts:23–23

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: CWE-922 — CWE-922

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

frontend/src/app/login/login.component.ts:106–106

```
        localStorage.setItem('email', user.email)
```

frontend/src/app/Services/request.interceptor.ts:23–23

```
          'X-User-Email': String(localStorage.getItem('email'))
```

Data Flow:

- Store — frontend/src/app/login/login.component.ts:106–106; storage; semgrep:op-store-localstorage-set; evidenced; localStorage key email

Recommended fix: Do not write Personal Data or Authentication Secrets to localStorage, sessionStorage, cookies or outbound headers beyond what the session strictly needs. Keep identity in an opaque session identifier held server-side, and keep only non-Personal Data preferences in the browser. Where a value must be held client-side, protect it as Rule 6(1)(a) requires. Tailored: not assessed

LLM triage: not assessed; cache key: 4e4fde50a6c15af2e7a1d17866b529515c468982b96d1b842e544de131ac7ac2

### SEC-08-177006878772 — Over-exposed responses (whole model or nested records serialised)

Severity: medium; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L, score 5.7. model:User.username (Profile) has Public Exposure based on Evidence at server.ts:640; CVSS CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:L scores 5.7. Primary Provision Rule 6(1)(b) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Public; Evidence: server.ts:640–640, server.ts:430–430, server.ts:440–451, server.ts:452–452, server.ts:453–453, server.ts:454–454, server.ts:540–546

Primary Provision: DPDP-Rule-6(1)(b) — Rule 6(1)(b)

Other Provisions: DPDP-Act-6(1) — Section 6(1), CWE-213 — CWE-213, OWASP-API3-2023 — API3:2023

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/authenticatedUsers.ts:12–12

```
    const users = await UserModel.findAll()
```

server.ts:640–640

```
  app.get('/rest/user/authentication-details', utils.asyncHandler(authenticatedUsers()))
```

models/user.ts:44–55

```
      username: {
        type: DataTypes.STRING,
        defaultValue: '',
        set (username: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            username = security.sanitizeLegacy(username)
          } else {
            username = security.sanitizeSecure(username)
          }
          this.setDataValue('username', username)
        }
      },
```

models/user.ts:56–69

```
      email: {
        type: DataTypes.STRING,
        unique: true,
        set (email: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            challengeUtils.solveIf(challenges.persistedXssUserChallenge, () => {
              return email?.includes('<iframe src="javascript:alert(`xss`)">') ?? false
            })
          } else {
            email = security.sanitizeSecure(email)
          }
          this.setDataValue('email', email)
…
```

models/user.ts:97–100

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

models/user.ts:101–104

```
      lastLoginIp: {
        type: DataTypes.STRING,
        defaultValue: '0.0.0.0'
      },
```

models/user.ts:105–108

```
      profileImage: {
        type: DataTypes.STRING,
        defaultValue:«SECRET».svg'
      },
```

server.ts:430–430

```
  app.use('/rest/user/authentication-details', security.isAuthorized())
```

server.ts:440–451

```
  app.post('/api/Users', (req: Request, res: Response, next: NextFunction) => {
    if (req.body.email !== undefined && req.body.password !== undefined && req.body.passwordRepeat !== undefined) {
      if (req.body.email.length !== 0 && req.body.password.length !== 0) {
        req.body.email = req.body.email.trim()
        req.body.password = req.body.password.trim()
        req.body.passwordRepeat = req.body.passwordRepeat.trim()
      } else {
        res.status(400).send(res.__('Invalid email/password cannot be empty'))
      }
    }
    next()
  })
```

server.ts:452–452

```
  app.post('/api/Users', verify.registerAdminChallenge())
```

server.ts:453–453

```
  app.post('/api/Users', verify.passwordRepeatChallenge()) // vuln-code-snippet hide-end
```

server.ts:454–454

```
  app.post('/api/Users', verify.emptyUserRegistration())
```

server.ts:540–546

```
    const resource = finale.resource({
      model,
      endpoints: [`/api/${name}s`, `/api/${name}s/:id`],
      excludeAttributes: exclude,
      pagination: false,
      include
    })
```

Data Flow:

- None recorded.

Recommended fix: Serialise only the fields a response needs, using explicit allow-lists or response shapes rather than whole models or nested records. Remove Personal Data Elements the requester is not entitled to see, so each response stays within the Purpose for which the data was collected under §6(1). Apply the same field limits on every route that returns the same record, as Rule 6(1)(b) requires for access control. Tailored: not assessed

LLM triage: not assessed; cache key: 63cb85dcdf0ec0c9247fd95986163d2099b087c2f5ed54c7f8742eecfefa4939

### TRF-02-56fc1119eb9b — Personal Data sent or stored outside India (disclosure, capped at Medium; Needs Legal Review unless the destination is restricted under §16)

Severity: medium; CVSS N/A (Disclosure Finding: processing presumed lawful, owed to the Data Principal); Risk Matrix cell medium (C, Cross-Border). model:User.email (Contact) has Cross-Border Exposure based on Evidence at terraform/variables.tf:1; Risk Matrix C/Cross-Border cell is medium, capped at medium for disclosure. Primary Provision Section 16(1) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Cross-Border; Evidence: terraform/variables.tf:1–5, terraform/main.tf:1–3, terraform/networking.tf:249–261

Primary Provision: DPDP-Act-16(1) — Section 16(1)

Other Provisions: DPDP-Rule-15 — Rule 15, DPDP-Rule-13(4) — Rule 13(4)

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-14.

Status: Needs Legal Review.

Legal reading — DPDP-Act-16(1) — Section 16(1): Transfer is lawful unless the destination is restricted by notification; this region is a deployment default, not evidence of deployed geography.

Legal reading — DPDP-Act-11(1)(b) — Section 11(1)(b): The Data Principal may be owed a summary of evidenced sharing; configured storage alone does not establish sharing.

Evidence:

terraform/variables.tf:1–5

```
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}
```

terraform/main.tf:1–3

```
provider "aws" {
  region = var.aws_region
}
```

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:16–17; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:98–98; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:56–69; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR

Recommended fix: Record the destination of each outbound transfer of Personal Data, and check it against any restriction the Central Government has notified under §16(1). Rule 15 governs data made available to foreign States, and Rule 13(4) applies where a Significant Data Fiduciary is involved. Send any flow whose destination is not restricted to legal review, and state the destination in the notice. Tailored: not assessed

LLM triage: not assessed; cache key: aa8d17bf032cfb34aaf8a3f52aa41b5889ba01e80069257df15dd3ff57c865cf

### SEC-02-03b1356ecc57 — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

Severity: medium; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 5.3. model:User.totpSecret (Authentication Secret) has Internal-Restricted Exposure based on Evidence at models/user.ts:109; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 5.3. The configured volume mount in terraform/main.tf:64 does not match SQLite storage at models/index.ts:42; volume encryption is not credited. The Personal Data Element remains without field-level protection. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: models/user.ts:109–112

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: ITAct-43A — Section 43A, CWE-311 — CWE-311

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

models/user.ts:109–112

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

terraform/main.tf:64–64

```
          containerPath = "/juice-shop/data/sqlite"
```

models/index.ts:42–42

```
    storage: options?.inMemory ? ':memory:' : 'data/juiceshop.sqlite',
```

Data Flow:

- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; totpSecret referenced in $VAR
- Expose — routes/authenticatedUsers.ts:14–31; response; semgrep:op-expose-response-json; evidenced; totpSecret referenced in $VAR

Recommended fix: Protect each Tier A and Tier B Personal Data Element at field or column level before it is stored, with keys held outside the data store, so that a database dump or a restored backup does not reveal the values. Disk or volume encryption protects only the storage medium, so it lowers severity without clearing the Finding. Until DPDP §44(2) omits IT Act §43A, that section's reasonable-security duty applies alongside Rule 6(1)(a). Tailored: not assessed

LLM triage: not assessed; cache key: e240a543418483de64606f5f98a34b595a6c88c54e06b4fd06147dd19245bfd0

### SEC-02-0f4631e6a05d — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

Severity: medium; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 5.3. model:User.deluxeToken (Authentication Secret) has Internal-Restricted Exposure based on Evidence at models/user.ts:97; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 5.3. The configured volume mount in terraform/main.tf:64 does not match SQLite storage at models/index.ts:42; volume encryption is not credited. The Personal Data Element remains without field-level protection. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: models/user.ts:97–100

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: ITAct-43A — Section 43A, CWE-311 — CWE-311

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

models/user.ts:97–100

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

terraform/main.tf:64–64

```
          containerPath = "/juice-shop/data/sqlite"
```

models/index.ts:42–42

```
    storage: options?.inMemory ? ':memory:' : 'data/juiceshop.sqlite',
```

Data Flow:

- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; deluxeToken referenced in $VAR
- Store — routes/deluxe.ts:43–43; model; semgrep:op-store-sequelize-update; evidenced; deluxeToken referenced in $VAR

Recommended fix: Protect each Tier A and Tier B Personal Data Element at field or column level before it is stored, with keys held outside the data store, so that a database dump or a restored backup does not reveal the values. Disk or volume encryption protects only the storage medium, so it lowers severity without clearing the Finding. Until DPDP §44(2) omits IT Act §43A, that section's reasonable-security duty applies alongside Rule 6(1)(a). Tailored: not assessed

LLM triage: not assessed; cache key: e240a543418483de64606f5f98a34b595a6c88c54e06b4fd06147dd19245bfd0

### SEC-02-b6efa0cd2309 — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

Severity: medium; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H, score 6.7. model:Card.cardNum (Financial) has Internal-Restricted Exposure based on Evidence at models/card.ts:38; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:H scores 6.7. The configured volume mount in terraform/main.tf:64 does not match SQLite storage at models/index.ts:42; volume encryption is not credited. The Personal Data Element remains without field-level protection. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: models/card.ts:38–45

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: ITAct-43A — Section 43A, CWE-311 — CWE-311

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

models/card.ts:38–45

```
      cardNum: {
        type: DataTypes.INTEGER,
        validate: {
          isInt: true,
          min: 1000000000000000,
          max: 9999999999999998
        }
      },
```

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

terraform/main.tf:64–64

```
          containerPath = "/juice-shop/data/sqlite"
```

models/index.ts:42–42

```
    storage: options?.inMemory ? ':memory:' : 'data/juiceshop.sqlite',
```

Data Flow:

- Collect — frontend/src/app/payment-method/payment-method.component.html:62–62; form; ts-join; evidenced
- Collect — frontend/src/app/payment-method/payment-method.component.ts:78–78; component; ts-join; evidenced
- Collect — frontend/src/app/Services/payment.service.ts:30–30; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Cards
- Collect — server.ts:470–470; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Cards
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/card.ts:38–45; model; ts-join; inferred; finale generated model write
- Expose — routes/payment.ts:32–32; response; ts-join; evidenced; masked
- Expose — routes/payment.ts:58–58; response; ts-join; evidenced; masked
- Store — data/datacreator.ts:271–277; model; semgrep:op-store-sequelize-create; evidenced; cardNum referenced in $VAR

Recommended fix: Protect each Tier A and Tier B Personal Data Element at field or column level before it is stored, with keys held outside the data store, so that a database dump or a restored backup does not reveal the values. Disk or volume encryption protects only the storage medium, so it lowers severity without clearing the Finding. Until DPDP §44(2) omits IT Act §43A, that section's reasonable-security duty applies alongside Rule 6(1)(a). Tailored: not assessed

LLM triage: not assessed; cache key: d9b5564d34156cb358434da96cce149cd1bd629aaaf5b8004e4bc08cb1b252d3

### SEC-02-e0994a7481e3 — Tier A/B Personal Data Elements without field-level protection at rest; disk- or volume-level encryption lowers severity, it does not clear the Finding

Severity: medium; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M, score 5.3. model:SecurityAnswer.answer (Authentication Secret) has Internal-Restricted Exposure based on Evidence at models/securityAnswer.ts:42; CVSS CVSS:4.0/AV:L/AC:L/AT:N/PR:H/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N/CR:M scores 5.3. The configured volume mount in terraform/main.tf:64 does not match SQLite storage at models/index.ts:42; volume encryption is not credited. The Personal Data Element remains without field-level protection. Primary Provision Rule 6(1)(a) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: models/securityAnswer.ts:42–47

Primary Provision: DPDP-Rule-6(1)(a) — Rule 6(1)(a)

Other Provisions: ITAct-43A — Section 43A, CWE-311 — CWE-311

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

models/securityAnswer.ts:42–47

```
      answer: {
        type: DataTypes.STRING,
        set (answer: string) {
          this.setDataValue('answer', security.hmac(answer))
        }
      }
```

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

terraform/main.tf:64–64

```
          containerPath = "/juice-shop/data/sqlite"
```

models/index.ts:42–42

```
    storage: options?.inMemory ? ':memory:' : 'data/juiceshop.sqlite',
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:93–95; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:109–109; component; ts-join; evidenced
- Collect — frontend/src/app/Services/security-answer.service.ts:21–21; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/SecurityAnswers
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/securityAnswer.ts:42–47; model; ts-join; inferred; finale generated model write
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:707–707; model; semgrep:op-store-sequelize-create; evidenced; answer referenced in $VAR
- Log — data/datacreator.ts:708–708; log; semgrep:op-log-logger; evidenced; answer referenced in $VAR

Recommended fix: Protect each Tier A and Tier B Personal Data Element at field or column level before it is stored, with keys held outside the data store, so that a database dump or a restored backup does not reveal the values. Disk or volume encryption protects only the storage medium, so it lowers severity without clearing the Finding. Until DPDP §44(2) omits IT Act §43A, that section's reasonable-security duty applies alongside Rule 6(1)(a). Tailored: not assessed

LLM triage: not assessed; cache key: 1d34d4b8a9f43e651935d3d99e15f287d7c4d4e3c2a9f31169ab5025a845f475

### SEC-13-394d3dbca514 — Logs of Personal Data processing kept under one year

Severity: medium; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell medium (B, Internal-Restricted). param:GET /rest/user/change-password?current (Authentication Secret) has Internal-Restricted Exposure based on Evidence at server.ts:362; Risk Matrix B/Internal-Restricted cell is medium. Primary Provision Rule 6(1)(e) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: server.ts:362–369

Primary Provision: DPDP-Rule-6(1)(e) — Rule 6(1)(e)

Other Provisions: DPDP-Rule-8(3) — Rule 8(3)

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

server.ts:362–369

```
  const accessLogStream = getStream({
    filename: path.resolve('logs/access.log.%DATE%'),
    date_format: 'YYYY-MM-DD',
    audit_file: 'logs/audit.json',
    frequency: 'daily',
    verbose: false,
    max_logs: '2d'
  })
```

frontend/src/app/Services/user.service.ts:54–55

```
    return this.http.get(this.hostServer + '/rest/user/change-password?current=' + passwords.current + '&new=' +
    passwords.new + '&repeat=' + passwords.repeat).pipe(map((response: any) => response.user), catchError((err) => { throw err.error }))
```

server.ts:370–370

```
  app.use(morgan('combined', { stream: accessLogStream }))
```

Data Flow:

- Collect — frontend/src/app/Services/user.service.ts:54–55; service; ts-join; evidenced; Query parameter appended to the request URL.
- Log — server.ts:370–370; log; config; evidenced; Morgan combined logs the request URL including its query; file pattern: logs/access.log.%DATE%; retention: 2 days.

Recommended fix: Keep access and processing logs for Personal Data for at least one year, as Rule 6(1)(e) and Rule 8(3) require, and set that period in the log store's own retention configuration. Where an erasure would remove records that these logs must keep, send the conflict to legal review rather than deleting the logs. Confirm the retention setting in deployment configuration as well as in application code. Tailored: not assessed

LLM triage: not assessed; cache key: 35e67a0287d7a55004d5c96758282978c2079ff775c4b5122f90dd0de5ca929b

### MON-01-8c5728dfea11 — No monitoring or review of access logs to detect unauthorised access

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:Address.fullName (Profile) has Internal-Restricted Exposure based on Evidence at monitoring/grafana-dashboard.json:121; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Rule 6(1)(c) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: monitoring/grafana-dashboard.json:121–121

Primary Provision: DPDP-Rule-6(1)(c) — Rule 6(1)(c)

Other Provisions: none

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

monitoring/grafana-dashboard.json:121–121

```
      "title": "Solved $difficulties Star Challenges",
```

Data Flow:

- Collect — frontend/src/app/address-create/address-create.component.html:14–14; form; ts-join; evidenced
- Collect — frontend/src/app/address-create/address-create.component.ts:91–91; component; ts-join; evidenced
- Collect — frontend/src/app/Services/address.service.ts:35–35; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; PUT /api/Addresss/:id
- Collect — server.ts:482–482; middleware; ts-join; evidenced; Explicit route before finale: PUT /api/Addresss/:id
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/address.ts:41–43; model; ts-join; inferred; finale generated model write
- Expose — routes/address.ts:12–12; response; ts-join; evidenced
- Expose — routes/address.ts:20–20; response; ts-join; evidenced
- Collect — frontend/src/app/Services/address.service.ts:30–30; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Addresss
- Collect — server.ts:480–480; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Addresss
- Store — data/datacreator.ts:253–262; model; semgrep:op-store-sequelize-create; evidenced; fullName referenced in $VAR

Recommended fix: Set up alerting or scheduled review on the access logs and authentication events for every store that holds Personal Data, so unauthorised access is detected and its cause and impact can be established. Rule 6(1)(c) requires monitoring and review of this kind, and investigation depends on it. Make sure the alert rules cover authentication failures and privileged reads, not only application errors. Tailored: not assessed

LLM triage: not assessed; cache key: 090328308fd397a9e287d197691d5218fb2cfd41a52fdc0cc2f8d03867de6b06

### SEC-14-c5e9ac6a126d — No backup for Personal Data stores

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:Address.fullName (Profile) has Internal-Restricted Exposure based on Evidence at terraform/networking.tf:249; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Rule 6(1)(d) has Penalty Ceiling ₹250 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: terraform/networking.tf:249–261

Primary Provision: DPDP-Rule-6(1)(d) — Rule 6(1)(d)

Other Provisions: none

Penalty Ceiling: ₹250 crore (DPDP-Act-8(5)); Enforceable From: 2027-05-14.

Status: open.

Evidence:

terraform/networking.tf:249–261

```
resource "aws_efs_file_system" "juice_shop_data" {
  «SECRET»
  encrypted      = var.efs_encrypted

  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"

  tags = {
    Name        = "${var.project_name}-sqlite-data"
    Project     = var.project_name
    Environment = var.environment
  }
…
```

terraform/main.tf:35–97

```
resource "aws_ecs_task_definition" "juice_shop" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn

  container_definitions = jsonencode([
    {
      name      = var.project_name
      image     = "${var.ecr_repository_url}:${var.container_tag}"
…
```

models/address.ts:41–43

```
      fullName: {
        type: DataTypes.STRING
      },
```

Data Flow:

- Collect — frontend/src/app/address-create/address-create.component.html:14–14; form; ts-join; evidenced
- Collect — frontend/src/app/address-create/address-create.component.ts:91–91; component; ts-join; evidenced
- Collect — frontend/src/app/Services/address.service.ts:35–35; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; PUT /api/Addresss/:id
- Collect — server.ts:482–482; middleware; ts-join; evidenced; Explicit route before finale: PUT /api/Addresss/:id
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/address.ts:41–43; model; ts-join; inferred; finale generated model write
- Expose — routes/address.ts:12–12; response; ts-join; evidenced
- Expose — routes/address.ts:20–20; response; ts-join; evidenced
- Collect — frontend/src/app/Services/address.service.ts:30–30; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Addresss
- Collect — server.ts:480–480; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Addresss
- Store — data/datacreator.ts:253–262; model; semgrep:op-store-sequelize-create; evidenced; fullName referenced in $VAR

Recommended fix: Back up every persistent store that holds Personal Data on a schedule, with encrypted copies held apart from the primary store. Test restoration before relying on the backups, and record the recovery point and recovery time each store must meet. Rule 6(1)(d) requires appropriate measures to continue processing if the data is compromised, and tested backups are the usual means of meeting it. Tailored: not assessed

LLM triage: not assessed; cache key: 44617509f5746ed42e1b16231e9d01cf027e1719df44d37c40b5c4e8d47740bb

### RET-02-4696497b9137 — Erasure request that does not erase (flag only, soft delete, Elements or Data Processors skipped)

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:User.email (Contact) has Internal-Restricted Exposure based on Evidence at routes/dataErasure.ts:85; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 12(3) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: routes/dataErasure.ts:85–85

Primary Provision: DPDP-Act-12(3) — Section 12(3)

Other Provisions: DPDP-Act-8(7) — Section 8(7), DPDP-Act-8(7)(b) — Section 8(7)(b)

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/dataErasure.ts:85–85

```
        deletionRequested: true
```

routes/dataErasure.ts:74–132

```
router.post('/', (req: Request<Record<string, unknown>, Record<string, unknown>, DataErasureRequestParams>, res: Response, next: NextFunction): void => {
  void (async () => {
    const loggedInUser = security.authenticatedUsers.get(req.cookies.token)
    if (!loggedInUser) {
      next(new Error('Blocked illegal activity by ' + req.socket.remoteAddress))
      return
    }

    try {
      await PrivacyRequestModel.create({
        UserId: loggedInUser.data.id,
        deletionRequested: true
…
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:16–17; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:98–98; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:56–69; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR

Recommended fix: Make the erasure route delete the Personal Data Elements from every store, cache and backup in scope, rather than setting a flag or hiding the records. Include the Data Processors in each erasure request, as §8(7)(b) requires, and confirm completion for each one. Keep only what a legal retention duty obliges you to keep, and erase the rest on request under §12(3). Tailored: not assessed

LLM triage: not assessed; cache key: 836f47fc3625284c62e3a4a6d363cfab60e68688aab09c4abd16d72c8ea83c99

### RET-03-41bffe4101f9 — No 48-hour notice before erasure

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:User.email (Contact) has Internal-Restricted Exposure based on Evidence at routes/dataErasure.ts:74; Risk Matrix C/Internal-Restricted cell is low. Applicable only if the Data Fiduciary is a Third Schedule class. Primary Provision Rule 8(2) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: routes/dataErasure.ts:74–132

Primary Provision: DPDP-Rule-8(2) — Rule 8(2)

Other Provisions: DPDP-Rule-8(1) — Rule 8(1), DPDP-Rules-Schedule-Third — Third Schedule

Penalty Ceiling: ₹50 crore (DPDP-Act-8(7)); Enforceable From: 2027-05-14.

Status: conditional.

Evidence:

routes/dataErasure.ts:74–132

```
router.post('/', (req: Request<Record<string, unknown>, Record<string, unknown>, DataErasureRequestParams>, res: Response, next: NextFunction): void => {
  void (async () => {
    const loggedInUser = security.authenticatedUsers.get(req.cookies.token)
    if (!loggedInUser) {
      next(new Error('Blocked illegal activity by ' + req.socket.remoteAddress))
      return
    }

    try {
      await PrivacyRequestModel.create({
        UserId: loggedInUser.data.id,
        deletionRequested: true
…
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:16–17; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:98–98; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:56–69; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR

Recommended fix: For a Third Schedule class, send the Data Principal a notice at least 48 hours before erasure under Rule 8(2), telling them the erasure is due and how to stop it. Build the notice into the erasure job so that it always runs ahead of deletion and cannot be skipped. Apply the requirement only where the Third Schedule class condition is met, not by default. Tailored: not assessed

LLM triage: not assessed; cache key: f290c4eb3a1c9739ca3f78901f9f08ec85c01a7023c0330b922cf414e96a0b60

### RIG-01-a9383e4db278 — Access summary missing, or omitting Personal Data Elements the app processes for that Data Principal; omitting the Data Fiduciaries and Data Processors it shared data with counts only where a sharing flow is evidenced

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:User.email (Contact) has Internal-Restricted Exposure based on Evidence at routes/dataExport.ts:15; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 11(1)(a) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: routes/dataExport.ts:15–116

Primary Provision: DPDP-Act-11(1)(a) — Section 11(1)(a)

Other Provisions: DPDP-Act-11(1)(b) — Section 11(1)(b), DPDP-Rule-14 — Rule 14

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/dataExport.ts:15–116

```
export function dataExport () {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const loggedInUser = security.authenticatedUsers.get(req.headers?.authorization?.replace('Bearer ', ''))
      if (loggedInUser?.data?.email && loggedInUser.data.id) {
        const username = loggedInUser.data.username
        const email = loggedInUser.data.email
        const updatedEmail = email.replace(/[aeiou]/gi, '*')

        let memories, orders, reviews
        try {
          memories = await MemoryModel.findAll({ where: { UserId: req.body.UserId } })
…
```

server.ts:660–660

```
  app.post('/rest/user/data-export', security.appendUserId(), utils.asyncHandler(dataExport()))
```

models/card.ts:37–37

```
      fullName: DataTypes.STRING,
```

models/card.ts:38–45

```
      cardNum: {
        type: DataTypes.INTEGER,
        validate: {
          isInt: true,
          min: 1000000000000000,
          max: 9999999999999998
        }
      },
```

models/card.ts:46–53

```
      expMonth: {
        type: DataTypes.INTEGER,
        validate: {
          isInt: true,
          min: 1,
          max: 12
        }
      },
```

models/card.ts:54–61

```
      expYear: {
        type: DataTypes.INTEGER,
        validate: {
          isInt: true,
          min: 2080,
          max: 2099
        }
      }
```

models/recycle.ts:33–35

```
      AddressId: {
        type: DataTypes.INTEGER
      },
```

models/securityAnswer.ts:42–47

```
      answer: {
        type: DataTypes.STRING,
        set (answer: string) {
          this.setDataValue('answer', security.hmac(answer))
        }
      }
```

models/user.ts:70–75

```
      «SECRET»
        type: DataTypes.STRING,
        set (clearTextPassword: string) {
          this.setDataValue('password', security.hash(clearTextPassword)) // vuln-code-snippet vuln-line weakPasswordChallenge
        }
      }, // vuln-code-snippet end weakPasswordChallenge
```

models/user.ts:97–100

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

models/user.ts:101–104

```
      lastLoginIp: {
        type: DataTypes.STRING,
        defaultValue: '0.0.0.0'
      },
```

models/user.ts:105–108

```
      profileImage: {
        type: DataTypes.STRING,
        defaultValue:«SECRET».svg'
      },
```

models/user.ts:109–112

```
      «SECRET»
        type: DataTypes.STRING,
        defaultValue: ''
      },
```

models/wallet.ts:35–41

```
      balance: {
        type: DataTypes.INTEGER,
        validate: {
          isInt: true
        },
        defaultValue: 0
      }
```

models/user.ts:56–69

```
      email: {
        type: DataTypes.STRING,
        unique: true,
        set (email: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            challengeUtils.solveIf(challenges.persistedXssUserChallenge, () => {
              return email?.includes('<iframe src="javascript:alert(`xss`)">') ?? false
            })
          } else {
            email = security.sanitizeSecure(email)
          }
          this.setDataValue('email', email)
…
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:16–17; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:98–98; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:56–69; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR

Recommended fix: Give each Data Principal a summary of the Personal Data Elements held about them and of the processing done on that data, as §11(1)(a) requires. Where a sharing flow exists, list the Data Fiduciaries and Data Processors the data was shared with and what was shared, under §11(1)(b). Serve the summary through an in-app or request route that Rule 14 describes. Tailored: not assessed

LLM triage: not assessed; cache key: cc5f460988a2bd82cea055003b2ebe6ca2a350283c563893b0de4386f466d71b

### RIG-02-f7117cbcde8b — No route to correct, complete or update Personal Data Elements

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). model:User.email (Contact) has Internal-Restricted Exposure based on Evidence at routes/updateUserProfile.ts:15; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 12(2) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: routes/updateUserProfile.ts:15–49

Primary Provision: DPDP-Act-12(2) — Section 12(2)

Other Provisions: DPDP-Rule-14 — Rule 14

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-14.

Status: open.

Evidence:

routes/updateUserProfile.ts:15–49

```
export function updateUserProfile () {
  return async (req: Request, res: Response, next: NextFunction) => {
    const loggedInUser = security.authenticatedUsers.get(req.cookies.token)

    if (!loggedInUser) {
      next(new Error('Blocked illegal activity by ' + req.socket.remoteAddress))
      return
    }

    try {
      const user = await UserModel.findByPk(loggedInUser.data.id)
      if (!user) {
…
```

server.ts:707–707

```
  app.post('/profile', utils.asyncHandler(updateUserProfile()))
```

models/user.ts:56–69

```
      email: {
        type: DataTypes.STRING,
        unique: true,
        set (email: string) {
          if (utils.isChallengeEnabled(challenges.persistedXssUserChallenge)) {
            challengeUtils.solveIf(challenges.persistedXssUserChallenge, () => {
              return email?.includes('<iframe src="javascript:alert(`xss`)">') ?? false
            })
          } else {
            email = security.sanitizeSecure(email)
          }
          this.setDataValue('email', email)
…
```

server.ts:396–398

```
  app.route('/api/Users/:id')
    .get(security.isAuthorized())
    .put(security.denyAll())
```

server.ts:342–342

```
  app.post('/profile/image/file', uploadToMemory.single('file'), ensureFileIsPassed, metrics.observeFileUploadMetricsMiddleware(), utils.asyncHandler(profileImageFileUpload()))
```

server.ts:418–418

```
  app.post('/api/Recycles', security.isAuthorized())
```

server.ts:470–470

```
  app.post('/api/Cards', security.appendUserId())
```

server.ts:480–480

```
  app.post('/api/Addresss', security.appendUserId())
```

server.ts:482–482

```
  app.put('/api/Addresss/:id', security.appendUserId())
```

server.ts:636–636

```
  app.get('/rest/user/change-password', utils.asyncHandler(changePassword()))
```

server.ts:637–637

```
  app.post('/rest/user/reset-password', utils.asyncHandler(resetPassword()))
```

Data Flow:

- Collect — frontend/src/app/register/register.component.html:16–17; form; ts-join; evidenced
- Collect — frontend/src/app/register/register.component.ts:98–98; component; ts-join; evidenced
- Collect — frontend/src/app/Services/user.service.ts:38–38; service; ts-join; evidenced
- Collect — server.ts:540–546; route; ts-join; inferred; POST /api/Users
- Collect — server.ts:440–451; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:452–452; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:453–453; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:454–454; middleware; ts-join; evidenced; Explicit route before finale: POST /api/Users
- Collect — server.ts:540–546; handler; ts-join; inferred; finale generated handler
- Store — models/user.ts:56–69; model; ts-join; inferred; finale generated model write
- Expose — routes/changePassword.ts:56–56; response; ts-join; evidenced
- Expose — routes/saveLoginIp.ts:33–33; response; ts-join; evidenced
- Expose — server.ts:625–631; response; ts-join; inferred; finale generated read response wrapper
- Store — data/datacreator.ts:192–201; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR
- Store — data/datacreator.ts:326–329; model; semgrep:op-store-sequelize-create; evidenced; email referenced in $VAR

Recommended fix: Give each Data Principal a route to correct, complete or update every user-editable Personal Data Element, and apply the change in every store the value lives in, including caches and derived records. §12(2) provides the right to correction, completion and update, and Rule 14 sets how the Data Principal exercises it. Tailored: not assessed

LLM triage: not assessed; cache key: 20bbfd5b9f35a810b4b87e92748ecf598a6206c3900026c4f1d72d382e8fd193

### Observations

No Observations.

## Consent Assessment

### recorded

Applicability: not applicable — The static inventory identifies a banner but no consent grant or Consent Record. Assessment: Not met by the identified banner: no Consent Record was established. A dismiss action is not a consent grant; no grant was established either.

Issue Types: CON-06

Linked identifiers: none

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### specific

Applicability: not determinable — No controls established by the static inventory; applicability is not established. The identified banner is not a grant. Assessment: Not determinable: a consent control or multiple Purposes not established by the static inventory.

Issue Types: CON-02, CON-03

Linked identifiers: none

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### enforced server-side

Applicability: not determinable — No purposes established by the static inventory; applicability is not established. The identified banner is not a grant. Assessment: Not determinable: a Purpose linked to a Processing Operation and its lawful basis not established by the static inventory.

Issue Types: CON-01

Linked identifiers: none

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### withdrawable with comparable ease

Applicability: not applicable — The static inventory identifies no consent grant; this is limited to the inspected inventory. Assessment: Not assessed; an inapplicable Gate is not a compliance conclusion.

Issue Types: CON-04

Linked identifiers: none

Static step counts: {   "grant": [],   "withdrawal": [] }

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### propagated to Data Processors

Applicability: not applicable — The static inventory identifies no Data Processor receiving Personal Data; this is limited to the inspected inventory. Assessment: Not assessed; an inapplicable Gate is not a compliance conclusion.

Issue Types: CON-05

Linked identifiers: none

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### preceded by notice

Applicability: not determinable — No controls established by the static inventory; applicability is not established. The identified banner is not a grant. Assessment: Not determinable: a consent request linked to notice contents and language options not established by the static inventory.

Issue Types: CON-07

Linked identifiers: notice:frontend/src/app/privacy-policy/privacy-policy.component.html:18, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:24, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:98, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:100, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:137, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:140, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:147, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:155, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:157, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:160, notice:frontend/src/app/privacy-policy/privacy-policy.component.html:165, notice:views/dataErasureForm.hbs:32

frontend/src/app/privacy-policy/privacy-policy.component.html:18–22

```
      <p>This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use
        our Service and the choices you have associated with that data. Our Privacy Policy for {{applicationName}} is
        created with the help of the <a href="https://www.freeprivacypolicy.com/"
                                        aria-label="Link to the page where the privacy policy was created">Free Privacy
          Policy website</a>.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:24–26

```
      <p>We use your data to provide and improve the Service. By using the Service, you agree to the collection and use of
        information in accordance with this policy. Unless otherwise defined in this Privacy Policy, terms used in this
        Privacy Policy have the same meanings as in our Terms and Conditions, accessible from {{applicationUrl}} .</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:98–99

```
      <p>Your consent to this Privacy Policy followed by your submission of such information represents your agreement to
        that transfer.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:100–104

```
      <p>{{applicationName}} will take all steps <span class="hot">reasonably necessary</span> to ensure that your data is
        treated securely and in
        accordance with this Privacy Policy and no transfer of your Personal Data will take place to an organization or a
        country unless there are adequate controls in place including the security of your data and other personal
        information.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:137–139

```
      <p>Our Service may contain links to other sites that are not operated by us. If you click on a third party link, you
        will be directed to that third party's site. We strongly advise you to review the Privacy Policy of every site you
        visit.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:140–142

```
      <p>We have no control over and assume no <span class="hot">responsibility</span> for the content, privacy policies
        or practices of any third
        party sites or services.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:147–151

```
      <p>We do not knowingly collect personally identifiable information from anyone under the age of 18. If you are a
        parent or guardian and you are aware that your Children has provided us with Personal Data, please contact us. If
        we
        become aware that we have collected Personal Data from children without verification of parental consent, we take
        steps to remove that information from our servers.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:155–156

```
      <p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy
        Policy on this page.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:157–159

```
      <p>We will let you know via email and/or a prominent notice on our Service, prior to the change becoming effective
        and
        update the "effective date" at the top of this Privacy Policy.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:160–161

```
      <p>You are advised to review this Privacy Policy periodically for any changes. Changes to this Privacy Policy are
        effective when they are posted on this page.</p>
```

frontend/src/app/privacy-policy/privacy-policy.component.html:165–165

```
      <p>If you have any questions about this Privacy Policy, please contact us:</p>
```

views/dataErasureForm.hbs:32–33

```
        <p>We take data security, customer privacy, and legal compliance very serious. In accordance with GDPR we allow
            you to request complete erasure of your account and any associated data.</p>
```

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

### verifiable parental consent

Applicability: not applicable — The static inventory identifies no age/DOB collection or explicit Child audience; this is limited to the inspected inventory. Assessment: Not assessed; an inapplicable Gate is not a compliance conclusion.

Issue Types: CHI-01

Linked identifiers: none

frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

Banner Evidence (not a grant): frontend/src/index.html:19–19

```
      window.cookieconsent.initialise({
```

LLM reasoning: not assessed; cache key: e4f4742e2b3aec416bfa3124896c40219ba704313596afb3b90eb207e7550c9e

Limitation: Only statically resolved Purpose-specific links are represented; missing links are not proof of absence.

Limitation: Step counts require a common, statically resolved starting template; credentials and text entry are not counted.

Limitation: A dispatched deletion, browser choice, or Data Processor call does not establish actual deletion or a contract.

## Coverage Matrix

| Provision | Citation | Classification | Covering Rules |
| --- | --- | --- | --- |
| DPDP-Act-1 | Section 1 | not code-checkable | none |
| DPDP-Act-1(1) | Section 1(1) | not code-checkable | none |
| DPDP-Act-1(2) | Section 1(2) | not code-checkable | none |
| DPDP-Act-2 | Section 2 | not code-checkable | none |
| DPDP-Act-2(f) | Section 2(f) | not code-checkable | none |
| DPDP-Act-2(i) | Section 2(i) | not code-checkable | none |
| DPDP-Act-2(j) | Section 2(j) | not code-checkable | none |
| DPDP-Act-2(k) | Section 2(k) | not code-checkable | none |
| DPDP-Act-2(t) | Section 2(t) | not code-checkable | none |
| DPDP-Act-2(za) | Section 2(za) | not code-checkable | none |
| DPDP-Act-3 | Section 3 | not code-checkable | none |
| DPDP-Act-4 | Section 4 | not determinable | CON-01-express-enforcement |
| DPDP-Act-4(1) | Section 4(1) | not determinable | CON-01-express-enforcement |
| DPDP-Act-4(2) | Section 4(2) | not code-checkable | none |
| DPDP-Act-5 | Section 5 | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-5(1) | Section 5(1) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-5(2) | Section 5(2) | not code-checkable | none |
| DPDP-Act-5(3) | Section 5(3) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-6 | Section 6 | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-05-express-processor-withdrawal, CON-06-django-incomplete-record, CON-06-sequelize-consent-record, CON-07-angular-consent-notice, CON-07-django-unitemised-notice, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author |
| DPDP-Act-6(1) | Section 6(1) | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author |
| DPDP-Act-6(2) | Section 6(2) | not code-checkable | none |
| DPDP-Act-6(3) | Section 6(3) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Act-6(4) | Section 6(4) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Act-6(5) | Section 6(5) | not code-checkable | none |
| DPDP-Act-6(6) | Section 6(6) | not determinable | CON-05-express-processor-withdrawal |
| DPDP-Act-6(7) | Section 6(7) | not code-checkable | none |
| DPDP-Act-6(8) | Section 6(8) | not code-checkable | none |
| DPDP-Act-6(9) | Section 6(9) | not code-checkable | none |
| DPDP-Act-6(10) | Section 6(10) | not determinable | CON-06-django-incomplete-record, CON-06-sequelize-consent-record |
| DPDP-Act-7 | Section 7 | not determinable | CON-01-express-enforcement |
| DPDP-Act-8 | Section 8 | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-02-express-erasure-request, RIG-03-express-grievance, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(1) | Section 8(1) | not code-checkable | none |
| DPDP-Act-8(2) | Section 8(2) | not code-checkable | TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(3) | Section 8(3) | not code-checkable | none |
| DPDP-Act-8(3)(a) | Section 8(3)(a) | not code-checkable | none |
| DPDP-Act-8(3)(b) | Section 8(3)(b) | not code-checkable | none |
| DPDP-Act-8(4) | Section 8(4) | not code-checkable | none |
| DPDP-Act-8(5) | Section 8(5) | not code-checkable | none |
| DPDP-Act-8(6) | Section 8(6) | not code-checkable | none |
| DPDP-Act-8(7) | Section 8(7) | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-02-express-erasure-request |
| DPDP-Act-8(7)(a) | Section 8(7)(a) | not determinable | RET-01-express-purpose-end |
| DPDP-Act-8(7)(b) | Section 8(7)(b) | not determinable | CON-05-express-processor-withdrawal, RET-02-express-erasure-request |
| DPDP-Act-8(8) | Section 8(8) | not code-checkable | none |
| DPDP-Act-8(8)(a) | Section 8(8)(a) | not code-checkable | none |
| DPDP-Act-8(8)(b) | Section 8(8)(b) | not code-checkable | none |
| DPDP-Act-8(9) | Section 8(9) | not determinable | RIG-03-express-grievance |
| DPDP-Act-8(10) | Section 8(10) | not determinable | RIG-03-express-grievance |
| DPDP-Act-8(11) | Section 8(11) | not code-checkable | none |
| DPDP-Act-9 | Section 9 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent, CHI-02-child-tracking |
| DPDP-Act-9(1) | Section 9(1) | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Act-9(2) | Section 9(2) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-9(3) | Section 9(3) | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Act-9(4) | Section 9(4) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-9(5) | Section 9(5) | not code-checkable; covered, not exercised on a real Target | none |
| DPDP-Act-10 | Section 10 | not code-checkable | none |
| DPDP-Act-10(1) | Section 10(1) | not code-checkable | none |
| DPDP-Act-10(2) | Section 10(2) | not code-checkable | none |
| DPDP-Act-11 | Section 11 | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1) | Section 11(1) | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1)(a) | Section 11(1)(a) | static | RIG-01-express-incomplete-export |
| DPDP-Act-11(1)(b) | Section 11(1)(b) | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1)(c) | Section 11(1)(c) | not code-checkable | none |
| DPDP-Act-11(2) | Section 11(2) | not code-checkable | none |
| DPDP-Act-12 | Section 12 | static | RET-02-express-erasure-request, RIG-02-express-email-correction |
| DPDP-Act-12(1) | Section 12(1) | not code-checkable | none |
| DPDP-Act-12(2) | Section 12(2) | static | RIG-02-express-email-correction |
| DPDP-Act-12(2)(a) | Section 12(2)(a) | not code-checkable | none |
| DPDP-Act-12(2)(b) | Section 12(2)(b) | not code-checkable | none |
| DPDP-Act-12(2)(c) | Section 12(2)(c) | not code-checkable | none |
| DPDP-Act-12(3) | Section 12(3) | static | RET-02-express-erasure-request |
| DPDP-Act-13 | Section 13 | not determinable | RIG-03-express-grievance |
| DPDP-Act-13(1) | Section 13(1) | not code-checkable | none |
| DPDP-Act-13(2) | Section 13(2) | not code-checkable | none |
| DPDP-Act-13(3) | Section 13(3) | not code-checkable | none |
| DPDP-Act-14 | Section 14 | not determinable | RIG-04-rights-notice |
| DPDP-Act-14(1) | Section 14(1) | not code-checkable | none |
| DPDP-Act-14(2) | Section 14(2) | not code-checkable | none |
| DPDP-Act-15 | Section 15 | not code-checkable | none |
| DPDP-Act-16 | Section 16 | static | TRF-02-terraform-storage-region |
| DPDP-Act-16(1) | Section 16(1) | static | TRF-02-terraform-storage-region |
| DPDP-Act-16(2) | Section 16(2) | not code-checkable | none |
| DPDP-Act-17 | Section 17 | not code-checkable | none |
| DPDP-Act-17(1) | Section 17(1) | not code-checkable | none |
| DPDP-Act-17(2) | Section 17(2) | not code-checkable | none |
| DPDP-Act-17(3) | Section 17(3) | not code-checkable | none |
| DPDP-Act-17(4) | Section 17(4) | not code-checkable | none |
| DPDP-Act-17(5) | Section 17(5) | not code-checkable | none |
| DPDP-Act-18 | Section 18 | not code-checkable | none |
| DPDP-Act-18(1) | Section 18(1) | not code-checkable | none |
| DPDP-Act-18(2) | Section 18(2) | not code-checkable | none |
| DPDP-Act-18(3) | Section 18(3) | not code-checkable | none |
| DPDP-Act-19 | Section 19 | not code-checkable | none |
| DPDP-Act-19(1) | Section 19(1) | not code-checkable | none |
| DPDP-Act-19(2) | Section 19(2) | not code-checkable | none |
| DPDP-Act-19(3) | Section 19(3) | not code-checkable | none |
| DPDP-Act-20 | Section 20 | not code-checkable | none |
| DPDP-Act-20(1) | Section 20(1) | not code-checkable | none |
| DPDP-Act-20(2) | Section 20(2) | not code-checkable | none |
| DPDP-Act-21 | Section 21 | not code-checkable | none |
| DPDP-Act-21(1) | Section 21(1) | not code-checkable | none |
| DPDP-Act-21(2) | Section 21(2) | not code-checkable | none |
| DPDP-Act-22 | Section 22 | not code-checkable | none |
| DPDP-Act-22(1) | Section 22(1) | not code-checkable | none |
| DPDP-Act-22(2) | Section 22(2) | not code-checkable | none |
| DPDP-Act-22(3) | Section 22(3) | not code-checkable | none |
| DPDP-Act-23 | Section 23 | not code-checkable | none |
| DPDP-Act-23(1) | Section 23(1) | not code-checkable | none |
| DPDP-Act-23(2) | Section 23(2) | not code-checkable | none |
| DPDP-Act-23(3) | Section 23(3) | not code-checkable | none |
| DPDP-Act-24 | Section 24 | not code-checkable | none |
| DPDP-Act-25 | Section 25 | not code-checkable | none |
| DPDP-Act-26 | Section 26 | not code-checkable | none |
| DPDP-Act-27 | Section 27 | not code-checkable | none |
| DPDP-Act-27(1) | Section 27(1) | not code-checkable | none |
| DPDP-Act-27(1)(d) | Section 27(1)(d) | not code-checkable | none |
| DPDP-Act-27(2) | Section 27(2) | not code-checkable | none |
| DPDP-Act-27(3) | Section 27(3) | not code-checkable | none |
| DPDP-Act-28 | Section 28 | not code-checkable | none |
| DPDP-Act-28(1) | Section 28(1) | not code-checkable | none |
| DPDP-Act-28(2) | Section 28(2) | not code-checkable | none |
| DPDP-Act-28(3) | Section 28(3) | not code-checkable | none |
| DPDP-Act-28(4) | Section 28(4) | not code-checkable | none |
| DPDP-Act-28(5) | Section 28(5) | not code-checkable | none |
| DPDP-Act-28(6) | Section 28(6) | not code-checkable | none |
| DPDP-Act-28(7) | Section 28(7) | not code-checkable | none |
| DPDP-Act-28(8) | Section 28(8) | not code-checkable | none |
| DPDP-Act-28(9) | Section 28(9) | not code-checkable | none |
| DPDP-Act-28(10) | Section 28(10) | not code-checkable | none |
| DPDP-Act-28(11) | Section 28(11) | not code-checkable | none |
| DPDP-Act-28(12) | Section 28(12) | not code-checkable | none |
| DPDP-Act-29 | Section 29 | not code-checkable | none |
| DPDP-Act-29(1) | Section 29(1) | not code-checkable | none |
| DPDP-Act-29(2) | Section 29(2) | not code-checkable | none |
| DPDP-Act-29(3) | Section 29(3) | not code-checkable | none |
| DPDP-Act-29(4) | Section 29(4) | not code-checkable | none |
| DPDP-Act-29(5) | Section 29(5) | not code-checkable | none |
| DPDP-Act-29(6) | Section 29(6) | not code-checkable | none |
| DPDP-Act-29(7) | Section 29(7) | not code-checkable | none |
| DPDP-Act-29(8) | Section 29(8) | not code-checkable | none |
| DPDP-Act-29(9) | Section 29(9) | not code-checkable | none |
| DPDP-Act-29(10) | Section 29(10) | not code-checkable | none |
| DPDP-Act-30 | Section 30 | not code-checkable | none |
| DPDP-Act-30(1) | Section 30(1) | not code-checkable | none |
| DPDP-Act-30(2) | Section 30(2) | not code-checkable | none |
| DPDP-Act-31 | Section 31 | not code-checkable | none |
| DPDP-Act-32 | Section 32 | not code-checkable | none |
| DPDP-Act-32(1) | Section 32(1) | not code-checkable | none |
| DPDP-Act-32(2) | Section 32(2) | not code-checkable | none |
| DPDP-Act-32(3) | Section 32(3) | not code-checkable | none |
| DPDP-Act-32(4) | Section 32(4) | not code-checkable | none |
| DPDP-Act-32(5) | Section 32(5) | not code-checkable | none |
| DPDP-Act-33 | Section 33 | not code-checkable | none |
| DPDP-Act-33(1) | Section 33(1) | not code-checkable | none |
| DPDP-Act-33(2) | Section 33(2) | not code-checkable | none |
| DPDP-Act-34 | Section 34 | not code-checkable | none |
| DPDP-Act-35 | Section 35 | not code-checkable | none |
| DPDP-Act-36 | Section 36 | not code-checkable | none |
| DPDP-Act-37 | Section 37 | not code-checkable | none |
| DPDP-Act-37(1) | Section 37(1) | not code-checkable | none |
| DPDP-Act-37(2) | Section 37(2) | not code-checkable | none |
| DPDP-Act-37(3) | Section 37(3) | not code-checkable | none |
| DPDP-Act-38 | Section 38 | not code-checkable | none |
| DPDP-Act-38(1) | Section 38(1) | not code-checkable | none |
| DPDP-Act-38(2) | Section 38(2) | not code-checkable | none |
| DPDP-Act-39 | Section 39 | not code-checkable | none |
| DPDP-Act-40 | Section 40 | not code-checkable | none |
| DPDP-Act-40(1) | Section 40(1) | not code-checkable | none |
| DPDP-Act-40(2) | Section 40(2) | not code-checkable | none |
| DPDP-Act-41 | Section 41 | not code-checkable | none |
| DPDP-Act-42 | Section 42 | not code-checkable | none |
| DPDP-Act-42(1) | Section 42(1) | not code-checkable | none |
| DPDP-Act-42(2) | Section 42(2) | not code-checkable | none |
| DPDP-Act-43 | Section 43 | not code-checkable | none |
| DPDP-Act-43(1) | Section 43(1) | not code-checkable | none |
| DPDP-Act-43(2) | Section 43(2) | not code-checkable | none |
| DPDP-Act-43(3) | Section 43(3) | not code-checkable | none |
| DPDP-Act-44 | Section 44 | not code-checkable | none |
| DPDP-Act-44(1) | Section 44(1) | not code-checkable | none |
| DPDP-Act-44(2) | Section 44(2) | not code-checkable | none |
| DPDP-Act-44(3) | Section 44(3) | not code-checkable | none |
| DPDP-Act-Schedule | Schedule | not code-checkable | none |
| DPDP-Act-Schedule-1 | Schedule, item 1 | not code-checkable | none |
| DPDP-Act-Schedule-2 | Schedule, item 2 | not code-checkable | none |
| DPDP-Act-Schedule-3 | Schedule, item 3 | not code-checkable | none |
| DPDP-Act-Schedule-4 | Schedule, item 4 | not code-checkable | none |
| DPDP-Act-Schedule-5 | Schedule, item 5 | not code-checkable | none |
| DPDP-Act-Schedule-6 | Schedule, item 6 | not code-checkable | none |
| DPDP-Act-Schedule-7 | Schedule, item 7 | not code-checkable | none |
| DPDP-Rule-1 | Rule 1 | not code-checkable | none |
| DPDP-Rule-1(2) | Rule 1(2) | not code-checkable | none |
| DPDP-Rule-1(3) | Rule 1(3) | not code-checkable | none |
| DPDP-Rule-1(4) | Rule 1(4) | not code-checkable | none |
| DPDP-Rule-2 | Rule 2 | not code-checkable | none |
| DPDP-Rule-3 | Rule 3 | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(a) | Rule 3(a) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(b) | Rule 3(b) | not determinable | CON-07-angular-consent-notice, CON-07-django-unitemised-notice |
| DPDP-Rule-3(c) | Rule 3(c) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Rule-3(c)(i) | Rule 3(c)(i) | not determinable | CON-04-django-comparable-paths, CON-04-express-withdrawal-path |
| DPDP-Rule-4 | Rule 4 | not code-checkable | none |
| DPDP-Rule-5 | Rule 5 | not code-checkable | none |
| DPDP-Rule-6 | Rule 6 | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1) | Rule 6(1) | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(a) | Rule 6(1)(a) | not determinable | SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-md5-password-hash, SEC-09-ts-query-authentication-secret, SEC-10-ts-storage-header, SEC-11-fastapi-wildcard-cors, SEC-11-ts-wildcard-cors, SEC-15-committed-personal-data |
| DPDP-Rule-6(1)(b) | Rule 6(1)(b) | static | SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-unchecked-nested-records, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(c) | Rule 6(1)(c) | not determinable | MON-01-monitoring-coverage, SEC-12-express-access-logging |
| DPDP-Rule-6(1)(d) | Rule 6(1)(d) | static | SEC-14-terraform-store-backup |
| DPDP-Rule-6(1)(e) | Rule 6(1)(e) | static | SEC-13-ts-access-log-retention |
| DPDP-Rule-6(1)(f) | Rule 6(1)(f) | not code-checkable | none |
| DPDP-Rule-6(1)(g) | Rule 6(1)(g) | not code-checkable | none |
| DPDP-Rule-6(2) | Rule 6(2) | not code-checkable | none |
| DPDP-Rule-7 | Rule 7 | not code-checkable | none |
| DPDP-Rule-7(1) | Rule 7(1) | not code-checkable | none |
| DPDP-Rule-7(2) | Rule 7(2) | not code-checkable | none |
| DPDP-Rule-8 | Rule 8 | static | RET-03-express-erasure-notice, SEC-13-ts-access-log-retention |
| DPDP-Rule-8(1) | Rule 8(1) | static | RET-03-express-erasure-notice |
| DPDP-Rule-8(2) | Rule 8(2) | static | RET-03-express-erasure-notice |
| DPDP-Rule-8(3) | Rule 8(3) | static | SEC-13-ts-access-log-retention |
| DPDP-Rule-9 | Rule 9 | not determinable | RIG-03-express-grievance |
| DPDP-Rule-10 | Rule 10 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Rule-11 | Rule 11 | not code-checkable | none |
| DPDP-Rule-12 | Rule 12 | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rule-13 | Rule 13 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-13(4) | Rule 13(4) | static | TRF-02-terraform-storage-region |
| DPDP-Rule-14 | Rule 14 | not determinable | RIG-01-express-incomplete-export, RIG-02-express-email-correction, RIG-03-express-grievance, RIG-04-rights-notice |
| DPDP-Rule-14(3) | Rule 14(3) | not determinable | RIG-03-express-grievance |
| DPDP-Rule-14(4) | Rule 14(4) | not determinable | RIG-04-rights-notice |
| DPDP-Rule-15 | Rule 15 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-16 | Rule 16 | not code-checkable | none |
| DPDP-Rule-17 | Rule 17 | not code-checkable | none |
| DPDP-Rule-18 | Rule 18 | not code-checkable | none |
| DPDP-Rule-19 | Rule 19 | not code-checkable | none |
| DPDP-Rule-20 | Rule 20 | not code-checkable | none |
| DPDP-Rule-21 | Rule 21 | not code-checkable | none |
| DPDP-Rule-22 | Rule 22 | not code-checkable | none |
| DPDP-Rule-23 | Rule 23 | not code-checkable | none |
| DPDP-Rules-Schedule-First | First Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Second | Second Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Third | Third Schedule | static | RET-03-express-erasure-notice |
| DPDP-Rules-Schedule-Fourth | Fourth Schedule | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rules-Schedule-Fifth | Fifth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Sixth | Sixth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Seventh | Seventh Schedule | not code-checkable | none |

## Method, accuracy and limitations

Static Rules use Semgrep, TypeScript AST and configuration analysers. Cache-only mode replays matching cached LLM fields; uncached fields are not assessed. Live Probe outcomes, when available, appear with their Findings.

| Method | Value |
| --- | --- |
| Target Application | juice-shop |
| Target revision | c9f99228d9d56afb5f5ca7925376292f7fa44b13 |
| Target source | targets/juice-shop |
| Exclusions | **/.git/**, **/node_modules/**, data/static/codefixes/**, test/**, frontend/**/*.spec.ts |
| Files scanned | 1042 |
| Files excluded | 484 |
| Rule count | 51 |
| LLM provider | ollama |
| LLM model | llama3.1 |
| Prompt versions | classification: classification-v1, triage: triage-v1, consent: consent-v1, fix: fix-v1 |
| LLM mode | cache-only |
| Cache hits | 0 |
| Cache misses | 144 |
| LLM fields not assessed | 144 |
| Cache-only reason | ollama is unreachable or authentication failed |
