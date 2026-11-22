"""Versioned JSON response contracts for the four LLM roles."""
PROMPT_VERSION = {role: f'{role}-v1' for role in ('classification', 'triage', 'consent', 'fix')}

SHAPES = {
    'classification': '{"data_category": "Government Identifier|Biometric|Financial|Health|Child Data|Authentication Secret|Contact|Profile", "reason": "nonempty explanation"}',
    'triage': '{"verdict": "true-positive|false-positive|uncertain", "reason": "nonempty explanation"}',
    'consent': '{"assessment": "explanation of the Consent Assessment"}',
    'fix': '{"fix": "recommended fix"}',
}


def system_prompt(role):
    return f'Assess the supplied Evidence for {role}. Return only a JSON object in this shape: {SHAPES[role]}.'


def valid_value(role, value):
    if not isinstance(value, dict):
        return False
    keys = {'classification': {'data_category', 'reason'}, 'triage': {'verdict', 'reason'}, 'consent': {'assessment'}, 'fix': {'fix'}}[role]
    if set(value) != keys or not all(isinstance(v, str) and v.strip() for v in value.values()):
        return False
    if role == 'triage':
        return value['verdict'] in {'true-positive', 'false-positive', 'uncertain'}
    if role == 'classification':
        return value['data_category'] in {'Government Identifier', 'Biometric', 'Financial', 'Health', 'Child Data', 'Authentication Secret', 'Contact', 'Profile'}
    return True
