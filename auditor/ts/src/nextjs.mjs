import path from 'node:path';
import { ts, coord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const property = (obj, key) => obj && ts.isObjectLiteralExpression(obj) ? obj.properties.find(p => p.name?.getText().replace(/^['"]|['"]$/g, '') === key) : null;
const literal = n => n && ts.isStringLiteralLike(n) ? n.text : null;
const normalise = p => {
  if (!p) return null;
  p = p.replace(/^https?:\/\/[^/]+/i, '').split('?')[0].replace(/\/+/g, '/').replace(/\/$/, '');
  return p.startsWith('/') ? p || '/' : null;
};

export function extractNextjs(project) {
  const forms = [], service_calls = [], client_storage = [], routes = [];
  const files = project.files.filter(f => f.startsWith('frontend/src/') && /\.[cm]?[jt]sx?$/.test(f));
  if (!files.some(f => /^frontend\/src\/(?:app\/(?:.*\/)?(?:page|route)|pages\/.+)\.[jt]sx?$/.test(f))) return { forms, service_calls, client_storage, routes };
  for (const file of files) {
    const sf = ts.createSourceFile(file, project.text(file), ts.ScriptTarget.Latest, true, file.endsWith('x') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    const constants = new Map(), methods = new Map(), inputs = [], labels = new Map();
    walk(sf, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) constants.set(n.name.text, n.initializer);
      if (ts.isMethodDeclaration(n) && n.name) methods.set(n.name.getText(sf), n);
      if (ts.isJsxElement(n) && n.openingElement.tagName.getText(sf) === 'label') {
        const attr = n.openingElement.attributes.properties.find(p => p.name?.getText(sf) === 'htmlFor');
        const id = literal(attr?.initializer);
        if (id) labels.set(id, n.children.map(c => ts.isJsxText(c) ? c.text.trim() : '').filter(Boolean).join(' '));
      }
    });
    const resolve = (n, seen = new Set()) => {
      if (!n) return '';
      if (ts.isStringLiteralLike(n)) return n.text;
      if (ts.isParenthesizedExpression(n)) return resolve(n.expression, seen);
      if (ts.isBinaryExpression(n)) {
        if (n.operatorToken.kind === ts.SyntaxKind.PlusToken) return resolve(n.left, seen) + resolve(n.right, seen);
        return '';
      }
      if (ts.isTemplateExpression(n)) return n.head.text + n.templateSpans.map(s => resolve(s.expression, seen) + s.literal.text).join('');
      if (ts.isIdentifier(n)) {
        if (constants.has(n.text) && !seen.has(n.text)) { const next = new Set(seen); next.add(n.text); return resolve(constants.get(n.text), next); }
        return `{${n.text}}`;
      }
      return '';
    };
    let current = null;
    function visit(n) {
      const previous = current;
      if (ts.isMethodDeclaration(n) || ts.isFunctionDeclaration(n)) current = n.name?.getText(sf) ?? null;
      if (ts.isJsxSelfClosingElement(n) || ts.isJsxOpeningElement(n)) {
        const tag = n.tagName.getText(sf);
        if (['input', 'select', 'textarea'].includes(tag)) {
          const get = key => {
            const attr = n.attributes.properties.find(p => p.name?.getText(sf) === key);
            return literal(attr?.initializer) ?? (attr?.initializer && ts.isJsxExpression(attr.initializer) ? literal(attr.initializer.expression) : null);
          };
          const id = get('id'), name = get('name') ?? id ?? (get('type') === 'file' ? 'file' : null);
          inputs.push({ name, input_type: get('type') ?? (tag === 'input' ? 'text' : tag), label: get('aria-label') ?? labels.get(id) ?? null, i18n_key: null, source: coord(sf, n) });
        }
      }
      if (ts.isCallExpression(n)) {
        const expr = n.expression.getText(sf), args = n.arguments;
        const storage = expr.match(/^(?:window\.)?(localStorage|sessionStorage)\.setItem$/);
        if (storage) client_storage.push({ api: storage[1], op: 'set', key: literal(args[0]) ?? args[0]?.getText(sf) ?? null, source: coord(sf, n) });
        let method = null, url = null;
        if (expr === 'fetch' || expr === 'window.fetch') {
          url = args[0]; method = literal(property(args[1], 'method')?.initializer)?.toUpperCase() ?? 'GET';
        } else if (/^(?:axios|api)\.(get|post|put|patch|delete)$/i.test(expr)) {
          url = args[0]; method = expr.split('.').at(-1).toUpperCase();
        } else if (expr === 'axios' && ts.isObjectLiteralExpression(args[0])) {
          url = property(args[0], 'url')?.initializer; method = literal(property(args[0], 'method')?.initializer)?.toUpperCase() ?? 'GET';
        } else if (expr.startsWith('this.') && methods.has(expr.slice(5))) {
          const wrapper = methods.get(expr.slice(5));
          let fetchCall = null;
          walk(wrapper, x => { if (ts.isCallExpression(x) && x.expression.getText(sf) === 'fetch') fetchCall = x; });
          if (fetchCall) {
            const parameter = wrapper.parameters.findIndex(p => fetchCall.arguments[0]?.getText(sf).includes(p.name.getText(sf)));
            if (parameter >= 0 && args[parameter]) {
              url = args[parameter];
              const options = wrapper.parameters.findIndex(p => fetchCall.arguments[1]?.getText(sf).includes(p.name.getText(sf)));
              method = literal(property(args[options], 'method')?.initializer)?.toUpperCase() ?? literal(property(fetchCall.arguments[1], 'method')?.initializer)?.toUpperCase() ?? 'GET';
            }
          }
        }
        const resolved = normalise(resolve(url));
        if (method && resolved) service_calls.push({ service: path.basename(file).replace(/\.[^.]+$/, ''), function: current, http_method: method, url_expression: url.getText(sf), normalised_path: resolved, source: coord(sf, n) });
      }
      ts.forEachChild(n, visit);
      current = previous;
    }
    visit(sf);
    if (inputs.length) forms.push({ component: path.basename(file).replace(/\.[^.]+$/, ''), style: 'jsx', source: coord(sf, sf), inputs });
    let match = file.match(/^frontend\/src\/(app|pages)\/(.+)\.[jt]sx?$/);
    if (match) {
      const [_, kind, name] = match;
      if ((kind === 'app' && /(?:^|\/)(page|route)$/.test(name)) || (kind === 'pages' && !/(?:^|\/)_(?:app|document|error)$/.test(name))) {
        const p = '/' + name.replace(/(?:^|\/)(page|route|index)$/, '').replace(/\[\.\.\.(\w+)\]/g, '{$1}').replace(/\[(\w+)\]/g, '{$1}');
        const source = coord(sf, sf);
        const verbs = [];
        if (kind === 'app' && name.endsWith('/route')) for (const stmt of sf.statements) if (ts.isFunctionDeclaration(stmt) && /^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/.test(stmt.name?.text ?? '')) verbs.push(stmt.name.text);
        for (const method of verbs.length ? verbs : ['GET']) routes.push({ method, path: p, normalised_path: p.replace(/\/$/, '') || '/', origin: 'nextjs', source, registration: source, handler: null, middleware: [], model: null, finale: null, swagger: null, query_params: [], body_params: [] });
      }
    }
  }
  return { forms, service_calls, client_storage, routes };
}
