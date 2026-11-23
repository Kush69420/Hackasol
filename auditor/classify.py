"""Extract and classify Personal Data Elements from the structured inventory.

Generic names and location fields need Data Principal context: only the listed
models (and their plural table names) are treated as such. This avoids treating
Product.name or Product.zip as information about an individual. Specific names
such as email or Aadhaar can identify an Element outside those models.
"""
from __future__ import annotations

import re

from auditor.masking import mask_for_egress
from auditor import validators


NAME_DICTIONARY = {
    **dict.fromkeys(('aadhaar', 'aadhar', 'adhaar', 'uid_number', 'pan', 'pan_no', 'pancard', 'passport', 'voter', 'epic', 'driving_licence', 'driving_license', 'dl_no', 'abha', 'health_id'), 'Government Identifier'),
    **dict.fromkeys(('fingerprint', 'face', 'iris', 'biometric'), 'Biometric'),
    **dict.fromkeys(('card_num', 'card_number', 'cardnum', 'exp_month', 'exp_year', 'wallet', 'balance', 'ifsc', 'upi', 'vpa', 'account_no', 'khata'), 'Financial'),
    **dict.fromkeys(('diagnosis', 'blood_group', 'health'), 'Health'),
    **dict.fromkeys(('password', 'passwd', 'token', 'otp', 'totp', 'secret', 'security_answer', 'authorization'), 'Authentication Secret'),
    **dict.fromkeys(('email', 'mobile', 'phone', 'phone_no', 'mobile_no', 'mobile_num', 'address', 'street_address', 'pata', 'zip', 'zip_code', 'city', 'state', 'country'), 'Contact'),
    **dict.fromkeys(('name', 'full_name', 'naam', 'username', 'author', 'profile_image', 'ip', 'janam_tithi', 'dob', 'date_of_birth'), 'Profile'),
}

_CATEGORIES = set(NAME_DICTIONARY.values()) | {'Child Data'}
_PRINCIPAL_MODELS = {'user', 'address', 'card', 'wallet', 'securityanswer', 'privacyrequest', 'memory', 'feedback', 'complaint', 'basket'}
_CONTEXTUAL = {'name', 'full_name', 'naam', 'zip', 'zip_code', 'city', 'state', 'country', 'balance', 'face', 'answer', 'exp_month', 'exp_year'}
_VALIDATORS = ((validators.is_email, 'Contact', 'email'), (validators.is_card, 'Financial', 'card'),
               (validators.is_indian_phone, 'Contact', 'phone'), (validators.is_ip, 'Profile', 'ip'),
               (validators.is_aadhaar, 'Government Identifier', 'aadhaar'), (validators.is_pan, 'Government Identifier', 'pan'),
               (validators.is_ifsc, 'Financial', 'ifsc'), (validators.is_vpa, 'Financial', 'vpa'))


def _normalise(value):
    value = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', str(value))
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
    return re.sub(r'[^a-z0-9]+', '_', value.lower()).strip('_')


def _principal(model):
    name = _normalise(model or '').replace('_', '')
    return name in _PRINCIPAL_MODELS or (name.endswith('s') and name[:-1] in _PRINCIPAL_MODELS)


def _match(text, contextual):
    normalized = _normalise(text)
    tokens = normalized.split('_')
    # Prefer the longest matching phrase over a component such as health in health_id.
    for key in sorted(NAME_DICTIONARY, key=lambda item: len(item.split('_')), reverse=True):
        parts = key.split('_')
        if key in _CONTEXTUAL and not contextual:
            continue
        if any(tokens[i:i + len(parts)] == parts for i in range(len(tokens) - len(parts) + 1)):
            return key, NAME_DICTIONARY[key]
    return None, None


def _element(identity, name, kind, source, *, model=None, field=None, detail=None, contextual=False):
    if not name or not isinstance(source, dict) or not source.get('file'):
        return None
    detail = detail or {}
    contextual = contextual or _principal(model)
    key, category = _match(name, contextual)
    signals = [f'name:{key}'] if key else []
    if not category and contextual and _normalise(name) == 'answer' and 'security' in _normalise(model or ''):
        category = 'Authentication Secret'
        signals.append('model:security-answer')
    for label_key in ('label', 'i18n_key'):
        if detail.get(label_key):
            label_match, label_category = _match(detail[label_key], contextual)
            if label_match:
                signals.append(f'{label_key}:{label_match}')
                if not category:
                    category = label_category
    # "face" alone (a face image upload, a face-match score) does not establish biometric processing;
    # it needs processing evidence. Explicit biometric terms (fingerprint, iris, biometric) still classify.
    if category == 'Biometric' and not re.search(r'fingerprint|iris|biometric', _normalise(name)):
        category = None
    if re.search(r'(?:face_match|liveness).*score|score.*(?:face_match|liveness)', _normalise(name)):
        category = 'Profile'
        signals.append('derived:verification-score')
    elif detail.get('biometric_evidence'):
        category = 'Biometric'
        signals.append('processing:biometric')
    if detail.get('government_identifier_evidence'):
        category = 'Government Identifier'
        signals.append('choices:government-identifier')
    input_type = str(detail.get('input_type') or '').lower()
    if input_type in ('email', 'password', 'tel'):
        signals.append(f'input_type:{input_type}')
        if not category:
            category = {'email': 'Contact', 'password': 'Authentication Secret', 'tel': 'Contact'}[input_type]
    schema_type = detail.get('type')
    if schema_type:
        signals.append(f'schema_type:{schema_type}')
    for validator in detail.get('validators') or []:
        signals.append(f'schema_validator:{validator}')
    if _normalise(name) in ('dob', 'date_of_birth', 'janam_tithi'):
        signals.append('possible Child Data')
    for value_key in ('default', 'example', 'value'):
        value = detail.get(value_key)
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        for validate, value_category, format_name in _VALIDATORS:
            if validate(str(value)):
                signals.append(f'{value_key}_format:{format_name}')
                if not category and contextual:
                    category = value_category
                break
    # Unknowns are retained only where there is a concrete reason to consider
    # them person-related, rather than sending every model field to the LLM.
    candidate = contextual and _normalise(name) not in {'id', 'user_id', 'userid'} or bool(re.search(r'(^|_)(person|personal|customer|user|profile|birth)(_|$)', _normalise(name)))
    if not category and not candidate:
        return None
    signals.append(f'kind:{kind}')
    return {'id': identity, 'name': name, 'kind': kind, 'data_category': category,
            'status': 'deterministic' if category else 'unresolved', 'signals': signals,
            'llm': None, 'source': source, 'model': model, 'field': field}


def extract_elements(inventory):
    """Return independently identified Elements, preserving inventory coordinates."""
    elements = []
    seen = set()

    def add(item):
        if item and item['id'] not in seen:
            seen.add(item['id'])
            elements.append(item)

    for model in inventory.get('models', []):
        model_name = model.get('name') or model.get('table')
        for field in model.get('fields', []):
            name = field.get('name')
            add(_element(f'model:{model_name}.{name}', name, 'model-field', field.get('source'), model=model_name, field=name, detail=field, contextual=_principal(model.get('table'))))
    for collection in inventory.get('collections', []):
        model_name = collection.get('name', '')
        for field in collection.get('fields', []):
            name = field.get('name')
            add(_element(f'collection:{model_name}.{name}', name, 'collection-field', field.get('source'), model=model_name, field=name, detail=field))
    for form in [*inventory.get('forms', []), *inventory.get('templates', [])]:
        for field in form.get('inputs', []):
            name, source = field.get('name'), field.get('source') or form.get('source')
            file = (source or {}).get('file', form.get('file', ''))
            add(_element(f'form:{file}#{name}', name, 'form-input', source, field=name, detail=field, contextual=True))
    for route in inventory.get('routes', []):
        path = route.get('normalised_path') or route.get('path') or ''
        method = route.get('method', '')
        source = route.get('registration') or route.get('source')
        for name in re.findall(r'\{([^{}]+)\}|:([A-Za-z_][\w]*)', path.split('?')[0]):
            name = name[0] or name[1]
            add(_element(f'param:{method} {path}#{name}', name, 'route-param', source, field=name))
        params = list(route.get('query_params') or [])
        params += list((route.get('swagger') or {}).get('parameters') or [])
        for param in params:
            if isinstance(param, str):
                param = {'name': param, 'in': 'query'}
            if param.get('in', 'query') != 'query':
                continue
            name = param.get('name')
            detail = dict(param)
            # A query parameter called current/new on a password route has a
            # clear route-level name signal, not an inferred code operation.
            if _match(path, False)[1] == 'Authentication Secret':
                detail['label'] = path
            add(_element(f'param:{method} {path}?{name}', name, 'route-param', param.get('source') or source, field=name, detail=detail))
        for param in route.get('body_params') or []:
            if isinstance(param, str):
                param = {'name': param}
            name = param.get('name')
            detail = dict(param)
            if _match(path, False)[1] == 'Authentication Secret':
                detail['label'] = path
            add(_element(f'param:{method} {path}#body.{name}', name, 'route-param',
                         param.get('source') or source, field=name, detail=detail))
    for item in inventory.get('client_storage', []):
        name = item.get('key')
        add(_element(f"storage:{item.get('api')}.{name}", name, 'storage-key', item.get('source'), field=name, detail=item))
    for item in inventory.get('outbound_headers', []):
        name = item.get('header')
        add(_element(f'header:{name}', name, 'header', item.get('source'), field=name, detail=item))

    def config_records(node, inherited_source=None, prefix=''):
        if isinstance(node, list):
            for child in node:
                yield from config_records(child, inherited_source, prefix)
        elif isinstance(node, dict):
            source = node.get('source') or inherited_source
            name = node.get('key') or node.get('name')
            if isinstance(name, str) and source:
                yield name, source, node
            for key, child in node.items():
                if isinstance(child, (dict, list)) and key not in ('source', 'sources'):
                    yield from config_records(child, source, f'{prefix}.{key}' if prefix else key)

    for section in ('env_files', 'config_files', 'app_json'):
        for name, source, detail in config_records(inventory.get(section, [])):
            add(_element(f"config:{source['file']}#{name}", name, 'config-value', source, field=name, detail=detail))
    return elements


def classify(elements, llm=None):
    """Resolve only remaining candidates; preserve cache-only misses and provenance."""
    result = []
    for original in elements:
        element = dict(original)
        if not element.get('data_category') and llm is not None:
            declaration = f"{element['kind']} {element['model'] or ''}.{element['name']} " + ' '.join(element.get('signals', []))
            verdict = llm.ask('classification', mask_for_egress(declaration),
                              {'name': mask_for_egress(element['name']), 'kind': element['kind'], 'model': mask_for_egress(element['model']) if element['model'] else None})
            element['llm'] = verdict
            if verdict.get('status') == 'assessed':
                category = (verdict.get('value') or {}).get('data_category')
                if category is None or category in _CATEGORIES:
                    element['data_category'] = category
                    element['status'] = 'llm'
        result.append(element)
    return result
