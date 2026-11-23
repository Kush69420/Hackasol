"""Deterministic evaluations of already observed, value-free behaviours."""
from http.cookies import SimpleCookie, CookieError
from urllib.parse import urlsplit
import ipaddress


def cookie_flags(headers) -> tuple[str, str]:
    """Assess only known session cookies; never retain cookie names or values."""
    seen = []
    try:
        for header in headers:
            jar = SimpleCookie()
            jar.load(header)
            for name, cookie in jar.items():
                if name.lower() in {"token", "session", "sessionid", "connect.sid"}:
                    seen.append(bool(cookie['secure']) and bool(cookie['httponly']))
    except CookieError:
        return 'inconclusive', 'Session cookie flags could not be parsed'
    if not seen:
        return 'inconclusive', 'No session cookie was issued by this response'
    return ('Refuted', 'The observed session cookie had Secure and HttpOnly') if all(seen) else ('Confirmed', 'An observed session cookie lacked Secure or HttpOnly')


def transport(target: str) -> tuple[str, str]:
    """Do not draw conclusions about production transport from loopback."""
    url = urlsplit(target)
    try:
        loopback = ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        loopback = url.hostname == 'localhost'
    if loopback:
        return 'inconclusive', 'Loopback transport does not establish production transport posture'
    if url.scheme == 'https':
        return 'Refuted', 'The observed instance used TLS; production posture is not inferred'
    return 'Confirmed', 'The observed non-loopback instance used HTTP; production posture is not inferred'


def consent_enforcement(before: bool | None, after: bool | None) -> tuple[str, str]:
    """The preselected Processing Operation must work before withdrawal."""
    if before is not True or after is None:
        return 'inconclusive', 'Grant, withdrawal or pre-withdrawal operation was not established'
    if after:
        return 'Confirmed', 'The Processing Operation remained available after withdrawal'
    return 'Refuted', 'The Processing Operation was unavailable after withdrawal'


def comparable_ease(grant: int | None, withdrawal: int | None) -> tuple[str, str]:
    """Compare recorded interaction counts for the same Purpose and convention."""
    if grant is None or withdrawal is None or grant < 0 or withdrawal < 0:
        return 'inconclusive', 'Comparable grant and withdrawal interactions were not both recorded'
    if withdrawal > grant:
        return 'Confirmed', f'Withdrawal required {withdrawal} interactions; grant required {grant}'
    return 'Refuted', f'Withdrawal required {withdrawal} interactions; grant required {grant}'


def declined_signup(control_created: bool | None, declined_created: bool | None, declined_rejected: bool | None) -> tuple[str, str]:
    """A declined Purpose must not yield an account that processes its Personal Data.

    The control (every consent supplied) must succeed, otherwise a rejection could have
    any cause. Confirmed needs a created account; Refuted needs an observed rejection."""
    if control_created is not True:
        return 'inconclusive', 'The control signup with every consent supplied was not established, so a rejection cannot be attributed to the declined Purpose'
    if declined_created is True:
        return 'Confirmed', 'An account was created although this consent was declined'
    if declined_rejected is True:
        return 'Refuted', 'Signup with this consent declined was rejected, so the Purpose is enforced at signup (it is mandatory rather than optional)'
    return 'inconclusive', 'Neither account creation nor a form rejection was observed for the declined signup'


def declined_processing(control_hits: int | None, observed_hits: int | None) -> tuple[str, str]:
    """Observed outbound processing after a declined or withdrawn Purpose.

    Both actions must succeed and be observable before comparing counts. Silence
    is meaningful only when granted consent produced an event on the same channel."""
    if observed_hits is None or control_hits is None:
        return 'inconclusive', 'A comparable login failed or the scoped outbound observation was unavailable'
    if observed_hits > 0:
        return 'Confirmed', f'{observed_hits} outbound event(s) were observed after the decline or withdrawal'
    if control_hits <= 0:
        return 'inconclusive', 'No outbound event was observed under granted consent, so silence after the decline is not evidence of enforcement'
    return 'Refuted', f'No outbound event was observed after the decline or withdrawal while the granted control produced {control_hits}'


def withdrawal_data(authenticates: bool | None, rows_remaining: int | None) -> tuple[str, str]:
    """Withdrawal must stop processing: the account no longer works and its rows are gone.

    Failed authentication alone is not erasure; a read-only row count is required."""
    if authenticates is True:
        return 'Confirmed', 'The Auditor-created account still authenticated after withdrawal'
    if rows_remaining is not None and rows_remaining > 0:
        return 'Confirmed', f'{rows_remaining} account-linked row(s) remained after withdrawal'
    if authenticates is False and rows_remaining == 0:
        return 'Refuted', 'The account no longer authenticated and no account-linked rows remained'
    return 'inconclusive', 'Both post-withdrawal authentication and a read-only row count are required; one was not observed'


TRI_STATE = {'Confirmed': 'Confirmed', 'Refuted': 'Not Confirmed'}
TRI_STATE_MEANING = {
    'Confirmed': 'violation observed',
    'Not Confirmed': 'enforcement observed',
    'Inconclusive': 'not run or inconclusive; no effect on the static verdict',
}


def tri_state(result: str) -> str:
    """Live Probe presentation: Refuted is reported as Not Confirmed, anything unobserved as Inconclusive."""
    return TRI_STATE.get(result, 'Inconclusive')
