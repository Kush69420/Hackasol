from pathlib import Path
from types import SimpleNamespace

from auditor.analysers.django import analyse_consent
from auditor.consent.graph import build_graph
from auditor.evidence import evidence


def _context(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    return SimpleNamespace(root=root, files=files, inventory={'forms': [], 'templates': []},
                           elements=[], routes=lambda *args: [],
                           evidence=lambda source: evidence(root, source))


def _fixture(root):
    files = {
        'app/models.py': '''\nclass ConsentEvent(models.Model):\n    user = models.ForeignKey(User)\n    action = models.CharField()\n    purpose = models.CharField()\n    consent_version = models.CharField()\n    timestamp = models.DateTimeField(auto_now_add=True)\n\nclass Profile(models.Model):\n    consent_granted = models.BooleanField(default=False)\n''',
        'app/views.py': '''\nclass GrantView(View):\n    template_name = "grant.html"\n    def post(self, request):\n        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="messages", consent_version="v1")\n\nclass WithdrawView(View):\n    template_name = "withdraw.html"\n    def post(self, request):\n        withdraw_consent(request.user)\n''',
        'app/urls.py': '''\nurlpatterns = [\n    path("grant/", GrantView.as_view(), name="grant"),\n    path("withdraw/", WithdrawView.as_view(), name="withdraw"),\n]\n''',
        'project/settings.py': '''\nMIDDLEWARE = ["app.middleware.ConsentMiddleware"]\n''',
        'app/middleware.py': '''\nclass ConsentMiddleware:\n    def __call__(self, request):\n        if not request.user.profile.consent_granted:\n            return redirect("grant")\n        return self.get_response(request)\n''',
        'templates/start.html': '''<a href="{% url 'grant' %}">Grant</a>\n<a href="{% url 'withdraw' %}">Withdraw</a>\n''',
        'templates/grant.html': '''<form method="post" action="{% url 'grant' %}">\n<p>To send messages</p><input type="checkbox" name="consent_messages" required>\n<input type="checkbox" name="confirm_age" required>\n<button type="submit">Grant</button>\n</form>''',
        'templates/withdraw.html': '''<form method="post">\n<p>Withdraw consent for messages</p>\n<button type="submit">Withdraw</button>\n</form>''',
    }
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    return list(files)


def test_django_inventory_resolves_sources(tmp_path):
    files = _fixture(tmp_path)
    result = analyse_consent(tmp_path, files)
    action = next(a for a in result['template_actions'] if a['url_name'] == 'grant')
    assert action['url']['view']['file'] == 'app/views.py'
    assert result['event_writes'][0]['model'] == 'ConsentEvent'
    assert result['middleware'][0]['implementation']['file'] == 'app/middleware.py'
    assert {m['name'] for m in result['models']} == {'ConsentEvent', 'Profile'}


def test_django_graph_records_and_static_steps(tmp_path):
    _fixture(tmp_path)
    graph = build_graph(_context(tmp_path))
    assert len(graph['records']) == 1 and graph['records'][0]['complete']
    assert graph['records'][0]['model'] == 'ConsentEvent'
    assert graph['enforcement_points'] and graph['enforcement_points'][0]['server_side']
    assert graph['grant_paths'][0]['step_count'] == 4
    assert graph['withdrawal_paths'][0]['step_count'] == 2
    assert graph['purposes'] and graph['purposes'][0]['evidence'][0]['file'] == 'templates/grant.html'


def test_django_boolean_is_not_a_consent_record(tmp_path):
    _fixture(tmp_path)
    (tmp_path / 'app/models.py').write_text('class Profile(models.Model):\n    consent_granted = models.BooleanField(default=False)\n')
    graph = build_graph(_context(tmp_path))
    assert graph['records'] == []


def test_django_unresolved_paths_have_no_invented_count(tmp_path):
    _fixture(tmp_path)
    (tmp_path / 'templates/start.html').unlink()
    graph = build_graph(_context(tmp_path))
    assert graph['grant_paths'][0]['step_count'] is None
    assert graph['withdrawal_paths'][0]['step_count'] is None


def test_django_distinguishes_purpose_records_from_shared_boolean(tmp_path):
    _fixture(tmp_path)
    template = tmp_path / 'templates/grant.html'
    template.write_text(template.read_text().replace(
        '<input type="checkbox" name="confirm_age" required>',
        '<p>To provide analytics</p><input type="checkbox" name="consent_analytics" required>\n'
        '<input type="checkbox" name="confirm_age" required>'))
    views = tmp_path / 'app/views.py'
    views.write_text(views.read_text().replace(
        '\n\nclass WithdrawView',
        '\n        ConsentEvent.objects.create(user=request.user, action="GRANTED", purpose="analytics", consent_version="v1")\n\nclass WithdrawView'))
    graph = build_graph(_context(tmp_path))
    assert len(graph['purposes']) == 2
    assert len(graph['records']) == 2
    first, second = graph['records']
    assert first['complete'] and second['complete']
    assert first['purpose_ids'] and second['purpose_ids']
    assert set(first['purpose_ids']).isdisjoint(second['purpose_ids'])
    assert graph['enforcement_points'][0]['purpose_ids'] == []


def test_django_signup_form_resolves_configured_event(tmp_path):
    _fixture(tmp_path)
    (tmp_path / 'project/settings.py').write_text(
        'ACCOUNT_SIGNUP_FORM_CLASS = "app.forms.SignupForm"\n')
    (tmp_path / 'app/forms.py').write_text(
        'class SignupForm(forms.Form):\n'
        '    consent_messages = forms.BooleanField()\n'
        '    def signup(self, request, user):\n'
        '        ConsentEvent.objects.create(user=user, action="GRANTED", purpose="messages", consent_version="v1")\n')
    (tmp_path / 'templates/signup.html').write_text(
        '<form action="{% url \'account_signup\' %}" method="post">\n'
        '<p>To send messages</p><input type="checkbox" name="consent_messages" required>\n'
        '<button type="submit">Grant</button></form>')
    graph = build_graph(_context(tmp_path))
    signup = next(path for path in graph['grant_paths']
                  if any(ev['file'] == 'templates/signup.html' for ev in path['evidence']))
    assert {'project/settings.py', 'app/forms.py'} <= {ev['file'] for ev in signup['evidence']}


def test_django_processor_gating_traces_wrapper(tmp_path):
    _fixture(tmp_path)
    (tmp_path / 'app/posthog_utils.py').write_text(
        'import posthog\n'
        'def ph_capture(user, event):\n'
        '    if not analytics_consent_given():\n'
        '        return\n'
        '    client.capture(user, event)\n')
    (tmp_path / 'app/telemetry.py').write_text(
        'from .posthog_utils import ph_capture\n'
        'def event(user):\n'
        '    ph_capture(user, "event")\n')
    graph = build_graph(_context(tmp_path))
    assert graph['processor_propagation'][0]['state'] == 'gated'
    assert 'app/telemetry.py' in {ev['file'] for ev in graph['processor_propagation'][0]['evidence']}
