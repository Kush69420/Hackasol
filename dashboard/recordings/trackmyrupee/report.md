# Report

## Applicability Assumptions

- AA-1: The Act applies: the Target Application processes digital Personal Data in India, or offers goods or services to Data Principals in India. Provisions: DPDP-Act-3 — Section 3. Dependent Findings: CON-03-5948c3734746, CON-03-94c021251539, CON-03-c8163452354e, CON-03-e9015c2df7d8, RIG-04-91983d63d6a4

- AA-2: The Data Fiduciary is not a Significant Data Fiduciary; its duties are shown as conditional. Provisions: DPDP-Act-10 — Section 10. Dependent Findings: none

- AA-3: The Data Fiduciary is not a Third Schedule class; its duties are shown as conditional. Provisions: DPDP-Rule-8(1) — Rule 8(1), DPDP-Rules-Schedule-Third — Third Schedule. Dependent Findings: none

- AA-4: Processing relies on consent unless the code shows a section 7 legitimate use, such as processing an order the Data Principal placed. Provisions: DPDP-Act-7 — Section 7. Dependent Findings: CON-03-5948c3734746, CON-03-94c021251539, CON-03-c8163452354e, CON-03-e9015c2df7d8

## Executive summary

| Severity | DPDP obligation | security dependent on Personal Data | Safeguard |
| --- | --- | --- | --- |
| critical | 0 | 0 | 0 |
| high | 0 | 0 | 0 |
| medium | 0 | 0 | 0 |
| low | 5 | 0 | 0 |

Penalty Ceilings: ₹50 crore; statutory maximum under the Schedule; the Board sets any amount.

### Fix before 13 May 2027

- CON-03-5948c3734746 — Enforceable From 2027-05-13
- CON-03-94c021251539 — Enforceable From 2027-05-13
- CON-03-c8163452354e — Enforceable From 2027-05-13
- CON-03-e9015c2df7d8 — Enforceable From 2027-05-13
- RIG-04-91983d63d6a4 — Enforceable From 2027-05-13

## Personal Data Map

| Element | Data Category | Processing Operations (Evidence) |
| --- | --- | --- |
| collection:AccountCreateView.user | Profile | None recorded |
| collection:AccountUpdateView.user | Profile | None recorded |
| collection:TransferCreateView.user | Profile | None recorded |
| collection:TransferUpdateView.user | Profile | None recorded |
| collection:HoldingsListView.user_currency | Financial | None recorded |
| collection:HoldingsListView.user_accounts | Financial | None recorded |
| collection:YearInReviewView.user_first_name | Profile | None recorded |
| collection:ExpenseUpdateView.user | Profile | None recorded |
| collection:SavingsGoalCreateView.user | Profile | None recorded |
| collection:SavingsGoalUpdateView.user | Profile | None recorded |
| collection:GoalContributionUpdateView.user | Profile | None recorded |
| collection:IncomeCreateView.user | Profile | None recorded |
| collection:IncomeUpdateView.user | Profile | None recorded |
| collection:LoanCreateView.user | Profile | None recorded |
| collection:LoanUpdateView.user | Profile | None recorded |
| collection:RecurringTransactionCreateView.user | Profile | None recorded |
| collection:RecurringTransactionUpdateView.user | Profile | None recorded |
| collection:ProfileUpdateView.is_social_user | Profile | None recorded |
| collection:PaymentHistoryView.profile | Profile | None recorded |

## Findings

### CON-03-5948c3734746 — Pre-ticked or default-true consent

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). protected Data Category Profile has Internal-Restricted Exposure based on Evidence at templates/expenses/dpdp_consent.html:53; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 6(1) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: templates/expenses/dpdp_consent.html:53–53

Primary Provision: DPDP-Act-6(1) — Section 6(1)

Other Provisions: none

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

templates/expenses/dpdp_consent.html:53–53

```
                <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

Data Flow:

- None recorded.

Recommended fix: Ship every consent control unselected, and record consent only after the Data Principal takes a clear affirmative action, such as ticking the box themselves. Do not default a consent value to true in the model, the form or the API, because §6(1) requires that clear affirmative action. Apply the same rule to any consent set during sign-up, import or migration. Tailored: {'fix': 'Remove the `checked` attribute from the consent checkbox so it starts unticked. Consent is only valid when the user ticks the box themselves (DPDP §6(1)). Keep `required` if this consent is truly needed for the service, or remove it if the user may refuse. The template should be: `&lt;input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" required style="width: 2.5em; height: 1.25em;"&gt;`. In the backend, make sure nothing else defaults this consent to true: the model field should use `default=False`, the Django form field should not set `initial=True`, and the API should not fill in a missing value as true. On submit, set consent to true only if `consent_transactions` is actually in the POST data (`\'consent_transactions\' in request.POST`, or `form.cleaned_data` with a `BooleanField` that has no initial value). Store when consent was given (timestamp) alongside it. Check sign-up, import and migration code for any consent set to true without the user\'s action, and reset those records to false until users confirm.'}

LLM triage: true-positive — At templates/expenses/dpdp_consent.html line 53, the consent checkbox 'consent_transactions' has the 'checked' attribute, so it is already ticked when the page loads. That matches the positive CON-03 example, a consent checkbox that is checked by default. Consent the user gets by default does not come from a clear affirmative action, which Section 6(1) requires for valid consent. The 'required' attribute adds to the problem: the form cannot be submitted unless this consent is given, so the consent may also fail to be free and unconditional.; cache key: 3b63bdc9eca2404bfbd6df607b3bb39d559b172e676fd0b44e480d8840520c89

LLM triage citations: DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6

### CON-03-94c021251539 — Pre-ticked or default-true consent

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). protected Data Category Profile has Internal-Restricted Exposure based on Evidence at templates/expenses/dpdp_consent.html:66; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 6(1) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: templates/expenses/dpdp_consent.html:66–66

Primary Provision: DPDP-Act-6(1) — Section 6(1)

Other Provisions: none

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

templates/expenses/dpdp_consent.html:66–66

```
                <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

Data Flow:

- None recorded.

Recommended fix: Ship every consent control unselected, and record consent only after the Data Principal takes a clear affirmative action, such as ticking the box themselves. Do not default a consent value to true in the model, the form or the API, because §6(1) requires that clear affirmative action. Apply the same rule to any consent set during sign-up, import or migration. Tailored: {'fix': 'Take the `checked` attribute off the consent_device checkbox so it starts unticked, and keep `required` so the form can\'t be submitted until the user ticks it. Corrected markup: `&lt;input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" required style="width: 2.5em; height: 1.25em;"&gt;`. If the template is built from a Django form, also look at the form field and any model field behind consent_device. Remove `initial=True` and `default=True` and use `required=True` with `initial=False`, so the server-side value is never true by default and can\'t put `checked` back. On the server, store consent only when the submitted POST includes consent_device=\'on\'. Don\'t assume consent when the field is missing, and save a timestamp with it. Apply the same rule to every place consent is set (sign-up, API serializers, data import or migration scripts) so none of them default it to true. This satisfies DPDP §6(1)\'s requirement for a clear affirmative action.'}

LLM triage: true-positive — The consent checkbox 'consent_device' (id_consent_device) in templates/expenses/dpdp_consent.html line 66 has the 'checked' attribute, so it is ticked before the user does anything. This matches the positive example (a consent checkbox that starts checked) and not the negative one (no 'checked'). The 'required' attribute does not help. Because the box starts ticked, a user can submit the form without ever taking a clear affirmative action, so the consent is not unambiguous as Section 6(1) requires. Any consent collected this way may be invalid under Section 6(2) to the extent it infringes that standard.; cache key: afcfcbb4643c5def1b1f4266eb28d4edc4750ed8d98fec7d377deed007f50c28

LLM triage citations: DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6, DPDP-Act-6(2) — Section 6(2)

### CON-03-c8163452354e — Pre-ticked or default-true consent

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). protected Data Category Profile has Internal-Restricted Exposure based on Evidence at templates/account/signup.html:156; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 6(1) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: templates/account/signup.html:156–156

Primary Provision: DPDP-Act-6(1) — Section 6(1)

Other Provisions: none

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

templates/account/signup.html:156–156

```
                    <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

Data Flow:

- None recorded.

Recommended fix: Ship every consent control unselected, and record consent only after the Data Principal takes a clear affirmative action, such as ticking the box themselves. Do not default a consent value to true in the model, the form or the API, because §6(1) requires that clear affirmative action. Apply the same rule to any consent set during sign-up, import or migration. Tailored: {'fix': 'Remove the `checked` attribute from the consent_device checkbox so it loads unticked. Keep `required` so the form can\'t be submitted until the user ticks the box themselves. Then fix it on the server side too: the Django form field and the model field for consent_device should not default to True (use `initial=False` / `default=False`). Only save consent when the submitted POST data actually includes consent_device, and store when it was given. Corrected markup: `&lt;input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" required style="width: 2.5em; height: 1.25em;"&gt;`. Apply the same rule to consent set during sign-up, import or migration, and in API serializers: never default it to true.'}

LLM triage: true-positive — At templates/account/signup.html:156 the consent checkbox 'consent_device' has the 'checked' attribute, so it is already ticked when the signup form loads. The user doesn't have to do anything to give consent, which goes against the requirement for 'a clear affirmative action'. This matches the positive example, a consent checkbox with 'checked'. The 'required' attribute also means signup can't go ahead without this consent, which makes it look conditional rather than free and unconditional. The Evidence doesn't show whether device processing is actually needed for the signup purpose.; cache key: 13f35e802db86fd00cf2a9fcb1824cc6ed97bd4edacf02b399c7fb62a8e39d09

LLM triage citations: DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6

### CON-03-e9015c2df7d8 — Pre-ticked or default-true consent

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). protected Data Category Profile has Internal-Restricted Exposure based on Evidence at templates/account/signup.html:143; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 6(1) has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: templates/account/signup.html:143–143

Primary Provision: DPDP-Act-6(1) — Section 6(1)

Other Provisions: none

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

templates/account/signup.html:143–143

```
                    <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

Data Flow:

- None recorded.

Recommended fix: Ship every consent control unselected, and record consent only after the Data Principal takes a clear affirmative action, such as ticking the box themselves. Do not default a consent value to true in the model, the form or the API, because §6(1) requires that clear affirmative action. Apply the same rule to any consent set during sign-up, import or migration. Tailored: {'fix': 'Take the `checked` attribute off the consent_transactions checkbox so it starts unticked. Keep `required` so the form can\'t be submitted until the user ticks it themselves: `&lt;input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" required style="width: 2.5em; height: 1.25em;"&gt;`. Also check the server side doesn\'t set this consent to true by default. The Django form field should use `initial=False` (or no initial value) and `required=True`. The model field should use `default=False`, or `null=True` with no default. Any API serializer, sign-up flow, import or migration should save consent as true only when the request explicitly contains the user\'s ticked value, and should store when that consent was given.'}

LLM triage: true-positive — At templates/account/signup.html line 143, the consent checkbox 'consent_transactions' is set to 'checked' by default. This matches the positive example: consent is ticked before the user does anything. A ticked box the user never touched is not the 'clear affirmative action' that Section 6(1) requires, and it does not show unambiguous agreement. The 'required' attribute adds a second problem: the form can't be submitted unless the box stays ticked, so consent becomes a condition of signing up rather than a free, unconditional choice.; cache key: 922e5aac415079693d01ba9718d906c54c3a6902776d4cefe41045a5989dbd88

LLM triage citations: DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6

### RIG-04-91983d63d6a4 — No nomination

Severity: low; CVSS N/A (Compliance Gap: no CVSS score, so the band is the Risk Matrix cell); Risk Matrix cell low (C, Internal-Restricted). protected Data Category Contact has Internal-Restricted Exposure based on Evidence at templates/landing.html:1431; Risk Matrix C/Internal-Restricted cell is low. Primary Provision Section 14 has Penalty Ceiling ₹50 crore (maximum under the Schedule; actual amount set by the Board under s.33).

Exposure: Internal-Restricted; Evidence: templates/landing.html:1431–1431

Primary Provision: DPDP-Act-14 — Section 14

Other Provisions: DPDP-Rule-14(4) — Rule 14(4)

Penalty Ceiling: ₹50 crore (DPDP-Act-Schedule-7); Enforceable From: 2027-05-13.

Status: open.

Evidence:

templates/landing.html:1431–1431

```
                    <span>{% trans "DPDP Act-aligned data handling" %}</span>
```

Data Flow:

- None recorded.

Recommended fix: List nomination alongside the other Data Principal rights in every in-repo notice or rights page, and provide a route for a Data Principal to nominate another individual who can exercise those rights on their behalf. §14 provides for nomination, and Rule 14(4) sets how it is made. Tailored: {'fix': 'The template claims "DPDP Act-aligned data handling", but no in-repo notice or rights page mentions the right to nominate under DPDP Act §14. Add a nomination entry to every privacy notice and Data Principal rights page, next to the rights to access, correct, erase and seek grievance redressal. For example: {% trans "Right to nominate: you may nominate another individual to exercise your rights under the DPDP Act if you die or become incapacitated (Section 14)." %}. Then build a working way to nominate, following the manner set by Rule 14(4): (1) a nominee form or view, reachable from the account or privacy settings and linked from the rights page, that records the nominee\'s name, contact details and relationship; (2) a Nominee model linked to the user, with created and updated timestamps, plus the ability to change or withdraw the nomination at any time; (3) a process for a nominee to submit a rights request with proof of death or incapacity, sent to the grievance or DPO contact for checking. Until nomination is listed and the form works, change the badge text to something that doesn\'t claim alignment, such as "Privacy-focused data handling".'}

LLM triage: false-positive — The flagged line, templates/landing.html:1431, is only a marketing tagline: "DPDP Act-aligned data handling". It is not a notice telling Data Principals what their rights are. It lists no rights at all, so it can't be said to leave out the right to nominate under Section 14(1) or Rule 14(4). The positive example is different: it lists rights (access, correction, erasure) and omits nomination. The evidence contains no list of rights, so the RIG-04-rights-notice pattern doesn't apply to this line. Whether a real rights notice elsewhere on the site omits nomination can't be judged from this evidence and would need its own finding.; cache key: 6c3d7b6e53b6859a01b0ba94d92996c071f807326e314b75d4b3264c1414b94d

LLM triage citations: DPDP-Act-14(1) — Section 14(1), DPDP-Rule-14(4) — Rule 14(4)

### Observations

No Observations.

## Consent Assessment

### recorded

Applicability: applicable — Inventory contains grant paths. Assessment: The identified record is incomplete or its write is unresolved; a boolean alone is not a Consent Record.

Issue Types: CON-06

Linked identifiers: grant_paths:templates/account/signup.html:171, grant_paths:templates/expenses/dpdp_consent.html:80, record:expenses/forms.py:911, record:expenses/family/households.py:203, record:expenses/family/households.py:312, record:expenses/family/households.py:169, record:expenses/family/households.py:255, record:expenses/views/misc.py:448

templates/account/signup.html:171–171

```
        <button class="btn-auth-primary mb-3" type="submit" id="btn_submit_consent">
```

templates/account/signup.html:24–24

```
<form class="signup needs-validation" id="signup_form" method="post" action="{% url 'account_signup' %}" novalidate>
```

finance_tracker/settings.py:414–414

```
ACCOUNT_SIGNUP_FORM_CLASS = 'expenses.forms.CustomSignupForm'
```

expenses/forms.py:876–918

```
class CustomSignupForm(forms.Form):
    # Age confirmation is validated at signup only. It is deliberately not stored (no schema change).
    confirm_age = forms.BooleanField(
        required=True,
        label=_("I confirm that I am 18 years of age or older"),
        error_messages={'required': _("You must confirm that you are 18 years of age or older to create an account.")},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    consent_email = forms.BooleanField(
        required=True,
        label=_("Email Address"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
…
```

expenses/forms.py:911–918

```
        ConsentEvent.objects.create(
            user=user,
            action='GRANTED',
            purpose='Signup Data Collection',
            consent_version='v1.0',
            ip_address=client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )
```

templates/expenses/dpdp_consent.html:80–80

```
    <button class="btn btn-primary btn-xl w-100 mb-3 shadow-sm" type="submit" id="btn_submit_consent">
```

templates/expenses/dpdp_consent.html:17–17

```
<form method="post" action="{% url 'dpdp_consent' %}" class="needs-validation" novalidate>
```

expenses/urls.py:153–153

```
    path('consent/', views.dpdp_consent_view, name='dpdp_consent'),
```

expenses/views/misc.py:418–467

```
def dpdp_consent_view(request):
    """
    Standalone DPDPA consent page for users who haven't granted consent yet.
    """
    try:
        profile = request.user.profile
    except Exception:
        from ..models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

    if profile.consent_granted:
        return redirect('home')
…
```

expenses/views/misc.py:448–455

```
            ConsentEvent.objects.create(
                user=request.user,
                action='GRANTED',
                purpose='Terms and Data Collection',
                consent_version='v1.0',
                ip_address=client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
```

expenses/models.py:3608–3618

```
class ConsentEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consent_events')
    action = models.CharField(max_length=20) # GRANTED, WITHDRAWN, UPDATED
    purpose = models.CharField(max_length=100, null=True, blank=True)
    consent_version = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} {self.action} on {self.timestamp}"
```

expenses/family/households.py:203–204

```
        ConsentEvent.objects.create(user=user, action='WITHDRAWN', purpose=CONSENT_PURPOSE,
                                    consent_version=CONSENT_VERSION)
```

expenses/family/households.py:312–313

```
        ConsentEvent.objects.create(user=removed_user, action='WITHDRAWN', purpose=CONSENT_PURPOSE,
                                    consent_version=CONSENT_VERSION)
```

expenses/family/households.py:169–171

```
            ConsentEvent.objects.create(
                user=user, action='GRANTED', purpose=CONSENT_PURPOSE, consent_version=CONSENT_VERSION,
                ip_address=_client_ip(request), user_agent=(request.META.get('HTTP_USER_AGENT', '')[:500] if request else None))
```

expenses/family/households.py:255–256

```
            ConsentEvent.objects.create(user=member_user, action='WITHDRAWN', purpose=CONSENT_PURPOSE,
                                        consent_version=CONSENT_VERSION)
```

### specific

Applicability: applicable — The deterministic Rule Gate is met by the linked Finding Evidence. Assessment: Finding identified; see linked Findings.

Issue Types: CON-02, CON-03

Linked identifiers: purpose:templates/account/signup.html:124:130, purpose:templates/account/signup.html:140:143, purpose:templates/account/signup.html:153:156, purpose:templates/expenses/dpdp_consent.html:34:40, purpose:templates/expenses/dpdp_consent.html:50:53, purpose:templates/expenses/dpdp_consent.html:63:66, control:templates/account/signup.html:130, control:templates/account/signup.html:143, control:templates/account/signup.html:156, control:templates/expenses/dpdp_consent.html:40, control:templates/expenses/dpdp_consent.html:53, control:templates/expenses/dpdp_consent.html:66, control:templates/expenses/family/join.html:58, CON-03-5948c3734746, CON-03-94c021251539, CON-03-c8163452354e, CON-03-e9015c2df7d8

templates/account/signup.html:124–124

```
                    <p class="small text-muted mb-0">{% trans "Used to identify your account, send secure login keys, and email notifications." %}</p>
```

templates/account/signup.html:130–130

```
                    <input type="hidden" name="consent_email" value="on">
```

templates/account/signup.html:140–140

```
                    <p class="small text-muted mb-0">{% trans "Required to process, format, and display your income, expenses, budgets, and savings goals. All the data is manually entered by you; TrackMyRupee never asks for any credentials." %}</p>
```

templates/account/signup.html:143–143

```
                    <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/account/signup.html:153–153

```
                    <p class="small text-muted mb-0">{% trans "Collected to verify authentic sessions, maintain secure tokens, and prevent automated bot access." %}</p>
```

templates/account/signup.html:156–156

```
                    <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:34–34

```
                <p class="small text-muted mb-0">{% trans "To identify your account, send secure login keys, and email notifications." %}</p>
```

templates/expenses/dpdp_consent.html:40–40

```
                <input type="hidden" name="consent_email" value="on">
```

templates/expenses/dpdp_consent.html:50–50

```
                <p class="small text-muted mb-0">{% trans "To process, format, and display your income, expenses, budgets, and savings goals. All the data is manually entered by you; TrackMyRupee never asks for any credentials." %}</p>
```

templates/expenses/dpdp_consent.html:53–53

```
                <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:63–63

```
                <p class="small text-muted mb-0">{% trans "Collected to verify authentic sessions, maintain secure tokens, and prevent automated bot access." %}</p>
```

templates/expenses/dpdp_consent.html:66–66

```
                <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/family/join.html:58–58

```
                <input class="form-check-input" type="checkbox" name="consent" id="fam-consent" required>
```

### enforced server-side

Applicability: applicable — Inventory contains purposes. Assessment: Not assessed: no server-side Enforcement Point is linked to both a Purpose and a Processing Operation.

Issue Types: CON-01

Linked identifiers: purpose:templates/account/signup.html:124:130, purpose:templates/account/signup.html:140:143, purpose:templates/account/signup.html:153:156, purpose:templates/expenses/dpdp_consent.html:34:40, purpose:templates/expenses/dpdp_consent.html:50:53, purpose:templates/expenses/dpdp_consent.html:63:66, operation:expenses/posthog_utils.py:115, operation:expenses/posthog_utils.py:135, enforcement:expenses/middleware.py:147, enforcement:expenses/posthog_utils.py:108, enforcement:expenses/posthog_utils.py:125

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — consent-after-withdrawal: The Processing Operation was unavailable after withdrawal Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — consent-declined:consent_email: Signup with this consent declined was rejected, so the Purpose is enforced at signup (it is mandatory rather than optional) Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — consent-declined:consent_transactions: Signup with this consent declined was rejected, so the Purpose is enforced at signup (it is mandatory rather than optional) Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — consent-declined:consent_device: Signup with this consent declined was rejected, so the Purpose is enforced at signup (it is mandatory rather than optional) Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — analytics-declined: No outbound event was observed after the decline or withdrawal while the granted control produced 2 Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — analytics-withdrawn: No outbound event was observed after the decline or withdrawal while the granted control produced 2 Static verdict above is unchanged.

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Not Confirmed (enforcement observed) — withdrawal-data-removal: The account no longer authenticated and no account-linked rows remained Static verdict above is unchanged.

templates/account/signup.html:124–124

```
                    <p class="small text-muted mb-0">{% trans "Used to identify your account, send secure login keys, and email notifications." %}</p>
```

templates/account/signup.html:130–130

```
                    <input type="hidden" name="consent_email" value="on">
```

templates/account/signup.html:140–140

```
                    <p class="small text-muted mb-0">{% trans "Required to process, format, and display your income, expenses, budgets, and savings goals. All the data is manually entered by you; TrackMyRupee never asks for any credentials." %}</p>
```

templates/account/signup.html:143–143

```
                    <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/account/signup.html:153–153

```
                    <p class="small text-muted mb-0">{% trans "Collected to verify authentic sessions, maintain secure tokens, and prevent automated bot access." %}</p>
```

templates/account/signup.html:156–156

```
                    <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:34–34

```
                <p class="small text-muted mb-0">{% trans "To identify your account, send secure login keys, and email notifications." %}</p>
```

templates/expenses/dpdp_consent.html:40–40

```
                <input type="hidden" name="consent_email" value="on">
```

templates/expenses/dpdp_consent.html:50–50

```
                <p class="small text-muted mb-0">{% trans "To process, format, and display your income, expenses, budgets, and savings goals. All the data is manually entered by you; TrackMyRupee never asks for any credentials." %}</p>
```

templates/expenses/dpdp_consent.html:53–53

```
                <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:63–63

```
                <p class="small text-muted mb-0">{% trans "Collected to verify authentic sessions, maintain secure tokens, and prevent automated bot access." %}</p>
```

templates/expenses/dpdp_consent.html:66–66

```
                <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

expenses/onboarding_v2.py:25–25

```
from .posthog_utils import ph_capture
```

expenses/onboarding_v2.py:70–70

```
        ph_capture(user, event_name, filtered_props)
```

expenses/signals.py:35–35

```
from .posthog_utils import ph_capture, ph_identify
```

expenses/signals.py:47–47

```
    ph_capture(user, 'user_signed_up', {'method': method})
```

expenses/signals.py:56–56

```
    ph_capture(user, 'user_logged_in', {'method': method})
```

expenses/insights/telemetry.py:5–5

```
from ..posthog_utils import ph_capture
```

expenses/insights/telemetry.py:12–12

```
    ph_capture(user, f'insight_{name}', clean)
```

expenses/views/accounts.py:60–60

```
from ..posthog_utils import ph_capture
```

expenses/views/accounts.py:2081–2081

```
            ph_capture(request.user, 'holding_nav_refreshed', {})
```

expenses/views/accounts.py:2113–2113

```
            ph_capture(request.user, 'account_nav_refreshed', {'funds': done})
```

expenses/views/accounts.py:2161–2161

```
        ph_capture(request.user, 'holding_created', {'has_scheme_code': bool(holding.scheme_code)})
```

expenses/views/accounts.py:2181–2181

```
    ph_capture(request.user, 'holding_deleted', {})
```

expenses/views/accounts.py:2230–2230

```
    ph_capture(request.user, 'holding_valued_manually', {})
```

expenses/views/accounts.py:2329–2329

```
        ph_capture(request.user, 'holding_purchase_added', {'from_transfer': bool(transfer)})
```

expenses/views/accounts.py:2361–2361

```
    ph_capture(request.user, 'holding_sold', {})
```

expenses/views/accounts.py:800–800

```
            ph_capture(self.request.user, 'account_created', {'account_type': self.object.account_type, 'currency': self.object.currency, 'has_credit_limit': bool(getattr(self.object, 'credit_limit', None))})
```

expenses/views/accounts.py:832–832

```
        ph_capture(self.request.user, 'account_updated', {'account_type': self.object.account_type})
```

expenses/views/accounts.py:913–913

```
        ph_capture(self.request.user, 'account_deleted', {})
```

expenses/views/accounts.py:935–935

```
        ph_capture(request.user, 'account_restored', {})
```

expenses/views/accounts.py:959–959

```
            ph_capture(request.user, 'account_pinned', {'account_id': str(account.uuid)})
```

expenses/views/accounts.py:962–962

```
            ph_capture(request.user, 'account_unpinned', {'account_id': str(account.uuid)})
```

expenses/views/accounts.py:993–993

```
            ph_capture(request.user, 'account_quick_created', {'account_type': account.account_type})
```

expenses/views/accounts.py:1044–1044

```
            ph_capture(self.request.user, 'transfer_allocated', {'funds': len(form.allocation_rows)})
```

expenses/views/accounts.py:1097–1097

```
            ph_capture(self.request.user, 'transfer_created', {'currency': getattr(self.object, 'currency', ''), 'is_cross_currency': bool(getattr(self.object, 'exchange_rate', None) and self.object.exchange_rate != 1)})
```

expenses/views/accounts.py:1156–1156

```
            ph_capture(self.request.user, 'transfer_updated', {})
```

expenses/views/accounts.py:1176–1176

```
        ph_capture(self.request.user, 'transfer_deleted', {})
```

expenses/views/accounts.py:1917–1917

```
                        ph_capture(request.user, 'maturity_income_recorded', {})
```

expenses/views/capital_events.py:23–23

```
from ..posthog_utils import ph_capture
```

expenses/views/capital_events.py:190–190

```
                ph_capture(request.user, 'capital_event_created', {'subtype': getattr(event, 'subtype', '')})
```

expenses/views/capital_events.py:244–244

```
                ph_capture(request.user, 'capital_event_updated', {})
```

expenses/views/capital_events.py:279–279

```
        ph_capture(self.request.user, 'capital_event_deleted', {})
```

expenses/views/capital_events.py:316–316

```
            ph_capture(request.user, 'capital_event_converted_to_expense', {})
```

expenses/views/categories.py:18–18

```
from ..posthog_utils import ph_capture
```

expenses/views/categories.py:134–134

```
        ph_capture(self.request.user, 'category_created', {'has_budget_limit': bool(form.instance.limit)})
```

expenses/views/categories.py:208–208

```
            ph_capture(self.request.user, 'category_updated', {})
```

expenses/views/categories.py:221–221

```
        ph_capture(self.request.user, 'category_deleted', {})
```

expenses/views/categories.py:239–239

```
            ph_capture(request.user, 'category_bulk_deleted', {'count': deleted_count})
```

expenses/views/composer.py:29–29

```
from ..posthog_utils import ph_capture
```

expenses/views/composer.py:172–172

```
        ph_capture(request.user, 'expense_added', props)
```

expenses/views/composer.py:213–213

```
    ph_capture(request.user, 'expense_undone', {})
```

expenses/views/composer.py:252–252

```
    ph_capture(request.user, name, props)
```

expenses/views/expenses.py:17–17

```
from ..posthog_utils import ph_capture
```

expenses/views/expenses.py:168–171

```
            ph_capture(self.request.user, 'expense_updated', {
                'currency': self.object.currency,
                'category': self.object.category or '',
            })
```

expenses/views/expenses.py:209–209

```
        ph_capture(self.request.user, 'expense_deleted', {})
```

expenses/views/expenses.py:247–247

```
            ph_capture(request.user, 'expense_bulk_deleted', {'count': deleted_count})
```

expenses/views/expenses.py:302–302

```
            ph_capture(request.user, 'expense_bulk_updated', {'count': updated_count})
```

expenses/views/expenses.py:341–341

```
        ph_capture(request.user, 'expense_converted_to_capital_event', {})
```

expenses/views/export.py:30–30

```
from ..posthog_utils import ph_capture
```

expenses/views/export.py:263–263

```
    ph_capture(request.user, 'expense_list_exported', {'has_filters': bool(search_query or start_date or end_date or categories)})
```

expenses/views/export.py:207–207

```
        ph_capture(request.user, 'data_exported', {'entities': selected_entities, 'format': 'zip' if len(files_to_zip) > 1 else 'csv'})
```

expenses/views/goals.py:23–23

```
from ..posthog_utils import ph_capture
```

expenses/views/goals.py:79–79

```
        ph_capture(self.request.user, 'goal_created', {'has_target_date': bool(self.object.target_date)})
```

expenses/views/goals.py:114–114

```
        ph_capture(self.request.user, 'goal_updated', {})
```

expenses/views/goals.py:126–126

```
        ph_capture(self.request.user, 'goal_deleted', {})
```

expenses/views/goals.py:480–480

```
            ph_capture(request.user, 'goal_contribution_added', {})
```

expenses/views/goals.py:521–521

```
        ph_capture(self.request.user, 'goal_contribution_updated', {})
```

expenses/views/goals.py:542–542

```
        ph_capture(self.request.user, 'goal_contribution_deleted', {})
```

expenses/views/income.py:21–21

```
from ..posthog_utils import ph_capture
```

expenses/views/income.py:324–328

```
        ph_capture(self.request.user, 'income_created', {
            'currency': self.object.currency,
            'source_type': self.object.source_type or '',
            'has_account': bool(self.object.account_id),
        })
```

expenses/views/income.py:367–369

```
            ph_capture(self.request.user, 'income_updated', {
                'currency': self.object.currency,
            })
```

expenses/views/income.py:391–391

```
        ph_capture(self.request.user, 'income_deleted', {})
```

expenses/views/loans.py:25–25

```
from ..posthog_utils import ph_capture
```

expenses/views/loans.py:203–203

```
        ph_capture(self.request.user, 'loan_created', {'loan_type': getattr(self.object, 'loan_type', ''), 'currency': self.object.currency, 'tenure_months': self.object.duration_months})
```

expenses/views/loans.py:233–233

```
        ph_capture(self.request.user, 'loan_updated', {})
```

expenses/views/loans.py:256–256

```
        ph_capture(self.request.user, 'loan_deleted', {})
```

expenses/views/loans.py:519–519

```
                ph_capture(request.user, 'loan_repayment_added', {'via': 'pay_emi' if request.POST.get('from_pay_emi') else 'loan_page'})
```

expenses/views/loans.py:565–565

```
            ph_capture(request.user, 'pay_emi_opened', {'has_loan': bool(loan)})
```

expenses/views/loans.py:583–583

```
            ph_capture(request.user, 'loan_interest_rate_updated', {})
```

expenses/views/loans.py:599–599

```
        ph_capture(self.request.user, 'loan_repayment_deleted', {})
```

expenses/views/misc.py:48–48

```
from ..posthog_utils import ph_capture
```

expenses/views/misc.py:266–271

```
                        ph_capture(request.user, 'expenses_imported', {
                            'created_count': summary['created_count'],
                            'duplicate_count': summary['duplicate_count'],
                            'error_count': summary['error_count'],
                            'total_rows': summary['total_rows'],
                        })
```

expenses/views/portfolio_summary.py:7–7

```
from ..posthog_utils import ph_capture
```

expenses/views/portfolio_summary.py:14–17

```
    ph_capture(request.user, 'portfolio_summary_viewed', {
        'investment_blocks': len(summary['blocks']), 'has_liabilities': bool(summary['liability_rows']),
        'has_sips': bool(summary['sip_rows']),
    })
```

expenses/views/recurring.py:19–19

```
from ..posthog_utils import ph_capture
```

expenses/views/recurring.py:230–230

```
        ph_capture(self.request.user, 'recurring_created', {'transaction_type': self.object.transaction_type, 'frequency': self.object.frequency})
```

expenses/views/recurring.py:272–272

```
        ph_capture(self.request.user, 'recurring_updated', {'frequency': self.object.frequency})
```

expenses/views/recurring.py:320–320

```
        ph_capture(self.request.user, 'recurring_deleted', {})
```

expenses/views/settings.py:39–39

```
from ..posthog_utils import ph_capture
```

expenses/views/settings.py:240–240

```
            ph_capture(user, 'account_deleted', {})
```

expenses/views/settings.py:454–454

```
        ph_capture(self.request.user, 'currency_changed', {'old_currency': old_currency, 'new_currency': form.cleaned_data.get('currency', '')})
```

expenses/views/settings.py:490–490

```
        ph_capture(self.request.user, 'language_changed', {'new_language': form.cleaned_data.get('language', '')})
```

expenses/views/settings.py:548–548

```
        ph_capture(self.request.user, 'profile_updated', {})
```

expenses/posthog_utils.py:115–115

```
        client.capture(posthog_distinct_id(user), event=event, properties=_scrub(properties))
```

expenses/posthog_utils.py:135–135

```
        client.identify(posthog_distinct_id(user), properties=props)
```

finance_tracker/settings.py:146–146

```
    'expenses.middleware.DPDPAConsentMiddleware',
```

expenses/middleware.py:147–147

```
            if profile and not profile.consent_granted and not is_static_or_media and url_name not in allowed_url_names:
```

expenses/middleware.py:148–148

```
                return redirect('dpdp_consent')
```

expenses/posthog_utils.py:108–108

```
    if not analytics_consent_given():
```

expenses/posthog_utils.py:125–125

```
    if not analytics_consent_given():
```

### withdrawable with comparable ease

Applicability: applicable — Inventory contains grant paths. Assessment: Not determinable: a grant and a comparable Withdrawal Path for the same Purpose not established by the static inventory.

Issue Types: CON-04

Linked identifiers: grant_paths:templates/account/signup.html:171, grant_paths:templates/expenses/dpdp_consent.html:80, withdrawal_paths:templates/expenses/withdraw_consent_confirm.html:37

Static step counts: {   "grant": [     null,     null   ],   "withdrawal": [     null   ] }

Live Probe (trackmyrupee @ 47990e4f19d7, 2026-11-23T21:28:56+00:00): Inconclusive (not run or inconclusive; no effect on the static verdict) — comparable-ease: Grant recorded 3 interactions and withdrawal 2; the Report does not establish a common starting point or Purpose link Static verdict above is unchanged.

templates/account/signup.html:171–171

```
        <button class="btn-auth-primary mb-3" type="submit" id="btn_submit_consent">
```

templates/account/signup.html:24–24

```
<form class="signup needs-validation" id="signup_form" method="post" action="{% url 'account_signup' %}" novalidate>
```

finance_tracker/settings.py:414–414

```
ACCOUNT_SIGNUP_FORM_CLASS = 'expenses.forms.CustomSignupForm'
```

expenses/forms.py:876–918

```
class CustomSignupForm(forms.Form):
    # Age confirmation is validated at signup only. It is deliberately not stored (no schema change).
    confirm_age = forms.BooleanField(
        required=True,
        label=_("I confirm that I am 18 years of age or older"),
        error_messages={'required': _("You must confirm that you are 18 years of age or older to create an account.")},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    consent_email = forms.BooleanField(
        required=True,
        label=_("Email Address"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
…
```

expenses/forms.py:911–918

```
        ConsentEvent.objects.create(
            user=user,
            action='GRANTED',
            purpose='Signup Data Collection',
            consent_version='v1.0',
            ip_address=client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
        )
```

templates/expenses/dpdp_consent.html:80–80

```
    <button class="btn btn-primary btn-xl w-100 mb-3 shadow-sm" type="submit" id="btn_submit_consent">
```

templates/expenses/dpdp_consent.html:17–17

```
<form method="post" action="{% url 'dpdp_consent' %}" class="needs-validation" novalidate>
```

expenses/urls.py:153–153

```
    path('consent/', views.dpdp_consent_view, name='dpdp_consent'),
```

expenses/views/misc.py:418–467

```
def dpdp_consent_view(request):
    """
    Standalone DPDPA consent page for users who haven't granted consent yet.
    """
    try:
        profile = request.user.profile
    except Exception:
        from ..models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

    if profile.consent_granted:
        return redirect('home')
…
```

expenses/views/misc.py:448–455

```
            ConsentEvent.objects.create(
                user=request.user,
                action='GRANTED',
                purpose='Terms and Data Collection',
                consent_version='v1.0',
                ip_address=client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
```

templates/expenses/withdraw_consent_confirm.html:37–37

```
                        <button type="submit" class="btn btn-danger px-2 fw-bold w-50 text-nowrap">
```

expenses/urls.py:154–154

```
    path('settings/consent/withdraw/', views.WithdrawConsentView.as_view(), name='withdraw-consent'),
```

expenses/views/settings.py:246–263

```
class WithdrawConsentView(LoginRequiredMixin, DeleteView):
    model = django_settings.AUTH_USER_MODEL
    success_url = reverse_lazy('landing')
    template_name =«SECRET».html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = self.get_object()
        user_id = user.id
        dispatched = dispatch_account_deletion(user_id)
…
```

### propagated to Data Processors

Applicability: applicable — Inventory contains processors. Assessment: processor:expenses/posthog_utils.py:115: gated — A server-side consent condition precedes this call; prior transfers and deletion remain unresolved.; processor:expenses/posthog_utils.py:135: gated — A server-side consent condition precedes this call; prior transfers and deletion remain unresolved.

Issue Types: CON-05

Linked identifiers: processor:expenses/posthog_utils.py:115, processor:expenses/posthog_utils.py:135, withdrawal_paths:templates/expenses/withdraw_consent_confirm.html:37

expenses/onboarding_v2.py:25–25

```
from .posthog_utils import ph_capture
```

expenses/onboarding_v2.py:70–70

```
        ph_capture(user, event_name, filtered_props)
```

expenses/signals.py:35–35

```
from .posthog_utils import ph_capture, ph_identify
```

expenses/signals.py:47–47

```
    ph_capture(user, 'user_signed_up', {'method': method})
```

expenses/signals.py:56–56

```
    ph_capture(user, 'user_logged_in', {'method': method})
```

expenses/insights/telemetry.py:5–5

```
from ..posthog_utils import ph_capture
```

expenses/insights/telemetry.py:12–12

```
    ph_capture(user, f'insight_{name}', clean)
```

expenses/views/accounts.py:60–60

```
from ..posthog_utils import ph_capture
```

expenses/views/accounts.py:2081–2081

```
            ph_capture(request.user, 'holding_nav_refreshed', {})
```

expenses/views/accounts.py:2113–2113

```
            ph_capture(request.user, 'account_nav_refreshed', {'funds': done})
```

expenses/views/accounts.py:2161–2161

```
        ph_capture(request.user, 'holding_created', {'has_scheme_code': bool(holding.scheme_code)})
```

expenses/views/accounts.py:2181–2181

```
    ph_capture(request.user, 'holding_deleted', {})
```

expenses/views/accounts.py:2230–2230

```
    ph_capture(request.user, 'holding_valued_manually', {})
```

expenses/views/accounts.py:2329–2329

```
        ph_capture(request.user, 'holding_purchase_added', {'from_transfer': bool(transfer)})
```

expenses/views/accounts.py:2361–2361

```
    ph_capture(request.user, 'holding_sold', {})
```

expenses/views/accounts.py:800–800

```
            ph_capture(self.request.user, 'account_created', {'account_type': self.object.account_type, 'currency': self.object.currency, 'has_credit_limit': bool(getattr(self.object, 'credit_limit', None))})
```

expenses/views/accounts.py:832–832

```
        ph_capture(self.request.user, 'account_updated', {'account_type': self.object.account_type})
```

expenses/views/accounts.py:913–913

```
        ph_capture(self.request.user, 'account_deleted', {})
```

expenses/views/accounts.py:935–935

```
        ph_capture(request.user, 'account_restored', {})
```

expenses/views/accounts.py:959–959

```
            ph_capture(request.user, 'account_pinned', {'account_id': str(account.uuid)})
```

expenses/views/accounts.py:962–962

```
            ph_capture(request.user, 'account_unpinned', {'account_id': str(account.uuid)})
```

expenses/views/accounts.py:993–993

```
            ph_capture(request.user, 'account_quick_created', {'account_type': account.account_type})
```

expenses/views/accounts.py:1044–1044

```
            ph_capture(self.request.user, 'transfer_allocated', {'funds': len(form.allocation_rows)})
```

expenses/views/accounts.py:1097–1097

```
            ph_capture(self.request.user, 'transfer_created', {'currency': getattr(self.object, 'currency', ''), 'is_cross_currency': bool(getattr(self.object, 'exchange_rate', None) and self.object.exchange_rate != 1)})
```

expenses/views/accounts.py:1156–1156

```
            ph_capture(self.request.user, 'transfer_updated', {})
```

expenses/views/accounts.py:1176–1176

```
        ph_capture(self.request.user, 'transfer_deleted', {})
```

expenses/views/accounts.py:1917–1917

```
                        ph_capture(request.user, 'maturity_income_recorded', {})
```

expenses/views/capital_events.py:23–23

```
from ..posthog_utils import ph_capture
```

expenses/views/capital_events.py:190–190

```
                ph_capture(request.user, 'capital_event_created', {'subtype': getattr(event, 'subtype', '')})
```

expenses/views/capital_events.py:244–244

```
                ph_capture(request.user, 'capital_event_updated', {})
```

expenses/views/capital_events.py:279–279

```
        ph_capture(self.request.user, 'capital_event_deleted', {})
```

expenses/views/capital_events.py:316–316

```
            ph_capture(request.user, 'capital_event_converted_to_expense', {})
```

expenses/views/categories.py:18–18

```
from ..posthog_utils import ph_capture
```

expenses/views/categories.py:134–134

```
        ph_capture(self.request.user, 'category_created', {'has_budget_limit': bool(form.instance.limit)})
```

expenses/views/categories.py:208–208

```
            ph_capture(self.request.user, 'category_updated', {})
```

expenses/views/categories.py:221–221

```
        ph_capture(self.request.user, 'category_deleted', {})
```

expenses/views/categories.py:239–239

```
            ph_capture(request.user, 'category_bulk_deleted', {'count': deleted_count})
```

expenses/views/composer.py:29–29

```
from ..posthog_utils import ph_capture
```

expenses/views/composer.py:172–172

```
        ph_capture(request.user, 'expense_added', props)
```

expenses/views/composer.py:213–213

```
    ph_capture(request.user, 'expense_undone', {})
```

expenses/views/composer.py:252–252

```
    ph_capture(request.user, name, props)
```

expenses/views/expenses.py:17–17

```
from ..posthog_utils import ph_capture
```

expenses/views/expenses.py:168–171

```
            ph_capture(self.request.user, 'expense_updated', {
                'currency': self.object.currency,
                'category': self.object.category or '',
            })
```

expenses/views/expenses.py:209–209

```
        ph_capture(self.request.user, 'expense_deleted', {})
```

expenses/views/expenses.py:247–247

```
            ph_capture(request.user, 'expense_bulk_deleted', {'count': deleted_count})
```

expenses/views/expenses.py:302–302

```
            ph_capture(request.user, 'expense_bulk_updated', {'count': updated_count})
```

expenses/views/expenses.py:341–341

```
        ph_capture(request.user, 'expense_converted_to_capital_event', {})
```

expenses/views/export.py:30–30

```
from ..posthog_utils import ph_capture
```

expenses/views/export.py:263–263

```
    ph_capture(request.user, 'expense_list_exported', {'has_filters': bool(search_query or start_date or end_date or categories)})
```

expenses/views/export.py:207–207

```
        ph_capture(request.user, 'data_exported', {'entities': selected_entities, 'format': 'zip' if len(files_to_zip) > 1 else 'csv'})
```

expenses/views/goals.py:23–23

```
from ..posthog_utils import ph_capture
```

expenses/views/goals.py:79–79

```
        ph_capture(self.request.user, 'goal_created', {'has_target_date': bool(self.object.target_date)})
```

expenses/views/goals.py:114–114

```
        ph_capture(self.request.user, 'goal_updated', {})
```

expenses/views/goals.py:126–126

```
        ph_capture(self.request.user, 'goal_deleted', {})
```

expenses/views/goals.py:480–480

```
            ph_capture(request.user, 'goal_contribution_added', {})
```

expenses/views/goals.py:521–521

```
        ph_capture(self.request.user, 'goal_contribution_updated', {})
```

expenses/views/goals.py:542–542

```
        ph_capture(self.request.user, 'goal_contribution_deleted', {})
```

expenses/views/income.py:21–21

```
from ..posthog_utils import ph_capture
```

expenses/views/income.py:324–328

```
        ph_capture(self.request.user, 'income_created', {
            'currency': self.object.currency,
            'source_type': self.object.source_type or '',
            'has_account': bool(self.object.account_id),
        })
```

expenses/views/income.py:367–369

```
            ph_capture(self.request.user, 'income_updated', {
                'currency': self.object.currency,
            })
```

expenses/views/income.py:391–391

```
        ph_capture(self.request.user, 'income_deleted', {})
```

expenses/views/loans.py:25–25

```
from ..posthog_utils import ph_capture
```

expenses/views/loans.py:203–203

```
        ph_capture(self.request.user, 'loan_created', {'loan_type': getattr(self.object, 'loan_type', ''), 'currency': self.object.currency, 'tenure_months': self.object.duration_months})
```

expenses/views/loans.py:233–233

```
        ph_capture(self.request.user, 'loan_updated', {})
```

expenses/views/loans.py:256–256

```
        ph_capture(self.request.user, 'loan_deleted', {})
```

expenses/views/loans.py:519–519

```
                ph_capture(request.user, 'loan_repayment_added', {'via': 'pay_emi' if request.POST.get('from_pay_emi') else 'loan_page'})
```

expenses/views/loans.py:565–565

```
            ph_capture(request.user, 'pay_emi_opened', {'has_loan': bool(loan)})
```

expenses/views/loans.py:583–583

```
            ph_capture(request.user, 'loan_interest_rate_updated', {})
```

expenses/views/loans.py:599–599

```
        ph_capture(self.request.user, 'loan_repayment_deleted', {})
```

expenses/views/misc.py:48–48

```
from ..posthog_utils import ph_capture
```

expenses/views/misc.py:266–271

```
                        ph_capture(request.user, 'expenses_imported', {
                            'created_count': summary['created_count'],
                            'duplicate_count': summary['duplicate_count'],
                            'error_count': summary['error_count'],
                            'total_rows': summary['total_rows'],
                        })
```

expenses/views/portfolio_summary.py:7–7

```
from ..posthog_utils import ph_capture
```

expenses/views/portfolio_summary.py:14–17

```
    ph_capture(request.user, 'portfolio_summary_viewed', {
        'investment_blocks': len(summary['blocks']), 'has_liabilities': bool(summary['liability_rows']),
        'has_sips': bool(summary['sip_rows']),
    })
```

expenses/views/recurring.py:19–19

```
from ..posthog_utils import ph_capture
```

expenses/views/recurring.py:230–230

```
        ph_capture(self.request.user, 'recurring_created', {'transaction_type': self.object.transaction_type, 'frequency': self.object.frequency})
```

expenses/views/recurring.py:272–272

```
        ph_capture(self.request.user, 'recurring_updated', {'frequency': self.object.frequency})
```

expenses/views/recurring.py:320–320

```
        ph_capture(self.request.user, 'recurring_deleted', {})
```

expenses/views/settings.py:39–39

```
from ..posthog_utils import ph_capture
```

expenses/views/settings.py:240–240

```
            ph_capture(user, 'account_deleted', {})
```

expenses/views/settings.py:454–454

```
        ph_capture(self.request.user, 'currency_changed', {'old_currency': old_currency, 'new_currency': form.cleaned_data.get('currency', '')})
```

expenses/views/settings.py:490–490

```
        ph_capture(self.request.user, 'language_changed', {'new_language': form.cleaned_data.get('language', '')})
```

expenses/views/settings.py:548–548

```
        ph_capture(self.request.user, 'profile_updated', {})
```

expenses/posthog_utils.py:115–115

```
        client.capture(posthog_distinct_id(user), event=event, properties=_scrub(properties))
```

expenses/posthog_utils.py:135–135

```
        client.identify(posthog_distinct_id(user), properties=props)
```

templates/expenses/withdraw_consent_confirm.html:37–37

```
                        <button type="submit" class="btn btn-danger px-2 fw-bold w-50 text-nowrap">
```

expenses/urls.py:154–154

```
    path('settings/consent/withdraw/', views.WithdrawConsentView.as_view(), name='withdraw-consent'),
```

expenses/views/settings.py:246–263

```
class WithdrawConsentView(LoginRequiredMixin, DeleteView):
    model = django_settings.AUTH_USER_MODEL
    success_url = reverse_lazy('landing')
    template_name =«SECRET».html'

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = self.get_object()
        user_id = user.id
        dispatched = dispatch_account_deletion(user_id)
…
```

expenses/posthog_utils.py:108–108

```
    if not analytics_consent_given():
```

expenses/posthog_utils.py:125–125

```
    if not analytics_consent_given():
```

### preceded by notice

Applicability: applicable — Inventory contains controls. Assessment: notice:docs/index.html:215: itemised=None, language=en, before grant=None; notice:docs/index.html:241: itemised=None, language=en, before grant=None; notice:templates/alternative_landing.html:210: itemised=None, language=None, before grant=None; notice:templates/alternatives_hub.html:58: itemised=None, language=None, before grant=None; notice:templates/landing_classic.html:1590: itemised=None, language=en, before grant=None; notice:templates/privacy_policy.html:17: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:130: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:136: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:141: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:154: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:262: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:333: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:408: itemised=None, language=None, before grant=None; notice:templates/privacy_policy.html:418: itemised=None, language=None, before grant=None; notice:templates/security.html:42: itemised=None, language=None, before grant=None; notice:templates/terms_of_service.html:67: itemised=None, language=None, before grant=None; notice:templates/terms_of_service.html:72: itemised=None, language=None, before grant=None; notice:templates/terms_of_service.html:149: itemised=None, language=None, before grant=None; notice:templates/terms_of_service.html:168: itemised=None, language=None, before grant=None; notice:templates/account/signup.html:105: itemised=True, language=None, before grant=True; notice:templates/account/signup.html:179: itemised=True, language=None, before grant=False; notice:templates/account/email/base_email.html:153: itemised=None, language=None, before grant=None; notice:templates/blog/blog_list.html:16: itemised=None, language=None, before grant=None; notice:templates/components/compare_plans_modal.html:14: itemised=None, language=None, before grant=None; notice:templates/components/cookie_consent.html:5: itemised=None, language=None, before grant=None; notice:templates/components/public_footer.html:12: itemised=None, language=None, before grant=None; notice:templates/email/subscription_expiry_reminder.html:19: itemised=None, language=None, before grant=None; notice:templates/email/welcome_email.html:32: itemised=None, language=None, before grant=None; notice:templates/expenses/capital_event_form.html:121: itemised=False, language=None, before grant=None; notice:templates/expenses/dpdp_consent.html:12: itemised=None, language=None, before grant=None; notice:templates/expenses/dpdp_consent.html:88: itemised=True, language=None, before grant=False; notice:templates/expenses/settings_home.html:416: itemised=None, language=None, before grant=None; notice:templates/expenses/settings_home.html:427: itemised=None, language=None, before grant=None; notice:templates/expenses/withdraw_consent_confirm.html:17: itemised=None, language=None, before grant=None; notice:templates/expenses/partials/_capital_event_list.html:327: itemised=None, language=None, before grant=None; unresolved values are not assessed.

Issue Types: CON-07

Linked identifiers: control:templates/account/signup.html:130, control:templates/account/signup.html:143, control:templates/account/signup.html:156, control:templates/expenses/dpdp_consent.html:40, control:templates/expenses/dpdp_consent.html:53, control:templates/expenses/dpdp_consent.html:66, control:templates/expenses/family/join.html:58, notice:docs/index.html:215, notice:docs/index.html:241, notice:templates/alternative_landing.html:210, notice:templates/alternatives_hub.html:58, notice:templates/landing_classic.html:1590, notice:templates/privacy_policy.html:17, notice:templates/privacy_policy.html:130, notice:templates/privacy_policy.html:136, notice:templates/privacy_policy.html:141, notice:templates/privacy_policy.html:154, notice:templates/privacy_policy.html:262, notice:templates/privacy_policy.html:333, notice:templates/privacy_policy.html:408, notice:templates/privacy_policy.html:418, notice:templates/security.html:42, notice:templates/terms_of_service.html:67, notice:templates/terms_of_service.html:72, notice:templates/terms_of_service.html:149, notice:templates/terms_of_service.html:168, notice:templates/account/signup.html:105, notice:templates/account/signup.html:179, notice:templates/account/email/base_email.html:153, notice:templates/blog/blog_list.html:16, notice:templates/components/compare_plans_modal.html:14, notice:templates/components/cookie_consent.html:5, notice:templates/components/public_footer.html:12, notice:templates/email/subscription_expiry_reminder.html:19, notice:templates/email/welcome_email.html:32, notice:templates/expenses/capital_event_form.html:121, notice:templates/expenses/dpdp_consent.html:12, notice:templates/expenses/dpdp_consent.html:88, notice:templates/expenses/settings_home.html:416, notice:templates/expenses/settings_home.html:427, notice:templates/expenses/withdraw_consent_confirm.html:17, notice:templates/expenses/partials/_capital_event_list.html:327

templates/account/signup.html:130–130

```
                    <input type="hidden" name="consent_email" value="on">
```

templates/account/signup.html:143–143

```
                    <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/account/signup.html:156–156

```
                    <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:40–40

```
                <input type="hidden" name="consent_email" value="on">
```

templates/expenses/dpdp_consent.html:53–53

```
                <input class="form-check-input" type="checkbox" name="consent_transactions" id="id_consent_transactions" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/dpdp_consent.html:66–66

```
                <input class="form-check-input" type="checkbox" name="consent_device" id="id_consent_device" checked required style="width: 2.5em; height: 1.25em;">
```

templates/expenses/family/join.html:58–58

```
                <input class="form-check-input" type="checkbox" name="consent" id="fam-consent" required>
```

docs/index.html:215–218

```
            <p class="lead text-muted mb-5 mx-auto" style="max-width: 600px;">
                A self-hosted, simplified expense tracker built for privacy. 
                <br>No bank syncing. No SMS reading. Just you and your data.
            </p>
```

docs/index.html:2–2

```
<html lang="en" data-bs-theme="dark">
```

docs/index.html:241–241

```
                <p class="text-muted">Built for those who value privacy over convenience.</p>
```

templates/alternative_landing.html:210–212

```
                        <p class="text-muted mb-4" style="font-size: 15px;">
                            {% trans "Join thousands of privacy-conscious Indian professionals tracking their salaries securely and ad-free." %}
                        </p>
```

templates/alternatives_hub.html:58–58

```
                <p class="lead text-muted mb-4">{% trans "The right expense tracker depends on one trade-off: convenience or privacy. Here is how the main approaches differ, and what to check before you install anything." %}</p>
```

templates/landing_classic.html:1590–1592

```
                <p class="mx-auto mb-5" style="font-size: 19px; line-height: 1.6; color: var(--tmr-ink-600); max-width: 680px;">
                    {% trans "Track your net worth, double-entry ledger, investments, loans, and monthly cashflow in one privacy-first powerhouse. No bank passwords required. No SMS reading." %}
                </p>
```

templates/landing_classic.html:3–3

```
<html lang="en">
```

templates/privacy_policy.html:17–21

```
                    <p class="lead mb-4">
                        {% blocktrans %}
                        Your privacy matters to us. This policy explains how TrackMyRupee collects, uses, and protects your information.
                        {% endblocktrans %}
                    </p>
```

templates/privacy_policy.html:130–134

```
                        <p class="text-muted">
                            {% blocktrans %}
                            We always use a few strictly necessary cookies: your login session, CSRF protection, and a record of your cookie choice. Analytics cookies and scripts are used only if you click Accept on the cookie banner. If you decline, or have not chosen yet, the Google Analytics and PostHog scripts are not loaded, no analytics cookies are set, and no analytics events are sent from your browser or from our servers.
                            {% endblocktrans %}
                        </p>
```

templates/privacy_policy.html:136–140

```
                        <p class="text-muted">
                            {% blocktrans %}
                            Google Analytics uses cookies to collect information such as your IP address, browser type, device and the pages you visit, so we can understand how the site is used. We switch off Google's advertising features.
                            {% endblocktrans %}
                        </p>
```

templates/privacy_policy.html:141–146

```
                        <p class="text-muted">
                            {% blocktrans %}
                            You can also opt out of Google Analytics across all websites by installing the Google Analytics Opt-out Browser Add-on.
                            {% endblocktrans %}
                            <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener noreferrer">Google Analytics Opt-out Browser Add-on</a>.
                        </p>
```

templates/privacy_policy.html:154–158

```
                        <p class="text-muted">
                            {% blocktrans %}
                            You can change your choice at any time using the Cookie preferences link in the footer, or the button below. Declining removes the analytics cookies we set. Analytics data already collected is not deleted when you change your choice.
                            {% endblocktrans %}
                        </p>
```

templates/privacy_policy.html:262–262

```
                        <p class="text-muted small">{% trans "Where your data lives: the application runs in Bangalore and the database in Mumbai, both in India, so what you store in TrackMyRupee is kept and processed in India. Some supporting services run outside India, such as Brevo for email delivery, PostHog for analytics and Sentry for error monitoring (all in the United States), and each receives only what is listed in the table above." %}</p>
```

templates/privacy_policy.html:333–337

```
                        <p class="text-muted">
                            {% blocktrans %}
                            Under India's Digital Personal Data Protection Act 2023, you have the right to: (1) Access your personal data. (2) Correct inaccurate data. (3) Request erasure of your data. (4) Withdraw consent at any time by deleting your account from Settings -> My Data -> Delete Account. Withdrawal of consent will result in account termination as the service cannot be provided without processing your data. (5) File a complaint with the Data Protection Board of India at dpboard.gov.in.
                            {% endblocktrans %}
                        </p>
```

templates/privacy_policy.html:408–413

```
                        <p class="text-muted">
                            {% blocktrans %}
                            We may update this privacy policy from time to time. We will notify you of significant changes by posting the new policy on this page 
                            or sending you an email. Your continued use of the Service constitutes acceptance of the changes.
                            {% endblocktrans %}
                        </p>
```

templates/privacy_policy.html:418–423

```
                        <p class="text-muted mb-3">
                            {% blocktrans %}
                            If you have questions about this privacy policy or our practices, please contact us at:
                            {% endblocktrans %} <br>
                            <a href="mailto:support@trackmyrupee.com" class="fw-bold text-decoration-none">support@trackmyrupee.com</a>
                        </p>
```

templates/security.html:42–44

```
                                    <p class="text-muted mb-0 mt-3" style="line-height: 1.7;">
                                        {% trans "Our application servers run in Bangalore and our database in Mumbai, both in India, so what you store in TrackMyRupee is kept and processed in India. Emails, analytics and error reports go through providers outside India; the Privacy Policy lists exactly what each one receives." %}
                                    </p>
```

templates/terms_of_service.html:67–71

```
                        <p class="text-muted">
                            {% blocktrans %}
                            By using the Service, you grant us a limited, non-exclusive license to use your data only to provide the features of the Service to your account (for example, generating charts, forecasts, and reports for you). If you accept analytics cookies, we also collect product-usage events, such as which features are used, as described in the Privacy Policy. These events do not include your transaction descriptions or amounts. We never sell your data or use it for advertising.
                            {% endblocktrans %}
                        </p>
```

templates/terms_of_service.html:72–77

```
                        <p class="text-muted">
                            {% blocktrans %}
                            Your rights regarding your personal data are governed by India's Digital Personal Data Protection (DPDP) Act 2023. For details on how to exercise your rights (such as access, correction, erasure, and consent withdrawal), please refer to Section 6 of our
                            {% endblocktrans %}
                            <a href="{% url 'privacy-policy' %}#section-6" class="text-decoration-none fw-bold">{% trans "Privacy Policy" %}</a>.
                        </p>
```

templates/terms_of_service.html:149–153

```
                        <p class="text-muted">
                            {% blocktrans %}
                            You may not copy, modify, distribute, sell, or lease any part of our Service without our written consent.
                            {% endblocktrans %}
                        </p>
```

templates/terms_of_service.html:168–172

```
                        <p class="text-muted">
                            {% blocktrans %}
                            You may also delete your account at any time from your account settings. Upon deletion, your data is removed from our live systems immediately, as described in the Privacy Policy (including what we keep after deletion).
                            {% endblocktrans %}
                        </p>
```

templates/account/signup.html:105–107

```
            <p class="text-muted small">
                {% trans "Under India's DPDP Act, 2023, we ask for your consent. Please review the categories of personal data we collect. Toggling each is required to complete your registration." %}
            </p>
```

templates/account/signup.html:171–171

```
        <button class="btn-auth-primary mb-3" type="submit" id="btn_submit_consent">
```

templates/account/signup.html:179–181

```
        <p class="text-muted text-center mt-3 mb-0" style="font-size: 0.72rem;">
            {% trans "Consent policy v1.0 · Effective June 2026" %}
        </p>
```

templates/account/email/base_email.html:153–159

```
            <p class="footer-text">
                &copy; {% now "Y" %} TrackMyRupee. All rights reserved.<br>
                You received this email because you signed up for TrackMyRupee.<br>
                <a href="https://trackmyrupee.com/privacy-policy/" class="footer-link">{% trans "Privacy Policy" %}</a> • 
                <a href="https://trackmyrupee.com/terms-of-service/" class="footer-link">{% trans "Terms of Service" %}</a> •
                <a href="https://trackmyrupee.com/settings/profile/" class="footer-link">{% trans "Unsubscribe" %}</a>
            </p>
```

templates/blog/blog_list.html:16–18

```
        <p class="fs-5 text-body-secondary mb-4" style="max-width: 680px; line-height: 1.6;">
            {% trans "Practical personal finance insights, privacy-first expense tracking, debt management, and net worth growth, built for Indian salaried professionals." %}
        </p>
```

templates/components/compare_plans_modal.html:14–21

```
                <p class="text-muted lead mb-4">
                    {% if user.profile.is_plus %}
                        {% trans "Unlock Advanced Analytics & Forecasting with Pro." %}<br>
                    {% else %}
                        {% trans "You've reached the limit for categories on the Free plan." %}<br>
                    {% endif %}
                    <span class="text-primary fw-bold">{% trans "Unlock Premium features for just ₹49/month" %}</span>
                </p>
```

templates/components/cookie_consent.html:5–8

```
            <p class="mb-0 small">
                {% trans "With your permission, we use Google Analytics and PostHog cookies to measure site traffic and which features are used. If you decline, no analytics scripts or cookies are loaded and the site works the same. You can change this later from Cookie preferences in the footer." %}
                <a href="{% url 'privacy-policy' %}#section-3" class="text-white text-decoration-underline">{% trans "Privacy Policy" %}</a>.
            </p>
```

templates/components/public_footer.html:12–12

```
                    <p style="font-size: 14px; color: var(--tmr-ink-600); line-height: 1.6;">{% blocktrans %}A privacy-first personal finance system for Indian salaried professionals. Built by a founder in Pune, India.{% endblocktrans %}</p>
```

templates/email/subscription_expiry_reminder.html:19–21

```
    <p style="color: #6c757d; font-size: 14px;">
        {% trans "Renew your subscription now to continue enjoying unlimited categories, recurring transactions, automation, and advanced analytics." %}
    </p>
```

templates/email/welcome_email.html:32–32

```
        <p style="margin: 0 0 12px;">📅 <strong>Calendar and analytics:</strong> spending day by day, your savings rate, month-on-month trends and a financial health view.</p>
```

templates/expenses/capital_event_form.html:121–121

```
                            <p class="fw-semibold small mb-2 text-muted text-uppercase letter-spacing-1">{% trans "Analytics Flags" %}</p>
```

templates/expenses/dpdp_consent.html:12–14

```
    <p class="text-muted small">
        {% trans "To continue using TrackMyRupee, we require your explicit, informed consent for processing your personal details, as described in our Privacy Policy and India's DPDP Act, 2023." %}
    </p>
```

templates/expenses/dpdp_consent.html:88–90

```
    <p class="text-muted text-center mt-3 mb-0" style="font-size: 0.72rem;">
        {% trans "Consent policy v1.0 · Effective June 2026" %}
    </p>
```

templates/expenses/dpdp_consent.html:80–80

```
    <button class="btn btn-primary btn-xl w-100 mb-3 shadow-sm" type="submit" id="btn_submit_consent">
```

templates/expenses/settings_home.html:416–416

```
                    <p class="text-muted smaller mb-0">{% trans "Withdraw your data consent and request permanent account/data deletion." %}</p>
```

templates/expenses/settings_home.html:427–427

```
                    <p class="text-muted smaller mb-0">{% trans "Delete your account and your data. See the Privacy Policy for what we keep." %}</p>
```

templates/expenses/withdraw_consent_confirm.html:17–19

```
                <p class="text-muted mb-4">
                    {% trans "Under the Digital Personal Data Protection (DPDP) Act of India, you have the right to withdraw your consent to data processing at any time. Doing so will immediately delete your account, settings, and all recorded financial transactions from our live database, as described in the Privacy Policy." %}
                </p>
```

templates/expenses/partials/_capital_event_list.html:327–327

```
            <p class="text-muted">{% trans "Big purchases are large one-off payments (e.g. a home loan down payment) that are excluded from your regular analytics so they don't distort your monthly trends." %}</p>
```

### verifiable parental consent

Applicability: not determinable — The existing CHI-01 Gate did not resolve age/DOB collection or an explicit Child audience. Assessment: Not determinable: the CHI-01 Gate and a linked parental verification mechanism not established by the static inventory.

Issue Types: CHI-01

Linked identifiers: none

LLM reasoning: The Evidence shows a DPDP consent design that is partly in place but has clear gaps. Server-side enforcement is established. A redirect middleware is registered in settings and sends users without consent_granted to the dpdp_consent page. Every PostHog client.capture and client.identify call is checked with analytics_consent_given() before it runs. Specific consent is not met on either grant path (signup.html and dpdp_consent.html). The transactions and device toggles are pre-checked and required, and email consent is a hidden input fixed to "on". The signup notice also says toggling each item is required to register. So the user cannot choose per Purpose, and the only real actions are the age checkbox and the submit button. Each grant writes a ConsentEvent with user, action, a single generic purpose label, version, timestamp, IP and user agent. However, the record is flagged incomplete and is not linked to the itemised Purposes, so it is not determinable whether it is adequate proof. An itemised notice comes before the signup grant (before_grant true), but no notice resolved for the dpdp_consent path comes before its grant. For either path, the Evidence does not show that the notice covers how to withdraw consent, how to complain to the Board, or language options. Withdrawal is only possible by deleting the whole account. Neither the grant nor the withdrawal path has a resolved step count, so comparable ease cannot be judged. PostHog calls are gated against future processing, but erasing data already sent to the Data Processor is unresolved. The privacy policy itself says analytics data already collected is not deleted when the user changes their choice. Verifiable parental consent was not resolved, and only an age self-declaration was found.; cache key: 10dfd58cd1c73370f7dd436a83cb80faab23cb238520d8fd484039d2dfb42af8

LLM reasoning citations: DPDP-Act-4(1) — Section 4(1), DPDP-Act-4 — Section 4, DPDP-Act-5(1) — Section 5(1), DPDP-Act-5 — Section 5, DPDP-Act-5(3) — Section 5(3), DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6, DPDP-Act-6(3) — Section 6(3), DPDP-Act-6(4) — Section 6(4), DPDP-Act-6(6) — Section 6(6), DPDP-Act-6(10) — Section 6(10), DPDP-Act-8(7) — Section 8(7), DPDP-Act-8(7)(b) — Section 8(7)(b), DPDP-Act-8 — Section 8, DPDP-Rule-3 — Rule 3, DPDP-Rule-3(a) — Rule 3(a), DPDP-Rule-3(b) — Rule 3(b), DPDP-Rule-3(c) — Rule 3(c), DPDP-Rule-3(c)(i) — Rule 3(c)(i)

LLM reading — recorded: not determinable. ConsentEvent records are created on both grant paths (expenses/forms.py:911 'Signup Data Collection' and expenses/views/misc.py:448 'Terms and Data Collection'). They store user, action, consent_version, timestamp, ip_address and user_agent. Every record is flagged complete=false and has no linked purpose_ids. Each one uses a single generic purpose label rather than the three itemised Purposes, and does not capture choices per control. The account-deletion withdrawal path does not show a WITHDRAWN record; such records appear only for family household flows. So the Evidence does not establish whether these records are enough to prove notice and consent.

LLM reading citations: DPDP-Act-6(10) — Section 6(10)

LLM reading — specific: not met. On both signup.html and dpdp_consent.html, consent_transactions and consent_device are pre-checked and required (default_selected true), and consent_email is a hidden input with value="on" that the user never sees or controls. The signup notice says 'Toggling each is required to complete your registration.' The user therefore cannot give or refuse consent for each Purpose separately. The only affirmative actions are confirm_age and submit, which does not meet the standard of specific, unconditional consent given by a clear affirmative action for each specified Purpose.

LLM reading citations: DPDP-Act-6(1) — Section 6(1), DPDP-Act-6 — Section 6, DPDP-Act-4(1) — Section 4(1)

LLM reading — enforced server-side: met. DPDPAConsentMiddleware is registered in finance_tracker/settings.py:146. It redirects to dpdp_consent when profile.consent_granted is false (expenses/middleware.py:147-148). PostHog capture and identify are each preceded by a server-side analytics_consent_given() check (expenses/posthog_utils.py:108 and 125). All of these enforcement points are flagged server_side=true.

LLM reading citations: DPDP-Act-4(1) — Section 4(1), DPDP-Act-4 — Section 4

LLM reading — withdrawable with comparable ease: not determinable. Withdrawal happens through WithdrawConsentView (settings/consent/withdraw/), a single form submit that deletes the account. Withdrawing per Purpose is not possible. Both the grant and withdrawal paths have start_template and step_count set to null, and step counts cannot be compared without a common, statically resolved starting point. Comparable ease therefore cannot be established.

LLM reading citations: DPDP-Act-6(4) — Section 6(4), DPDP-Rule-3(c)(i) — Rule 3(c)(i)

LLM reading — propagated to Data Processors: not determinable. Future calls to the PostHog Data Processor (client.capture and client.identify) are gated server-side by a consent check. The processor_propagation state, however, records that earlier transfers and deletion are unresolved. Calling dispatch_account_deletion does not prove that any processor erasure happened. The privacy policy notice (templates/privacy_policy.html:154) states that 'Analytics data already collected is not deleted when you change your choice.' That points to a possible gap in causing the Data Processor to stop processing or erase, but the Evidence does not show what happens when the account is deleted.

LLM reading citations: DPDP-Act-6(6) — Section 6(6), DPDP-Act-8(7)(b) — Section 8(7)(b), DPDP-Act-8(7) — Section 8(7), DPDP-Act-8 — Section 8

LLM reading — preceded by notice: not determinable. On signup, an itemised notice (templates/account/signup.html:105, before_grant true) with linked Purposes appears before the submit button. On the dpdp_consent path, the general notice (line 12) has before_grant null, and the version notice (line 88) has before_grant false. Neither linked notice is shown to state how to withdraw consent, how to exercise rights, or how to complain to the Board. That information appears only in the privacy policy (notice 333), whose before_grant is null and which is not linked to the grant. No option to read the notice in English or an Eighth Schedule language is established (language null).

LLM reading citations: DPDP-Act-5(1) — Section 5(1), DPDP-Act-5 — Section 5, DPDP-Act-5(3) — Section 5(3), DPDP-Act-6(3) — Section 6(3), DPDP-Rule-3 — Rule 3, DPDP-Rule-3(a) — Rule 3(a), DPDP-Rule-3(b) — Rule 3(b), DPDP-Rule-3(c) — Rule 3(c)

LLM reading — verifiable parental consent: not determinable. Both the child gate and the parental verification are in state 'not determinable'. The only related evidence is a required confirm_age self-declaration checkbox (age 18 or older, not stored) on both grant paths. No mechanism for verifiable parental consent was found, and whether the audience includes children, or whether age or date of birth is collected, was not established.

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
| DPDP-Act-6 | Section 6 | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-04-django-comparable-paths, CON-04-express-withdrawal-path, CON-05-express-processor-withdrawal, CON-06-django-incomplete-record, CON-06-sequelize-consent-record, CON-07-angular-consent-notice, CON-07-django-unitemised-notice, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation |
| DPDP-Act-6(1) | Section 6(1) | not determinable | CON-01-express-enforcement, CON-02-angular-bundled-purposes, CON-03-angular-default-true, CON-03-django-default-selected, CON-08-angular-excess-elements, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation |
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
| DPDP-Act-8 | Section 8 | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-01-sequelize-soft-delete, RET-02-express-erasure-request, RIG-03-express-grievance, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(1) | Section 8(1) | not code-checkable | none |
| DPDP-Act-8(2) | Section 8(2) | not code-checkable | TRF-01-undisclosed-processor-transfer |
| DPDP-Act-8(3) | Section 8(3) | not code-checkable | none |
| DPDP-Act-8(3)(a) | Section 8(3)(a) | not code-checkable | none |
| DPDP-Act-8(3)(b) | Section 8(3)(b) | not code-checkable | none |
| DPDP-Act-8(4) | Section 8(4) | not code-checkable | none |
| DPDP-Act-8(5) | Section 8(5) | not code-checkable | none |
| DPDP-Act-8(6) | Section 8(6) | not code-checkable | none |
| DPDP-Act-8(7) | Section 8(7) | not determinable | CON-05-express-processor-withdrawal, RET-01-express-purpose-end, RET-01-sequelize-soft-delete, RET-02-express-erasure-request |
| DPDP-Act-8(7)(a) | Section 8(7)(a) | not determinable | RET-01-express-purpose-end, RET-01-sequelize-soft-delete |
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
| DPDP-Act-11(1)(a) | Section 11(1)(a) | not determinable | RIG-01-express-incomplete-export |
| DPDP-Act-11(1)(b) | Section 11(1)(b) | not determinable | RIG-01-express-incomplete-export, TRF-01-undisclosed-processor-transfer |
| DPDP-Act-11(1)(c) | Section 11(1)(c) | not code-checkable | none |
| DPDP-Act-11(2) | Section 11(2) | not code-checkable | none |
| DPDP-Act-12 | Section 12 | not determinable | RET-02-express-erasure-request, RIG-02-express-email-correction |
| DPDP-Act-12(1) | Section 12(1) | not code-checkable | none |
| DPDP-Act-12(2) | Section 12(2) | not determinable | RIG-02-express-email-correction |
| DPDP-Act-12(2)(a) | Section 12(2)(a) | not code-checkable | none |
| DPDP-Act-12(2)(b) | Section 12(2)(b) | not code-checkable | none |
| DPDP-Act-12(2)(c) | Section 12(2)(c) | not code-checkable | none |
| DPDP-Act-12(3) | Section 12(3) | not determinable | RET-02-express-erasure-request |
| DPDP-Act-13 | Section 13 | not determinable | RIG-03-express-grievance |
| DPDP-Act-13(1) | Section 13(1) | not code-checkable | none |
| DPDP-Act-13(2) | Section 13(2) | not code-checkable | none |
| DPDP-Act-13(3) | Section 13(3) | not code-checkable | none |
| DPDP-Act-14 | Section 14 | static | RIG-04-rights-notice |
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
| DPDP-Rule-6 | Rule 6 | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1) | Rule 6(1) | not determinable | MON-01-monitoring-coverage, SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-12-express-access-logging, SEC-13-ts-access-log-retention, SEC-14-terraform-store-backup, SEC-15-committed-personal-data, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(a) | Rule 6(1)(a) | not determinable | SEC-01-nginx-query-logging, SEC-01-ts-morgan-query-secrets, SEC-02-django-plain-fields, SEC-02-sequelize-plain-fields, SEC-03-django-aadhaar-storage, SEC-03-fastapi-aadhaar-response, SEC-03-sequelize-aadhaar-storage, SEC-04-ts-constant-key-verifier, SEC-04-ts-md5-credential-compare, SEC-04-ts-md5-password-hash, SEC-09-ts-query-authentication-secret, SEC-09-ts-query-personal-data, SEC-10-ts-storage-header, SEC-10-ts-token-storage-site, SEC-11-fastapi-wildcard-cors, SEC-11-terraform-plaintext-listener, SEC-11-ts-jsonp-response, SEC-11-ts-session-cookie-flags, SEC-11-ts-wildcard-cors, SEC-15-committed-personal-data |
| DPDP-Rule-6(1)(b) | Rule 6(1)(b) | static | SEC-05-ts-hardcoded-hmac-key, SEC-05-ts-hardcoded-jwt-key, SEC-06-express-error-disclosure, SEC-07-ts-lossy-owner-key, SEC-07-ts-public-personal-data-directory, SEC-07-ts-unauthenticated-record-read, SEC-07-ts-unchecked-nested-records, SEC-07-ts-unscoped-authenticated-read, SEC-08-ts-account-list, SEC-08-ts-nested-records, SEC-08-ts-review-author, SEC-08-ts-whole-model-serialisation, SEC-16-docker-root-container, SEC-16-kubernetes-privileged-store, SEC-16-kubernetes-public-store, SEC-16-terraform-public-storage, SEC-16-terraform-public-store |
| DPDP-Rule-6(1)(c) | Rule 6(1)(c) | not determinable | MON-01-monitoring-coverage, SEC-12-express-access-logging |
| DPDP-Rule-6(1)(d) | Rule 6(1)(d) | not determinable | SEC-14-terraform-store-backup |
| DPDP-Rule-6(1)(e) | Rule 6(1)(e) | not determinable | SEC-13-ts-access-log-retention |
| DPDP-Rule-6(1)(f) | Rule 6(1)(f) | not code-checkable | none |
| DPDP-Rule-6(1)(g) | Rule 6(1)(g) | not code-checkable | none |
| DPDP-Rule-6(2) | Rule 6(2) | not code-checkable | none |
| DPDP-Rule-7 | Rule 7 | not code-checkable | none |
| DPDP-Rule-7(1) | Rule 7(1) | not code-checkable | none |
| DPDP-Rule-7(2) | Rule 7(2) | not code-checkable | none |
| DPDP-Rule-8 | Rule 8 | not determinable | RET-03-express-erasure-notice, SEC-13-ts-access-log-retention |
| DPDP-Rule-8(1) | Rule 8(1) | not determinable | RET-03-express-erasure-notice |
| DPDP-Rule-8(2) | Rule 8(2) | not determinable | RET-03-express-erasure-notice |
| DPDP-Rule-8(3) | Rule 8(3) | not determinable | SEC-13-ts-access-log-retention |
| DPDP-Rule-9 | Rule 9 | not determinable | RIG-03-express-grievance |
| DPDP-Rule-10 | Rule 10 | not determinable; covered, not exercised on a real Target | CHI-01-age-parental-consent |
| DPDP-Rule-11 | Rule 11 | not code-checkable | none |
| DPDP-Rule-12 | Rule 12 | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rule-13 | Rule 13 | static | TRF-02-terraform-storage-region |
| DPDP-Rule-13(4) | Rule 13(4) | static | TRF-02-terraform-storage-region |
| DPDP-Rule-14 | Rule 14 | not determinable | RIG-01-express-incomplete-export, RIG-02-express-email-correction, RIG-03-express-grievance, RIG-04-rights-notice |
| DPDP-Rule-14(3) | Rule 14(3) | not determinable | RIG-03-express-grievance |
| DPDP-Rule-14(4) | Rule 14(4) | static | RIG-04-rights-notice |
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
| DPDP-Rules-Schedule-Third | Third Schedule | not determinable | RET-03-express-erasure-notice |
| DPDP-Rules-Schedule-Fourth | Fourth Schedule | not determinable; covered, not exercised on a real Target | CHI-02-child-tracking |
| DPDP-Rules-Schedule-Fifth | Fifth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Sixth | Sixth Schedule | not code-checkable | none |
| DPDP-Rules-Schedule-Seventh | Seventh Schedule | not code-checkable | none |

## Statutory Penalty Ceilings and Enforcement Timeline

Statutory maximum per Schedule; not a predicted or estimated fine. The actual penalty is determined by the Data Protection Board under section 33(2) factors. Ceilings apply per breach instance and are never added together. Under the Report's Applicability Assumptions, only applicable Primary Provisions contribute to the highest ceiling. Related and conditional Provisions and Findings that need legal review do not contribute.

Highest applicable ceiling: ₹50 crore (DPDP-Act-14, DPDP-Act-6(1)). Ceilings are not summed into a total exposure figure.

| Provision | Schedule entry | Statutory maximum | Finding applicability | Severity mix |
| --- | --- | --- | --- | --- |
| DPDP-Act-14 | Schedule, item 7 | ₹50 crore | Applicable Primary Provision: RIG-04-91983d63d6a4 | low: 1 |
| DPDP-Act-6(1) | Schedule, item 7 | ₹50 crore | Applicable Primary Provision: CON-03-5948c3734746, CON-03-94c021251539, CON-03-c8163452354e, CON-03-e9015c2df7d8 | low: 4 |
| DPDP-Rule-14(4) | Schedule, item 7 | ₹50 crore | Related Provision: RIG-04-91983d63d6a4 | low: 1 |

### Enforcement timeline (days relative to scan date 2026-11-23)

| Enforceable From | Status | Findings |
| --- | --- | --- |
| 2027-05-13 | enforceable in 171 days | CON-03-5948c3734746, CON-03-94c021251539, CON-03-c8163452354e, CON-03-e9015c2df7d8, RIG-04-91983d63d6a4 |

## Method, accuracy and limitations

Static Rules use Semgrep, TypeScript AST and configuration analysers. Cache-only mode replays matching cached LLM fields; uncached fields are not assessed. Live Probe outcomes, when available, appear with their Findings.

| Method | Value |
| --- | --- |
| Target Application | trackmyrupee |
| Target revision | 47990e4f19d7debea70c5d56bab77e3c3f051546 |
| Target source | targets/trackmyrupee |
| Exclusions | **/.git/**, **/node_modules/**, expenses/tests/**, **/__pycache__/**, **/*.pyc |
| Files scanned | 1676 |
| Files excluded | 290 |
| Rule count | 65 |
| LLM provider | omp |
| LLM model | anthropic/claude-opus-5-5 |
| Prompt versions | classification: classification-v1, triage: triage-v2, consent: consent-v2, fix: fix-v1 |
| LLM mode | cache-only |
| Cache hits | 30 |
| Cache misses | 0 |
| LLM fields not assessed | 0 |
| Cache-only reason | forced offline for artifact regeneration |
