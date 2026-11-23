"""Mask Authentication Secrets and Personal Data without changing line anchors."""
import ipaddress
import re

_D = ((0,1,2,3,4,5,6,7,8,9),(1,2,3,4,0,6,7,8,9,5),(2,3,4,0,1,7,8,9,5,6),(3,4,0,1,2,8,9,5,6,7),(4,0,1,2,3,9,5,6,7,8),(5,9,8,7,6,0,4,3,2,1),(6,5,9,8,7,1,0,4,3,2),(7,6,5,9,8,2,1,0,4,3),(8,7,6,5,9,3,2,1,0,4),(9,8,7,6,5,4,3,2,1,0))
_P = ((0,1,2,3,4,5,6,7,8,9),(1,5,7,6,2,8,3,0,9,4),(5,8,0,3,7,9,6,1,4,2),(8,9,1,6,0,4,3,5,2,7),(9,4,5,3,1,2,6,8,7,0),(4,2,8,6,5,7,3,9,0,1),(2,7,9,3,8,0,6,4,1,5),(7,0,4,6,9,1,3,2,5,8))


def _aadhaar(value):
    digits = re.sub(r'\D', '', value)
    c = 0
    for i, digit in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(digit)]]
    return c == 0


def _luhn(value):
    digits = re.sub(r'\D', '', value)
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, digit in enumerate(reversed(digits)):
        n = int(digit) * (2 if i % 2 else 1)
        total += n // 10 + n % 10
    return total % 10 == 0


def _sub(text, pattern, label, flags=0, predicate=None):
    def replace(m):
        if predicate and not predicate(m.group()):
            return m.group()
        return f'«{label}»' + '\n' * m.group().count('\n')
    return re.sub(pattern, replace, text, flags=flags)


def _mask(text: str, *, egress: bool) -> str:
    text = _sub(text, r'data:image/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+', 'BIOMETRIC_PAYLOAD', re.I)
    text = _sub(text, r'(?<![A-Za-z0-9+/=])[A-Za-z0-9+/=]{200,}(?![A-Za-z0-9+/=])', 'BINARY')
    text = _sub(text, r'-----BEGIN [^-\n]*PRIVATE KEY-----[\s\S]*?-----END [^-\n]*PRIVATE KEY-----', 'SECRET')
    text = _sub(text, r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', 'SECRET')
    text = _sub(text, r'\bAKIA[0-9A-Z]{16}\b|\bBearer[ \t]+[A-Za-z0-9._~+/=-]+', 'SECRET', re.I)
    # Replace the complete assignment, including quoted values with spaces.
    text = _sub(text, r'''\b(?:[\w-]*(?:password|passwd|secret|token|api[_-]?key|private[_ -]?key)[\w-]*)["']?\s*[:=]\s*(?:"[^"\n]*"|'[^'\n]*'|[^\s,;})]+)''', 'SECRET', re.I)
    text = _sub(text, r'''(?<=[=:])[ \t]*["']?[A-Za-z0-9+/=_-]{32,}["']?''', 'SECRET')
    text = _sub(text, r'(?<!\d)\d{2}-\d{4}-\d{4}-\d{4}(?!\d)', 'ABHA')
    text = _sub(text, r'(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)', 'AADHAAR', predicate=_aadhaar)
    text = _sub(text, r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', 'PAN')
    text = _sub(text, r'\b[A-PR-WY][1-9]\d ?\d{4}[1-9]\b', 'PASSPORT')
    text = _sub(text, r'\b[A-Z]{3}\d{7}\b', 'VOTER_ID')
    text = _sub(text, r'\b[A-Z]{2}[ -]?\d{2}[ -]?(?:19|20)?\d{2}[ -]?\d{7}\b', 'DRIVING_LICENCE')
    if egress:
        text = _sub(text, r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', 'EMAIL')
        text = _sub(text, r'\b[A-Za-z0-9._-]+@[A-Za-z][A-Za-z0-9.-]*\b', 'UPI')
        text = _sub(text, r'\b[A-Z]{4}0[A-Z0-9]{6}\b', 'IFSC')
        text = _sub(text, r'(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)', 'CARD', predicate=_luhn)
        text = _sub(text, r'(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)', 'PHONE')
        text = _sub(text, r'(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w:])', 'IP', predicate=lambda s: _ip(s))
        text = _sub(text, r'(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])', 'IP', predicate=lambda s: _ip(s))
    return text


def _ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def mask_for_egress(text: str) -> str:
    return _mask(text, egress=True)


def mask_for_report(text: str) -> str:
    return _mask(text, egress=False)
