import path from 'node:path';
import { ts, coord, textCoord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const propName = n => n?.name && (ts.isIdentifier(n.name) || ts.isStringLiteral(n.name)) ? n.name.text : null;
const attr = (tag, key) => {
  const escaped = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return tag.match(new RegExp('(?:^|\\s)' + escaped + '\\s*=\\s*["\']([^"\']*)["\']', 'i'))?.[1] ?? null;
};
const location = (file, text, match) => textCoord(file, text, match.index, match.index + match[0].length - 1);
const normalise = value => {
  if (!value) return null;
  const start = value.indexOf('/');
  if (start < 0) return null;
  return value.slice(start).replace(/\/+/g, '/').replace(/\/$/, '') || '/';
};
const scriptExcerpt = code => {
  if (!code.trim()) return null;
  const sf = ts.createSourceFile('inline.js', code, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
  const calls = [];
  walk(sf, n => {
    if (ts.isCallExpression(n) && (ts.isIdentifier(n.expression) || ts.isPropertyAccessExpression(n.expression))) {
      const expression = n.expression.getText(sf);
      if (/^[\w$.]+$/.test(expression)) calls.push(`${expression}(…)`);
    }
  });
  return calls.join('; ') || null;
};

export function extractFrontend(project) {
  const forms = [], templates = [], service_calls = [], client_storage = [], outbound_headers = [];
  const translationFile = 'frontend/src/assets/i18n/en.json';
  let translations = {};
  if (project.has(translationFile)) { try { translations = JSON.parse(project.text(translationFile)); } catch {} }
  const tsFiles = project.files.filter(f => f.startsWith('frontend/') && /\.[cm]?ts$/.test(f));
  const components = new Map();
  for (const file of tsFiles) {
    const sf = project.source(file), constants = new Map(), controls = new Map();
    let className = path.basename(file).replace(/\.ts$/, ''), templateUrl = null;
    walk(sf, n => {
      if (ts.isClassDeclaration(n) && n.name) className = n.name.text;
      if (ts.isPropertyAssignment(n) && propName(n) === 'templateUrl' && ts.isStringLiteral(n.initializer)) templateUrl = n.initializer.text;
      if ((ts.isPropertyDeclaration(n) || ts.isVariableDeclaration(n)) && n.name && ts.isIdentifier(n.name) && n.initializer) {
        constants.set(n.name.text, n.initializer);
        if (ts.isNewExpression(n.initializer)) {
          const ctor = n.initializer.expression.getText(sf);
          if (ctor === 'UntypedFormControl') controls.set(n.name.text, 'untyped');
          if (ctor === 'FormControl') controls.set(n.name.text, 'reactive');
        }
      }
    });
    if (templateUrl) components.set(path.posix.normalize(path.posix.join(path.posix.dirname(file), templateUrl)), { className, controls });
    const resolve = (n, seen = new Set()) => {
      if (!n) return '';
      if (ts.isStringLiteralLike(n)) return n.text;
      if (ts.isParenthesizedExpression(n)) return resolve(n.expression, seen);
      if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PlusToken) return resolve(n.left, seen) + resolve(n.right, seen);
      if (ts.isTemplateExpression(n)) return n.head.text + n.templateSpans.map(s => resolve(s.expression, seen) + s.literal.text).join('');
      const key = ts.isIdentifier(n) ? n.text : ts.isPropertyAccessExpression(n) && n.expression.kind === ts.SyntaxKind.ThisKeyword ? n.name.text : null;
      if (key && constants.has(key) && !seen.has(key)) { const next = new Set(seen); next.add(key); return resolve(constants.get(key), next); }
      if (ts.isPropertyAccessExpression(n) && n.getText(sf).startsWith('environment.')) return '';
      return key ? `{${key}}` : `{${n.getText(sf)}}`;
    };
    let method = null;
    const visit = n => {
      const previous = method;
      if (ts.isMethodDeclaration(n)) method = propName(n);
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression)) {
        const access = n.expression, receiver = access.expression.getText(sf), op = access.name.text;
        if (file.startsWith('frontend/src/app/Services/') && receiver === 'this.http' && ['get','post','put','patch','delete'].includes(op) && n.arguments[0]) {
          service_calls.push({ service: className, function: method, http_method: op.toUpperCase(), url_expression: n.arguments[0].getText(sf), normalised_path: normalise(resolve(n.arguments[0])), source: coord(sf, n) });
        }
        const storage = receiver === 'localStorage' || receiver === 'sessionStorage' ? receiver : /(?:^|\.)cookieService$/i.test(receiver) ? 'cookie' : null;
        const operation = ({ getItem: 'get', setItem: 'set', removeItem: 'remove', get: 'get', put: 'set', set: 'set', remove: 'remove', delete: 'remove' })[op];
        if (storage && operation) client_storage.push({ api: storage, op: operation, key: n.arguments[0] && ts.isStringLiteralLike(n.arguments[0]) ? n.arguments[0].text : n.arguments[0]?.getText(sf) ?? null, source: coord(sf, n) });
      }
      if (ts.isPropertyAccessExpression(n) && n.getText(sf) === 'document.cookie') {
        const parent = n.parent;
        const write = ts.isBinaryExpression(parent) && parent.left === n && parent.operatorToken.kind === ts.SyntaxKind.EqualsToken;
        client_storage.push({ api: 'cookie', op: write ? 'set' : 'get', key: null, source: coord(sf, write ? parent : n) });
      }
      if (file === 'frontend/src/app/Services/request.interceptor.ts' && ts.isPropertyAssignment(n) && propName(n) === 'setHeaders' && ts.isObjectLiteralExpression(n.initializer)) {
        for (const p of n.initializer.properties) if (ts.isPropertyAssignment(p) && propName(p)) {
          // Keep storage lookup keys while redacting other literal values.
          const expression = p.initializer.getText(sf).replace(/(['"])(?:\\.|(?!\1).)*?\1/g, s => /^(?:'token'|"token"|'email'|"email")$/.test(s) ? s : '<literal>').replace(/`[^$`]*/g, '`<literal>');
          outbound_headers.push({ header: propName(p), value_expression: expression, source: coord(sf, p) });
        }
      }
      ts.forEachChild(n, visit);
      method = previous;
    };
    visit(sf);
  }
  for (const file of project.files.filter(f => /^views\/.*\.hbs$/.test(f) || f === 'frontend/src/index.html' || (f.startsWith('frontend/src/app/') && f.endsWith('.html')))) {
    const text = project.text(file), inputs = [], scripts = [];
    for (const m of text.matchAll(/<(input|textarea|select|mat-select)\b[^>]*>/gi)) {
      const tag = m[0];
      inputs.push({ match: m, name: attr(tag, 'name') ?? attr(tag, 'id'), input_type: attr(tag, 'type') ?? (m[1].toLowerCase() === 'input' ? 'text' : m[1].toLowerCase()), source: location(file, text, m) });
    }
    if (/^views\/.*\.hbs$/.test(file) || file === 'frontend/src/index.html') {
      for (const m of text.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)) scripts.push({ src: attr(m[0].slice(0, m[0].indexOf('>') + 1), 'src'), inline_excerpt: scriptExcerpt(m[2]), source: location(file, text, m) });
      templates.push({ file, kind: file.endsWith('.hbs') ? 'hbs' : 'html', source: textCoord(file, text, 0, Math.max(0, text.length - 1)), inputs: inputs.map(({match, ...input}) => input), scripts, notes: [] });
    }
    const component = components.get(file);
    if (!component) continue;
    const grouped = new Map();
    for (const input of inputs) {
      const tag = input.match[0], binding = attr(tag, '[formField]') ?? attr(tag, '[field]') ?? attr(tag, '[control]'), control = attr(tag, '[formControl]'), model = attr(tag, '[(ngModel)]'), formControlName = attr(tag, 'formControlName');
      const style = binding ? 'signal' : model ? 'ngModel' : control ? component.controls.get(control.replace(/^this\./, '')) ?? 'reactive' : formControlName ? 'reactive' : null;
      if (!style) continue;
      const before = text.slice(0, input.match.index), start = Math.max(before.lastIndexOf('<mat-form-field'), before.lastIndexOf('<label'), before.lastIndexOf('<div'));
      const nearby = before.slice(Math.max(0, start));
      const labels = [...nearby.matchAll(/<(mat-label|label)\b([^>]*)>([\s\S]*?)<\/\1\s*>/gi)];
      const labelMatch = labels.at(-1), labelText = labelMatch?.[3]?.replace(/<[^>]*>/g, '').trim() ?? null;
      const key = labelText?.match(/['"]([^'"]+)['"]\s*\|\s*translate/)?.[1] ?? (labelMatch && /\btranslate\b/.test(labelMatch[2]) ? labelText : null);
      const label = key ? translations[key] ?? key : labelText;
      const name = (binding ?? model ?? control ?? formControlName ?? input.name)?.split('.').at(-1) ?? null;
      if (!grouped.has(style)) grouped.set(style, []);
      grouped.get(style).push({ name, input_type: input.input_type, label, i18n_key: key, source: input.source });
    }
    for (const [style, fields] of grouped) forms.push({ component: component.className, style, source: textCoord(file, text, 0, Math.max(0, text.length - 1)), inputs: fields });
  }
  return { forms, templates, service_calls, client_storage, outbound_headers };
}
