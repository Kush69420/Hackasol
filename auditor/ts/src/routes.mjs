import path from 'node:path';
import { parseDocument } from 'yaml';
import { coord, textCoord, ts } from './project.mjs';

const verbs = new Set(['get', 'post', 'put', 'delete', 'patch']);
const normalise = (p) => (p.replace(/:([\w]+)/g, '{$1}').replace(/\/$/, '') || '/');
const join = (a, b) => `${a === '/' ? '' : a}${b === '/' ? '' : b}` || '/';
const property = (object, key) => object?.properties?.find(p => p.name?.getText().replace(/^['"]|['"]$/g, '') === key);
const initializer = (object, key) => { const p = property(object, key); return p && (ts.isShorthandPropertyAssignment(p) ? p.name : p.initializer); };
const literal = (n) => n && (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) ? n.text : null;
const arrayValues = n => ts.isArrayLiteralExpression(n) ? n.elements.map(x => literal(x) ?? x.getText()) : [];

// Expressions are useful as evidence, but their literal arguments may be Authentication Secrets.
function expression(node, sf) {
  const start = node.getStart(sf), replacements = [];
  function visit(n) {
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n) || ts.isNumericLiteral(n)) replacements.push([n.getStart(sf) - start, n.end - start]);
    else ts.forEachChild(n, visit);
  }
  visit(node);
  let result = node.getText(sf);
  for (const [a, b] of replacements.reverse()) result = result.slice(0, a) + '<literal>' + result.slice(b);
  return result;
}

export function extractRoutes(project) {
  const routes = [], logging = [], globals = [], active = new Set();
  function imports(sf) {
    const result = new Map();
    for (const s of sf.statements) {
      if (!ts.isImportDeclaration(s) || !s.importClause || !s.moduleSpecifier.text.startsWith('.')) continue;
      const base = path.posix.normalize(path.posix.join(path.posix.dirname(sf.fileName), s.moduleSpecifier.text));
      const file = [base + '.ts', base + '.js', base + '/index.ts'].find(f => project.has(f));
      if (!file) continue;
      const c = s.importClause;
      if (c.name) result.set(c.name.text, { file, name: 'default' });
      if (c.namedBindings && ts.isNamespaceImport(c.namedBindings)) result.set(c.namedBindings.name.text, { file, name: '*' });
      else if (c.namedBindings) for (const e of c.namedBindings.elements) result.set(e.name.text, { file, name: (e.propertyName ?? e.name).text });
    }
    return result;
  }
  function declaration(file, name) {
    const sf = project.source(file);
    for (const s of sf.statements) {
      if ((ts.isFunctionDeclaration(s) || ts.isClassDeclaration(s)) && (s.name?.text === name || (name === 'default' && s.modifiers?.some(m => m.kind === ts.SyntaxKind.DefaultKeyword)))) return { name: s.name?.text ?? 'default', ...coord(sf, s) };
      if (ts.isVariableStatement(s)) for (const d of s.declarationList.declarations) if (d.name.getText(sf) === name) return { name, ...coord(sf, d) };
      if (name === 'default' && ts.isExportAssignment(s) && ts.isIdentifier(s.expression)) return declaration(file, s.expression.text);
    }
    return null;
  }
  function resolve(node, sf, imps) {
    if (ts.isCallExpression(node)) {
      // Wrappers such as asyncHandler carry the actual route handler as an argument.
      for (const arg of node.arguments) { const found = resolve(arg, sf, imps); if (found) return found; }
      return resolve(node.expression, sf, imps);
    }
    let binding, name;
    if (ts.isPropertyAccessExpression(node) && ts.isIdentifier(node.expression)) { binding = imps.get(node.expression.text); name = node.name.text; }
    else if (ts.isIdentifier(node)) { binding = imps.get(node.text); name = binding?.name; }
    if (!binding || !binding.file.includes('routes/')) return null;
    return declaration(binding.file, binding.name === '*' ? name : binding.name);
  }
  function middleware(node, sf, scope) {
    const expr = expression(node, sf);
    const nameNode = ts.isCallExpression(node) ? node.expression : node;
    const name = nameNode.getText(sf);
    const role = /^security\.(isAuthorized|denyAll|isAccounting|is[A-Z])$/.test(name) ? 'authentication' : name === 'security.appendUserId' ? 'identity' : name === 'morgan' ? 'logging' : 'other';
    return { name, expression: expr, role, scope, source: coord(sf, node) };
  }
  function matches(prefix, route) {
    const a = normalise(prefix).split('/').filter(Boolean), b = normalise(route).split('/').filter(Boolean);
    return a.length <= b.length && a.every((x, i) => x.startsWith('{') || b[i]?.startsWith('{') || x === b[i]);
  }
  function chain(p) { return globals.filter(g => matches(g.path, p)).map(g => g.middleware); }
  const parameterCache = new Map();
  function parameters(handler) {
    const empty = { query_params: [], body_params: [] };
    if (!handler || !project.has(handler.file)) return empty;
    const key = `${handler.file}:${handler.start_line}:${handler.end_line}:${handler.name}`;
    if (parameterCache.has(key)) return parameterCache.get(key);
    const sf = project.source(handler.file);
    let root = null;
    function find(n) {
      const c = coord(sf, n);
      if (!root && c.start_line === handler.start_line && c.end_line === handler.end_line &&
          ((n.name && n.name.getText(sf) === handler.name) ||
           (handler.name === '<anonymous>' && (ts.isArrowFunction(n) || ts.isFunctionExpression(n))))) {
        root = n;
        return;
      }
      if (!root) ts.forEachChild(n, find);
    }
    find(sf);
    if (!root) return empty;
    const aliases = { query: new Set(), body: new Set() };
    const requests = new Set(['req']);
    function requestPart(n) {
      if (ts.isIdentifier(n)) {
        if (aliases.query.has(n.text)) return 'query';
        if (aliases.body.has(n.text)) return 'body';
      }
      if (ts.isPropertyAccessExpression(n) && ts.isIdentifier(n.expression) &&
          requests.has(n.expression.text) && (n.name.text === 'query' || n.name.text === 'body')) return n.name.text;
      return null;
    }
    function add(kind, name, node) {
      const list = empty[`${kind}_params`];
      if (name && !list.some(p => p.name === name)) list.push({ name, source: coord(sf, node) });
    }
    function visit(n) {
      if ((ts.isFunctionDeclaration(n) || ts.isFunctionExpression(n) || ts.isArrowFunction(n)) && n.parameters.length) {
        const first = n.parameters[0].name;
        if (ts.isIdentifier(first)) requests.add(first.text);
        else if (ts.isObjectBindingPattern(first)) for (const e of first.elements) {
          const key = e.propertyName?.getText(sf) ?? e.name.getText(sf);
          if ((key === 'query' || key === 'body') && ts.isIdentifier(e.name)) aliases[key].add(e.name.text);
        }
      }
      if (ts.isVariableDeclaration(n) && n.initializer && ts.isObjectBindingPattern(n.name)) {
        const kind = requestPart(n.initializer);
        if (kind) for (const e of n.name.elements) {
          if (!e.dotDotDotToken) add(kind, e.propertyName ? (literal(e.propertyName) ?? e.propertyName.getText(sf)) : e.name.getText(sf), e);
        }
      }
      if (ts.isPropertyAccessExpression(n)) {
        const kind = requestPart(n.expression);
        if (kind) add(kind, n.name.text, n);
      } else if (ts.isElementAccessExpression(n)) {
        const kind = requestPart(n.expression);
        if (kind) add(kind, literal(n.argumentExpression), n);
      }
      ts.forEachChild(n, visit);
    }
    visit(root);
    parameterCache.set(key, empty);
    return empty;
  }
  function emit(method, p, origin, registration, handler, middlewareList, model = null, finale = null) {
    routes.push({ method: method.toUpperCase(), path: p, normalised_path: normalise(p), origin, registration, handler, middleware: middlewareList, model, finale, swagger: null, ...parameters(handler) });
  }
  function moduleFile(sf, node, imps) {
    if (!ts.isIdentifier(node)) return null;
    const binding = imps.get(node.text);
    return binding?.file ?? null;
  }
  function scanFile(file, base = '/', receiver = 'app') {
    const marker = `${file}:${base}`;
    if (active.has(marker)) return;
    active.add(marker);
    const sf = project.source(file), imps = imports(sf);
    const vars = new Map();
    function routeCall(node) {
      if (!ts.isCallExpression(node) || !ts.isPropertyAccessExpression(node.expression)) return null;
      const method = node.expression.name.text, obj = node.expression.expression;
      if (ts.isIdentifier(obj) && obj.text === receiver && (verbs.has(method) || method === 'use')) return { method, args: [...node.arguments], path: null };
      if (verbs.has(method) && ts.isCallExpression(obj) && ts.isPropertyAccessExpression(obj.expression)) {
        if (obj.expression.name.text === 'route' && ts.isIdentifier(obj.expression.expression) && obj.expression.expression.text === receiver) return { method, args: [...node.arguments], path: literal(obj.arguments[0]) };
        const prior = routeCall(obj);
        if (prior && prior.method !== 'use' && prior.path !== null) { processCall(obj, prior); return { method, args: [...node.arguments], path: prior.path }; }
      }
      return null;
    }
    function processCall(node, info) {
      let args = info.args, p = info.path;
      if (p === null && literal(args[0]) !== null) { p = literal(args[0]); args = args.slice(1); }
      if (info.method !== 'use' && p === null) return;
      p = join(base, p ?? '/');
      if (info.method === 'use') {
        for (const arg of args) {
          const mounted = moduleFile(sf, arg, imps);
          if (mounted) { scanFile(mounted, p, 'router'); continue; }
          globals.push({ path: p, middleware: middleware(arg, sf, 'global') });
        }
      } else {
        let handler = null, handlerIndex = -1;
        for (let i = args.length - 1; i >= 0; i--) { handler = resolve(args[i], sf, imps); if (handler) { handlerIndex = i; break; } }
        if (!handler && args.length && (ts.isArrowFunction(args.at(-1)) || ts.isFunctionExpression(args.at(-1)))) { const n = args.at(-1); handler = { name: n.name?.text ?? '<anonymous>', ...coord(sf, n) }; handlerIndex = args.length - 1; }
        emit(info.method, p, 'explicit', coord(sf, node), handler, [...chain(p), ...args.filter((_, i) => i !== handlerIndex).map(n => middleware(n, sf, 'route'))]);
      }
    }
    function finale(loop) {
      if (!ts.isForOfStatement(loop) || !ts.isIdentifier(loop.expression)) return false;
      const list = vars.get(loop.expression.text);
      if (!list || !ts.isArrayLiteralExpression(list)) return false;
      let call;
      function find(n) { if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.expression.getText(sf) === 'finale' && n.expression.name.text === 'resource') call = n; else ts.forEachChild(n, find); }
      find(loop.statement);
      if (!call || !ts.isObjectLiteralExpression(call.arguments[0])) return false;
      const endpoints = initializer(call.arguments[0], 'endpoints');
      if (!endpoints || !ts.isArrayLiteralExpression(endpoints) || endpoints.elements.length < 2) return false;
      for (const entry of list.elements) {
        if (!ts.isObjectLiteralExpression(entry)) continue;
        const name = literal(initializer(entry, 'name')); if (name === null) continue;
        const modelNode = initializer(entry, 'model');
        const model = modelNode?.getText(sf) ?? name;
        const exclude = initializer(entry, 'exclude'), include = initializer(entry, 'include');
        const render = n => {
          if (ts.isTemplateExpression(n)) return n.head.text + n.templateSpans.map(s => (s.expression.getText(sf) === 'name' ? name : '') + s.literal.text).join('');
          return literal(n);
        };
        // Finale defaults: https://raw.githubusercontent.com/tommybananas/finale/master/lib/Resource.js
        // Controller methods/plurality: https://github.com/tommybananas/finale/tree/master/lib/Controllers
        for (const [index, methods] of [[0, ['GET', 'POST']], [1, ['GET', 'PUT', 'DELETE']]]) {
          const rendered = render(endpoints.elements[index]); if (rendered === null) continue;
          const p = join(base, rendered);
          for (const method of methods) emit(method, p, 'finale', coord(sf, call), null, chain(p), model, { endpoint: index ? 'item' : 'collection', exclude_attributes: exclude ? arrayValues(exclude) : [], include: include ? arrayValues(include) : [], model_entry: coord(sf, entry) });
        }
      }
      return true;
    }
    function loggingCall(n) {
      if (!ts.isCallExpression(n)) return;
      const name = n.expression.getText(sf);
      if (name === 'getStream' && n.arguments[0] && ts.isObjectLiteralExpression(n.arguments[0])) {
        const obj = n.arguments[0];
        const val = k => { const v = initializer(obj, k); return v ? literal(v) ?? expression(v, sf) : null; };
        // A log file path is not a secret: unwrap path.resolve('<literal>') so the persisted file pattern is evidenced.
        const fileNode = initializer(obj, 'filename');
        const filename = fileNode && ts.isCallExpression(fileNode) && fileNode.expression.getText(sf) === 'path.resolve'
          && fileNode.arguments.length === 1 && literal(fileNode.arguments[0]) != null
          ? literal(fileNode.arguments[0]) : val('filename');
        const binding = ts.isVariableDeclaration(n.parent) && ts.isIdentifier(n.parent.name) ? n.parent.name.text : null;
        logging.push({ kind: 'rotation', binding, filename, frequency: val('frequency'), max_logs: val('max_logs'), date_format: val('date_format'), audit_file: val('audit_file'), source: coord(sf, n) });
      }
      if (name === 'morgan') {
        const options = n.arguments[1], stream = options && initializer(options, 'stream');
        logging.push({ kind: 'morgan', format: literal(n.arguments[0]), stream: stream ? expression(stream, sf) : null, source: coord(sf, n) });
      }
    }
    function visit(n) {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) vars.set(n.name.text, n.initializer);
      if (ts.isForOfStatement(n) && finale(n)) return;
      if (ts.isCallExpression(n)) {
        loggingCall(n);
        const info = routeCall(n);
        if (info) { processCall(n, info); for (const a of info.args) visit(a); return; }
      }
      ts.forEachChild(n, visit);
    }
    visit(sf); active.delete(marker);
  }
  if (project.has('server.ts')) scanFile('server.ts');
  if (project.has('swagger.yml')) {
    const file = 'swagger.yml', text = project.text(file), doc = parseDocument(text), root = doc.contents;
    const paths = root?.get('paths', true), servers = doc.get('servers');
    const server = servers?.items?.[0]?.get('url') ?? '';
    for (const pair of paths?.items ?? []) {
      const routePath = join(server || '/', String(pair.key.value));
      for (const operation of pair.value?.items ?? []) {
        const method = String(operation.key.value).toLowerCase(); if (!verbs.has(method)) continue;
        const info = { summary: operation.value?.get('summary') ?? null, parameters: operation.value?.get('parameters')?.toJSON() ?? [] };
        const found = routes.filter(r => r.method === method.toUpperCase() && r.normalised_path === normalise(routePath));
        if (found.length) for (const r of found) r.swagger = info;
        else { emit(method, routePath, 'swagger-only', textCoord(file, text, operation.key.range[0], operation.value.range[1]), null, []); routes.at(-1).swagger = info; }
      }
    }
  }
  return { routes, logging };
}
