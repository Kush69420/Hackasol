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
