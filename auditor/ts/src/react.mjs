// React form bindings: JSX inputs, the state or react-hook-form field each one is bound to, the submit
// handler that reads it, and the client request (fetch/axios) that carries it.
// Emits `forms` (same shape as nextjs.mjs, style 'jsx') and `react_requests`. A request whose method
// or URL cannot be resolved statically is kept with `unresolved: true` and never joined to a route.
import { ts, coord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const lit = n => n && ts.isStringLiteralLike(n) ? n.text : null;
const prop = (obj, key) => obj && ts.isObjectLiteralExpression(obj)
  ? obj.properties.find(p => p.name && p.name.getText().replace(/^['"]|['"]$/g, '') === key) : null;
const propValue = p => p && (ts.isShorthandPropertyAssignment(p) ? p.name : ts.isPropertyAssignment(p) ? p.initializer : null);
const unwrap = n => { while (n && (ts.isParenthesizedExpression(n) || ts.isAsExpression(n) || ts.isNonNullExpression(n) || ts.isAwaitExpression(n))) n = n.expression; return n; };
const ENV = /^(?:process\.env|import\.meta\.env)\b/;

export function extractReact(project, existingForms = []) {
  const forms = [], react_requests = [];
  const covered = new Set(existingForms.filter(f => f.style === 'jsx').map(f => f.source.file));
  for (const file of project.files.filter(f => /\.[jt]sx$/.test(f) && !covered.has(f))) {
    const text = project.text(file);
    if (!/<form[\s>]/.test(text)) continue;
    const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const state = new Map(), setters = new Map(), fns = new Map(), consts = new Map(), labels = new Map();
    let hookForm = null;
    walk(sf, n => {
      if (ts.isVariableDeclaration(n) && n.initializer) {
        const init = unwrap(n.initializer);
        if (ts.isArrayBindingPattern(n.name) && ts.isCallExpression(init) && /^(?:React\.)?useState$/.test(init.expression.getText(sf))) {
          const [value, setter] = n.name.elements.map(e => ts.isBindingElement(e) ? e.name.getText(sf) : null);
          const seed = init.arguments[0];
          if (value) { state.set(value, { setter, object: !!seed && ts.isObjectLiteralExpression(seed) }); if (setter) setters.set(setter, value); }
        } else if (ts.isIdentifier(n.name)) {
          if (ts.isArrowFunction(init) || ts.isFunctionExpression(init)) fns.set(n.name.text, init);
          else consts.set(n.name.text, init);
        } else if (ts.isObjectBindingPattern(n.name) && ts.isCallExpression(init) && /^useForm$/.test(init.expression.getText(sf))) {
          hookForm = {};
          for (const e of n.name.elements) hookForm[(e.propertyName ?? e.name).getText(sf)] = e.name.getText(sf);
        }
      }
      if (ts.isFunctionDeclaration(n) && n.name) fns.set(n.name.text, n);
      if (ts.isJsxElement(n) && n.openingElement.tagName.getText(sf) === 'label') {
        const attr = n.openingElement.attributes.properties.find(p => p.name?.getText(sf) === 'htmlFor');
        const id = lit(attr?.initializer) ?? (attr?.initializer && ts.isJsxExpression(attr.initializer) ? lit(attr.initializer.expression) : null);
        if (id) labels.set(id, n.children.map(c => ts.isJsxText(c) ? c.text.trim() : '').filter(Boolean).join(' '));
      }
    });
    const registerName = hookForm?.register ?? 'register', submitWrapper = hookForm?.handleSubmit ?? 'handleSubmit';

    function enclosingComponent(n) {
      for (let p = n.parent; p; p = p.parent) {
        if (ts.isFunctionDeclaration(p) && p.name) return p.name.text;
        if (ts.isVariableDeclaration(p) && ts.isIdentifier(p.name) && p.initializer && (ts.isArrowFunction(unwrap(p.initializer)) || ts.isFunctionExpression(unwrap(p.initializer)))) return p.name.text;
      }
      return file.replace(/^.*\//, '').replace(/\.[jt]sx$/, '');
    }
    const attrOf = (el, key) => el.attributes.properties.find(p => ts.isJsxAttribute(p) && p.name.getText(sf) === key);
    const attrText = (el, key) => { const a = attrOf(el, key); return a ? (lit(a.initializer) ?? (a.initializer && ts.isJsxExpression(a.initializer) ? lit(a.initializer.expression) : null)) : null; };
    const attrExpr = (el, key) => { const a = attrOf(el, key); return a?.initializer && ts.isJsxExpression(a.initializer) ? unwrap(a.initializer.expression) : null; };

    function inputOf(el, labelText) {
      const id = attrText(el, 'id');
      let name = attrText(el, 'name') ?? id, binding = null;
      for (const p of el.attributes.properties) {
        if (!ts.isJsxSpreadAttribute(p)) continue;
        const call = unwrap(p.expression);
        if (ts.isCallExpression(call) && call.expression.getText(sf) === registerName && lit(call.arguments[0])) { name = lit(call.arguments[0]); binding = { kind: 'register', key: name }; }
      }
      const value = attrExpr(el, 'value'), change = attrExpr(el, 'onChange');
      if (!binding && value && ts.isIdentifier(value) && state.has(value.text)) binding = { kind: 'state', variable: value.text };
      if (!binding && value && ts.isPropertyAccessExpression(value) && ts.isIdentifier(value.expression) && state.get(value.expression.text)?.object) {
        binding = { kind: 'state-field', variable: value.expression.text, field: value.name.text };
        name ??= value.name.text;
      }
      if (!binding && change) {
        let found = null;
        walk(change, x => { if (!found && ts.isCallExpression(x) && ts.isIdentifier(x.expression) && setters.has(x.expression.text)) found = setters.get(x.expression.text); });
        if (found) binding = { kind: 'state', variable: found };
      }
      if (!binding && name) binding = { kind: 'name', key: name };
      const type = attrText(el, 'type');
      const tag = el.tagName.getText(sf);
      return { name, input_type: type ?? (tag === 'input' ? 'text' : tag), label: attrText(el, 'aria-label') ?? (id && labels.get(id)) ?? labelText ?? attrText(el, 'placeholder') ?? null, i18n_key: null, source: coord(sf, el), binding };
    }

    function handlerOf(formEl) {
      const expr = attrExpr(formEl, 'onSubmit');
      if (!expr) return null;
      if (ts.isIdentifier(expr)) return fns.get(expr.text) ?? null;
      if (ts.isArrowFunction(expr) || ts.isFunctionExpression(expr)) return expr;
      if (ts.isCallExpression(expr) && expr.expression.getText(sf) === submitWrapper) {
        const inner = unwrap(expr.arguments[0]);
        return inner && ts.isIdentifier(inner) ? fns.get(inner.text) ?? null : inner ?? null;
      }
      return null;
    }

    // Static URL resolution. A leading environment/base-URL part is dropped; anything else dynamic is
    // only accepted as a whole path segment ({param}); otherwise the request is unresolved.
    function parts(n, seen = new Set()) {
      n = unwrap(n);
      if (!n) return null;
      if (ts.isStringLiteralLike(n)) return [{ text: n.text }];
      if (ts.isTemplateExpression(n)) {
        const out = [{ text: n.head.text }];
        for (const s of n.templateSpans) { out.push({ expr: unwrap(s.expression) }, { text: s.literal.text }); }
        return out;
      }
      if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.PlusToken) {
        const a = parts(n.left, seen), b = parts(n.right, seen);
        return a && b ? [...a, ...b] : null;
      }
      return [{ expr: n }];
    }
    function isBase(e) {
      if (ENV.test(e.getText(sf))) return true;
      if (ts.isIdentifier(e) && consts.has(e.text)) {
        const init = unwrap(consts.get(e.text));
        const t = init.getText(sf);
        return ENV.test(t) || (lit(init) !== null && /^(?:https?:\/\/[^/]*)?$/.test(lit(init)));
      }
      return false;
    }
    function resolveUrl(node) {
      let list = parts(node);
      if (!list) return null;
      // Expand a const that holds a literal path.
      list = list.flatMap(p => p.expr && ts.isIdentifier(p.expr) && consts.has(p.expr.text) && !isBase(p.expr) && parts(consts.get(p.expr.text))?.every(x => x.text !== undefined) ? parts(consts.get(p.expr.text)) : [p]);
      if (list[0]?.expr && isBase(list[0].expr)) list = list.slice(1);
      let out = '';
      for (let i = 0; i < list.length; i++) {
        const p = list[i];
        if (p.text !== undefined) { out += p.text; continue; }
        const before = out.endsWith('/'), next = list[i + 1];
        if (!before || (next && next.text !== undefined && next.text !== '' && !next.text.startsWith('/') && !next.text.startsWith('?'))) return null;
        out += `{${ts.isIdentifier(p.expr) ? p.expr.text : ts.isPropertyAccessExpression(p.expr) ? p.expr.name.text : 'param'}}`;
      }
      out = out.replace(/^https?:\/\/[^/]+/i, '').split('?')[0].replace(/\/+/g, '/').replace(/(.)\/$/, '$1');
      return out.startsWith('/') ? out : null;
    }

    function requestsIn(fnNode, depth, seen) {
      const found = [];
      if (!fnNode || seen.has(fnNode) || depth > 2) return found;
      seen.add(fnNode);
      walk(fnNode, n => {
        if (!ts.isCallExpression(n)) return;
        const expr = n.expression.getText(sf), args = n.arguments;
        let method = null, url = null, payload = null, dynamicMethod = false;
        if (expr === 'fetch' || expr === 'window.fetch') {
          url = args[0];
          const m = propValue(prop(args[1], 'method'));
          method = m ? lit(unwrap(m))?.toUpperCase() ?? null : 'GET'; dynamicMethod = !method;
          const body = propValue(prop(args[1], 'body'));
          const b = body && unwrap(body);
          payload = b && ts.isCallExpression(b) && b.expression.getText(sf) === 'JSON.stringify' ? b.arguments[0] : b;
        } else if (/^(?:axios|api|http|client)\.(get|post|put|patch|delete)$/i.test(expr)) {
          url = args[0]; method = expr.split('.').at(-1).toUpperCase(); payload = method === 'GET' || method === 'DELETE' ? null : args[1];
        } else if (expr === 'axios' && args[0] && ts.isObjectLiteralExpression(args[0])) {
          url = propValue(prop(args[0], 'url')); const m = propValue(prop(args[0], 'method'));
          method = m ? lit(unwrap(m))?.toUpperCase() ?? null : 'GET'; dynamicMethod = !method; payload = propValue(prop(args[0], 'data'));
        } else if (ts.isIdentifier(n.expression) && fns.has(n.expression.text)) {
          found.push(...requestsIn(fns.get(n.expression.text), depth + 1, seen));
          return;
        } else return;
        if (!url) return;
        found.push({ node: n, method, dynamicMethod, url, payload });
      });
      return found;
    }

    walk(sf, n => {
      if (!ts.isJsxElement(n) || n.openingElement.tagName.getText(sf) !== 'form') return;
      const component = enclosingComponent(n);
      const inputs = [];
      walk(n, x => {
        const el = ts.isJsxSelfClosingElement(x) ? x : ts.isJsxOpeningElement(x) && ['input', 'select', 'textarea'].includes(x.tagName.getText(sf)) ? x : null;
        if (!el || !['input', 'select', 'textarea'].includes(el.tagName.getText(sf))) return;
        let labelText = null;
        for (let p = el.parent; p && p !== n; p = p.parent) if (ts.isJsxElement(p) && p.openingElement.tagName.getText(sf) === 'label') { labelText = p.children.map(c => ts.isJsxText(c) ? c.text.trim() : '').filter(Boolean).join(' ') || null; break; }
        const input = inputOf(el, labelText);
        if (input.name) inputs.push(input);
      });
      if (!inputs.length) return;
      const handler = handlerOf(n.openingElement);
      forms.push({ component, style: 'jsx', source: coord(sf, n.openingElement), inputs, submit: handler ? coord(sf, handler) : null });
      if (!handler) return;
      const dataParam = ts.isFunctionLike(handler) && handler.parameters[0] && ts.isIdentifier(handler.parameters[0].name) ? handler.parameters[0].name.text : null;
      for (const call of requestsIn(handler, 0, new Set())) {
        const path = resolveUrl(call.url), method = call.dynamicMethod ? null : call.method;
        const urlText = call.url.getText(sf).replace(/\s+/g, ' ').slice(0, 160);
        const payload = [];
        const add = (key, valueNode, node) => {
          // Base identifier of a call/property chain: email.trim() -> email; form.email -> form.email.
          let v = unwrap(valueNode), field = null;
          while (v && ts.isCallExpression(v) && ts.isPropertyAccessExpression(v.expression)) v = unwrap(v.expression.expression);
          let variable = null;
          if (v && ts.isIdentifier(v)) variable = v.text;
          else if (v && ts.isPropertyAccessExpression(v) && ts.isIdentifier(v.expression)) { variable = v.expression.text; field = v.name.text; }
          const match = inputs.find(i => i.binding && (
            (i.binding.kind === 'state' && i.binding.variable === variable && !field) ||
            (i.binding.kind === 'state-field' && i.binding.variable === variable && i.binding.field === field) ||
            ((i.binding.kind === 'register' || i.binding.kind === 'name') && variable === dataParam && field === i.binding.key)));
          payload.push({ key, input: match?.name ?? null, source: coord(sf, node) });
        };
        const body = call.payload && unwrap(call.payload);
        const everyInput = (variable) => {
          for (const i of inputs) {
            const b = i.binding;
            if (b?.kind === 'state-field' && b.variable === variable) payload.push({ key: b.field, input: i.name, source: coord(sf, body) });
            else if ((b?.kind === 'register' || b?.kind === 'name') && variable === dataParam) payload.push({ key: b.key, input: i.name, source: coord(sf, body) });
          }
        };
        if (body && ts.isObjectLiteralExpression(body)) {
          for (const p of body.properties) {
            if (ts.isSpreadAssignment(p)) { const s = unwrap(p.expression); if (ts.isIdentifier(s)) everyInput(s.text); }
            else if (ts.isShorthandPropertyAssignment(p)) add(p.name.text, p.name, p);
            else if (ts.isPropertyAssignment(p)) add(p.name.getText(sf).replace(/^['"]|['"]$/g, ''), p.initializer, p);
          }
        } else if (body && ts.isIdentifier(body)) everyInput(body.text);
        else if (body && ts.isCallExpression(body) && /Object\.fromEntries/.test(body.expression.getText(sf)) && dataParam) {
          for (const i of inputs) payload.push({ key: i.name, input: i.name, source: coord(sf, body) });
        }
        react_requests.push({ component, http_method: method, url_expression: urlText, normalised_path: path, unresolved: path === null || method === null,
          source: coord(sf, call.node), form: coord(sf, n.openingElement), handler: coord(sf, handler), payload });
      }
    });
  }
  return { forms, react_requests };
}
