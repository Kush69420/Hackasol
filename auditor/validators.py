"""Format signals for Personal Data Elements; a format alone is not identity."""
import ipaddress
import re

from auditor.masking import _aadhaar, _luhn


def is_email(value):
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value))


def is_card(value):
    return isinstance(value, str) and bool(re.fullmatch(r'\d(?:[ -]?\d){12,18}', value)) and _luhn(value)


def is_indian_phone(value):
    return isinstance(value, str) and bool(re.fullmatch(r'(?:\+91[ -]?)?[6-9]\d{9}', value))


def is_ip(value):
    try:
        if not isinstance(value, str):
            return False
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def is_aadhaar(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}', value)) and _aadhaar(value)


def is_pan(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Z]{5}[0-9]{4}[A-Z]', value))


def is_ifsc(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Z]{4}0[A-Z0-9]{6}', value))


def is_vpa(value):
    return isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{1,255}@[A-Za-z][A-Za-z0-9.-]{1,63}', value))
