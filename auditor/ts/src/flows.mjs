import path from 'node:path';
import { ts, coord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const name = n => n?.name && (ts.isIdentifier(n.name) || ts.isStringLiteral(n.name)) ? n.name.text : null;
const text = n => n?.getText() ?? '';
const inRange = (sf, node, source) => { const c = coord(sf, node); return c.start_line >= source.start_line && c.end_line <= source.end_line; };
const step = (id, operation, stage, source, note = '', relation = 'evidenced') => ({ element_id: id, operation, stage, source, origin: 'ts-join', relation, note });

function modelBindings(project, file, models) {
  if (!project.has(file)) return new Map();
  const sf = project.source(file), bindings = new Map();
  for (const s of sf.statements) {
    if (!ts.isImportDeclaration(s) || !s.importClause || !s.moduleSpecifier.text.startsWith('.')) continue;
    const base = path.posix.normalize(path.posix.join(path.posix.dirname(file), s.moduleSpecifier.text));
    const model = models.find(m => m.source.file.replace(/\.[cm]?[jt]s$/, '') === base);
    if (!model) continue;
    const clause = s.importClause;
    if (clause.name) bindings.set(clause.name.text, model);
    if (clause.namedBindings && ts.isNamedImports(clause.namedBindings)) for (const e of clause.namedBindings.elements) bindings.set(e.name.text, model);
  }
  // A model can also be declared in the route registration file.
  for (const m of models) if (m.source.file === file) {
    const source = project.source(file);
    walk(source, n => { if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === 'init' && inRange(source, n, m.source)) bindings.set(text(n.expression.expression), m); });
  }
  return bindings;
}

function serviceAccepts(project, serviceCall, argumentIndex) {
  const file = serviceCall.source.file;
  if (!project.has(file)) return false;
  const sf = project.source(file);
  let method, request;
  walk(sf, n => {
    if (ts.isMethodDeclaration(n) && name(n) === serviceCall.function && inRange(sf, n, { start_line: 1, end_line: Number.MAX_SAFE_INTEGER })) {
      const c = coord(sf, n);
      if (c.start_line <= serviceCall.source.start_line && c.end_line >= serviceCall.source.end_line) method = n;
    }
  });
  if (!method || !method.parameters[argumentIndex] || !ts.isIdentifier(method.parameters[argumentIndex].name)) return false;
  const parameter = method.parameters[argumentIndex].name.text;
  walk(method, n => {
    if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text.toUpperCase() === serviceCall.http_method && inRange(sf, n, serviceCall.source)) request = n;
  });
  if (!request || !request.arguments[1]) return false;
  let used = false;
  walk(request.arguments[1], n => { if (ts.isIdentifier(n) && n.text === parameter) used = true; });
  return used;
}

function componentInfo(project, form) {
  const file = form.source.file.replace(/\.html$/, '.ts');
  if (!project.has(file)) return null;
  const sf = project.source(file), services = new Map(), properties = new Map(), template = project.text(form.source.file).split('\n');
  walk(sf, n => {
    if (ts.isPropertyDeclaration(n) && name(n)) {
      if (n.initializer && ts.isCallExpression(n.initializer) && text(n.initializer.expression) === 'inject' && n.initializer.arguments[0]) services.set(name(n), text(n.initializer.arguments[0]));
      if (n.type && ts.isTypeReferenceNode(n.type)) services.set(name(n), text(n.type.typeName));
      if (n.initializer) properties.set(name(n), n.initializer);
    }
    if (ts.isParameter(n) && name(n) && n.type && ts.isTypeReferenceNode(n.type)) services.set(name(n), text(n.type.typeName));
  });
  return { sf, services, properties, template };
}

// Trace only explicit object members, spreads of a known signal model, and assignments
// to the actual argument. Do not connect fields merely because their names coincide.
function payloadFields(project, info, method, call, input, serviceCall) {
  const { sf, properties, template } = info, vars = new Map(), assignments = [];
  walk(method, n => {
    if (n.pos >= call.pos) return;
    if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) vars.set(n.name.text, n.initializer);
    if (ts.isBinaryExpression(n) && n.operatorToken.kind === ts.SyntaxKind.EqualsToken && ts.isPropertyAccessExpression(n.left)) assignments.push(n);
  });
  const matches = [];
  const usesInput = n => {
    let found = false;
    walk(n, x => { if (ts.isPropertyAccessExpression(x) && x.name.text === input.name) found = true; });
    return found;
  };
  function inspect(n, seen = new Set()) {
    if (!n) return;
    if (ts.isIdentifier(n) && vars.has(n.text) && !seen.has(n.text)) { seen.add(n.text); inspect(vars.get(n.text), seen); }
    if (ts.isPropertyAccessExpression(n) && n.expression.kind === ts.SyntaxKind.ThisKeyword) {
      for (const a of assignments) if (text(a.left.expression) === text(n) && usesInput(a.right)) matches.push({ field: a.left.name.text, node: a });
    }
    if (ts.isObjectLiteralExpression(n)) for (const p of n.properties) {
      if (ts.isPropertyAssignment(p) && usesInput(p.initializer)) matches.push({ field: name(p), node: p });
      if (ts.isShorthandPropertyAssignment(p) && p.name.text === input.name) matches.push({ field: p.name.text, node: p });
      if (ts.isSpreadAssignment(p)) inspect(p.expression, seen);
    }
    if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.expression.kind === ts.SyntaxKind.ThisKeyword) {
      const initializer = properties.get(n.expression.name.text);
      // Signal form model is tied to the template's form through form(this.model).
      const lines = template.slice(input.source.start_line - 1, input.source.end_line).join('\n');
      const binding = lines.match(/\[formField\]\s*=\s*["'](?:this\.)?([\w$]+)\./)?.[1];
      const formInitializer = properties.get(binding);
      const tied = formInitializer && ts.isCallExpression(formInitializer) && text(formInitializer.expression) === 'form' && text(formInitializer.arguments[0]) === text(n.expression);
      if (tied && initializer) {
        let found = false;
        const search = x => { if (ts.isPropertyAssignment(x) && name(x) === input.name) found = true; };
        walk(initializer, search);
        walk(initializer, x => {
          if (ts.isSpreadAssignment(x) && ts.isPropertyAccessExpression(x.expression) && x.expression.expression.kind === ts.SyntaxKind.ThisKeyword) {
            const spread = properties.get(x.expression.name.text);
            if (spread) walk(spread, search);
          }
        });
        if (found) matches.push({ field: input.name, node: n });
      }
    }
  }
  call.arguments.forEach((arg, index) => { if (serviceAccepts(project, serviceCall, index)) inspect(arg); });
  return matches.filter(x => x.field);
}

function responses(project, inventory, model, field) {
  const result = [];
  for (const route of inventory.routes ?? []) {
    if (route.method !== 'GET' || route.origin !== 'explicit' || !route.handler || !project.has(route.handler.file)) continue;
    const sf = project.source(route.handler.file), bindings = modelBindings(project, route.handler.file, inventory.models ?? []);
    const names = [...bindings].filter(([, m]) => m.name === model.name).map(([n]) => n);
    if (!names.length) continue;
    let handler;
    walk(sf, n => { if ((ts.isFunctionDeclaration(n) || ts.isArrowFunction(n) || ts.isFunctionExpression(n)) && inRange(sf, n, route.handler) && (!handler || n.end - n.pos > handler.end - handler.pos)) handler = n; });
    if (!handler) continue;
    const vars = new Set(), derived = new Set(), masked = new Set();
    walk(handler, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) {
        let found = false; walk(n.initializer, x => { if (ts.isCallExpression(x) && ts.isPropertyAccessExpression(x.expression) && names.includes(text(x.expression.expression)) && ['findAll','findOne','findByPk'].includes(x.expression.name.text)) found = true; });
        if (found) vars.add(n.name.text);
      }
    });
    if (!vars.size) continue;
    // Track derived response variables, including values populated in forEach callbacks.
    walk(handler, n => {
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === 'forEach' && vars.has(text(n.expression.expression))) {
        const cb = n.arguments[0]; if (cb?.parameters?.[0] && ts.isIdentifier(cb.parameters[0].name)) vars.add(cb.parameters[0].name.text);
      }
    });
    const references = (n, set) => { let found = false; walk(n, x => { if (ts.isIdentifier(x) && set.has(x.text)) found = true; }); return found; };
    // Resolve intermediate variables and output containers to a fixed point.
    for (let pass = 0; pass < 4; pass++) walk(handler, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer && references(n.initializer, new Set([...vars, ...derived]))) derived.add(n.name.text);
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === 'push' && n.arguments.some(a => references(a, derived))) derived.add(text(n.expression.expression));
      if (ts.isBinaryExpression(n) && ts.isPropertyAccessExpression(n.left) && n.operatorToken.kind === ts.SyntaxKind.EqualsToken && references(n.right, new Set([...vars, ...derived]))) derived.add(text(n.left.expression));
    });
    walk(handler, n => {
      let target, value;
      if (ts.isBinaryExpression(n) && ts.isPropertyAccessExpression(n.left) && n.left.name.text === field && n.operatorToken.kind === ts.SyntaxKind.EqualsToken) { target = text(n.left.expression); value = n.right; }
      if (ts.isPropertyAssignment(n) && name(n) === field && ts.isObjectLiteralExpression(n.parent) && ts.isVariableDeclaration(n.parent.parent)) { target = text(n.parent.parent.name); value = n.initializer; }
      if (target && value && /(?:replace|substring|slice|repeat|mask)/i.test(text(value))) masked.add(target);
    });
    walk(handler, n => {
      if (!ts.isCallExpression(n) || !ts.isPropertyAccessExpression(n.expression) || !['json','send'].includes(n.expression.name.text) || !/^res(?:\.|$)/.test(text(n.expression.expression)) || !n.arguments[0]) return;
      if (!references(n.arguments[0], new Set([...vars, ...derived]))) return;
      const isMasked = masked.size > 0;
      result.push({ source: coord(sf, n), note: isMasked ? 'masked' : '', route });
    });
  }
  return result;
}

function finaleResponseHook(project, route) {
  if (!project.has(route.registration.file)) return null;
  const sf = project.source(route.registration.file);
  let registration;
  walk(sf, n => {
    if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && text(n.expression) === 'finale.resource' && inRange(sf, n, route.registration)) registration = n;
  });
  let loop = registration;
  while (loop && !ts.isForOfStatement(loop)) loop = loop.parent;
  if (!loop) return null;
  let hook = null;
  walk(loop.statement, n => {
    if (ts.isCallExpression(n) && text(n.expression) === 'resource.all.send.before') hook = coord(sf, n);
  });
  return hook;
}

// Resolve collection imports to the declaration, not merely to a matching name.
function collectionReceiver(project, file, expression, collections) {
  const sf = project.source(file);
  for (const s of sf.statements) {
    if (!ts.isImportDeclaration(s) || !s.importClause?.namedBindings || !s.moduleSpecifier.text.startsWith('.')) continue;
    const base = path.posix.normalize(path.posix.join(path.posix.dirname(file), s.moduleSpecifier.text));
    const binding = s.importClause.namedBindings;
    for (const collection of collections) {
      if (collection.source.file.replace(/\.[cm]?[jt]s$/, '') !== base) continue;
      if (ts.isNamespaceImport(binding) && text(expression) === `${binding.name.text}.${collection.name}`) return collection;
      if (ts.isNamedImports(binding) && ts.isIdentifier(expression) && binding.elements.some(e => e.name.text === expression.text && (e.propertyName ?? e.name).text === collection.name)) return collection;
    }
  }
  return null;
}

function handlerNode(project, route) {
  if (!route.handler || !project.has(route.handler.file)) return null;
  const sf = project.source(route.handler.file);
  let handler;
  walk(sf, n => {
    if (ts.isFunctionDeclaration(n) && n.name?.text === route.handler.name && inRange(sf, n, route.handler)) handler = n;
  });
  return handler ? { sf, handler } : null;
}

function collectionReads(project, inventory, writeRoute, collection, field) {
  const out = [];
  for (const route of inventory.routes ?? []) {
    if (route.origin !== 'explicit' || route.method !== 'GET' || route.normalised_path !== writeRoute.normalised_path) continue;
    const resolved = handlerNode(project, route);
    if (!resolved) continue;
    const { sf, handler } = resolved;
    walk(handler, n => {
      if (!ts.isCallExpression(n) || !ts.isPropertyAccessExpression(n.expression) || n.expression.name.text !== 'then') return;
      const query = n.expression.expression, cb = n.arguments[0];
      if (!ts.isCallExpression(query) || !ts.isPropertyAccessExpression(query.expression) || query.expression.name.text !== 'find' || collectionReceiver(project, sf.fileName, query.expression.expression, [collection]) !== collection || query.arguments.length > 1) return;
      if (!cb || !(ts.isArrowFunction(cb) || ts.isFunctionExpression(cb)) || !cb.parameters[0] || !ts.isIdentifier(cb.parameters[0].name)) return;
      const records = cb.parameters[0].name.text;
      let changed = false;
      walk(cb.body, x => {
        if (ts.isDeleteExpression(x) && text(x.expression).includes(`.${field}`)) changed = true;
        if (ts.isBinaryExpression(x) && x.operatorToken.kind === ts.SyntaxKind.EqualsToken && text(x.left).includes(`.${field}`)) changed = true;
      });
      if (changed) return;
      walk(cb.body, x => {
        if (!ts.isCallExpression(x) || !ts.isPropertyAccessExpression(x.expression) || !['json', 'send'].includes(x.expression.name.text) || text(x.expression.expression) !== 'res' || !x.arguments[0]) return;
        const arg = x.arguments[0];
        // Permit the records themselves or a transparent, imported object wrapper.
        if (text(arg) !== records && !transparentWrapper(project, sf, arg, records)) return;
        out.push({ route, source: coord(sf, x) });
      });
    });
  }
  return out;
}

function transparentWrapper(project, sf, expression, records) {
  if (!ts.isCallExpression(expression) || expression.arguments.length !== 1 || text(expression.arguments[0]) !== records || !ts.isPropertyAccessExpression(expression.expression) || !ts.isIdentifier(expression.expression.expression)) return false;
  const namespace = expression.expression.expression.text, exported = expression.expression.name.text;
  for (const imp of sf.statements) {
    if (!ts.isImportDeclaration(imp) || !ts.isNamespaceImport(imp.importClause?.namedBindings) || imp.importClause.namedBindings.name.text !== namespace || !imp.moduleSpecifier.text.startsWith('.')) continue;
    const base = path.posix.normalize(path.posix.join(path.posix.dirname(sf.fileName), imp.moduleSpecifier.text));
    const file = [base + '.ts', base + '.js'].find(f => project.has(f));
    if (!file) continue;
    let valid = false;
    walk(project.source(file), n => {
      if (!ts.isVariableDeclaration(n) || name(n) !== exported || !n.initializer || !ts.isArrowFunction(n.initializer) || !n.initializer.parameters[0] || !ts.isIdentifier(n.initializer.parameters[0].name)) return;
      const parameter = n.initializer.parameters[0].name.text;
      walk(n.initializer.body, r => {
        if (!ts.isReturnStatement(r) || !r.expression || !ts.isObjectLiteralExpression(r.expression)) return;
        if (r.expression.properties.some(p => ts.isShorthandPropertyAssignment(p) && p.name.text === parameter || ts.isPropertyAssignment(p) && text(p.initializer) === parameter)) valid = true;
      });
    });
    if (valid) return true;
  }
  return false;
}

function collectionFlows(project, inventory) {
  const flows = [], collections = inventory.collections ?? [];
  for (const route of inventory.routes ?? []) {
    if (route.origin !== 'explicit' || !['POST', 'PUT', 'PATCH'].includes(route.method)) continue;
    const resolved = handlerNode(project, route);
    if (!resolved) continue;
    const { sf, handler } = resolved;
    walk(handler, insert => {
      if (!ts.isCallExpression(insert) || !ts.isPropertyAccessExpression(insert.expression) || insert.expression.name.text !== 'insert' || !insert.arguments[0] || !ts.isObjectLiteralExpression(insert.arguments[0])) return;
      const collection = collectionReceiver(project, sf.fileName, insert.expression.expression, collections);
      if (!collection) return;
      for (const prop of insert.arguments[0].properties) {
        const field = name(prop);
        if (!field || !ts.isPropertyAssignment(prop) || text(prop.initializer) !== `req.body.${field}` || !collection.fields.some(f => f.name === field)) continue;
        const reads = collectionReads(project, inventory, route, collection, field);
        if (!reads.length) continue;
        for (const serviceCall of inventory.service_calls ?? []) {
          if (serviceCall.http_method !== route.method || serviceCall.normalised_path !== route.normalised_path) continue;
          for (const file of project.files.filter(f => f.startsWith('frontend/') && f.endsWith('.component.ts'))) {
            const component = project.source(file), services = new Map();
            walk(component, n => {
              if (ts.isPropertyDeclaration(n) && name(n) && n.initializer && ts.isCallExpression(n.initializer) && text(n.initializer.expression) === 'inject') services.set(name(n), text(n.initializer.arguments[0]));
            });
            walk(component, method => {
              if (!ts.isMethodDeclaration(method) || !method.body) return;
              const vars = new Map();
              walk(method.body, n => { if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) vars.set(n.name.text, n.initializer); });
              walk(method.body, call => {
                if (!ts.isCallExpression(call) || !ts.isPropertyAccessExpression(call.expression) || !ts.isPropertyAccessExpression(call.expression.expression) || call.expression.expression.expression.kind !== ts.SyntaxKind.ThisKeyword || services.get(call.expression.expression.name.text) !== serviceCall.service || call.expression.name.text !== serviceCall.function) return;
                call.arguments.forEach((arg, index) => {
                  if (!serviceAccepts(project, serviceCall, index)) return;
                  const obj = ts.isIdentifier(arg) ? vars.get(arg.text) : arg;
                  if (!obj || !ts.isObjectLiteralExpression(obj)) return;
                  const member = obj.properties.find(p => name(p) === field && ts.isPropertyAssignment(p));
                  if (!member) return;
                  const id = `collection:${collection.name}.${field}`;
                  const steps = [step(id, 'Collect', 'component', coord(component, member)), step(id, 'Collect', 'service', serviceCall.source), step(id, 'Collect', 'route', route.registration, `${route.method} ${route.path}`), step(id, 'Collect', 'handler', coord(sf, prop.initializer)), step(id, 'Store', 'storage', coord(sf, prop), `insert into ${collection.name}`)];
                  for (const read of reads) steps.push(step(id, 'Expose', 'response', read.source, `${field} not projected out; ${read.route.method} ${read.route.path}`));
                  const flow = { element_id: id, steps };
                  // A signal populated by an account response is provenance, not a claim
                  // that the anonymous fallback always contains Personal Data.
                  if (ts.isCallExpression(member.initializer) && ts.isPropertyAccessExpression(member.initializer.expression) && member.initializer.expression.expression.kind === ts.SyntaxKind.ThisKeyword) {
                    const signal = member.initializer.expression.name.text;
                    walk(component, n => {
                      if (!ts.isCallExpression(n) || text(n.expression) !== `this.${signal}.set` || !n.arguments[0]) return;
                      let callback = n.parent;
                      while (callback && !ts.isArrowFunction(callback)) callback = callback.parent;
                      if (!callback?.parameters[0] || !ts.isIdentifier(callback.parameters[0].name)) return;
                      const account = callback.parameters[0].name.text;
                      let email = false;
                      walk(n.arguments[0], x => { if (ts.isPropertyAccessExpression(x) && x.name.text === 'email' && text(x.expression) === account) email = true; });
                      let subscription = callback.parent;
                      while (subscription && !(ts.isCallExpression(subscription) && ts.isPropertyAccessExpression(subscription.expression) && subscription.expression.name.text === 'subscribe')) subscription = subscription.parent;
                      let accountRequest = false;
                      if (subscription) walk(subscription.expression.expression, x => {
                        if (!ts.isCallExpression(x) || !ts.isPropertyAccessExpression(x.expression) || !ts.isPropertyAccessExpression(x.expression.expression) || x.expression.expression.expression.kind !== ts.SyntaxKind.ThisKeyword) return;
                        const service = services.get(x.expression.expression.name.text);
                        if ((inventory.service_calls ?? []).some(s => {
                          if (s.service !== service || s.function !== x.expression.name.text || s.http_method !== 'GET') return false;
                          return (inventory.routes ?? []).some(r => {
                            if (r.method !== 'GET' || r.normalised_path !== s.normalised_path?.split(/[?{]/)[0]) return false;
                            const accountHandler = handlerNode(project, r);
                            if (!accountHandler) return false;
                            let accountLookup = false, emailField = false;
                            walk(accountHandler.handler, node => {
                              if (ts.isCallExpression(node) && /authenticatedUsers\.get$/.test(text(node.expression))) accountLookup = true;
                              if (ts.isPropertyAccessExpression(node) && node.name.text === 'email') emailField = true;
                            });
                            return accountLookup && emailField;
                          });
                        })) accountRequest = true;
                      });
                      if (email && accountRequest && (inventory.models ?? []).some(m => m.name === 'User' && m.fields.some(f => f.name === 'email'))) {
                        flow.derived_from = ['model:User.email'];
                        steps.unshift(step(id, 'Collect', 'component', coord(component, n), 'Account email, or an anonymous fallback; model identity inferred from account response', 'inferred'));
                      }
                    });
                  }
                  flows.push(flow);
                });
              });
            });
          }
        }
      }
    });
  }
  return flows;
}

export function extractFlows(project, inventory) {
  const flows = collectionFlows(project, inventory), models = inventory.models ?? [], routes = inventory.routes ?? [];
  for (const form of inventory.forms ?? []) {
    const info = componentInfo(project, form); if (!info) continue;
    const { sf, services } = info;
    walk(sf, method => {
      if (!ts.isMethodDeclaration(method) || !method.body) return;
      walk(method.body, call => {
        if (!ts.isCallExpression(call) || !ts.isPropertyAccessExpression(call.expression) || !ts.isPropertyAccessExpression(call.expression.expression) || call.expression.expression.expression.kind !== ts.SyntaxKind.ThisKeyword) return;
        const service = services.get(call.expression.expression.name.text); if (!service) return;
        const calls = (inventory.service_calls ?? []).filter(s => s.service === service && s.function === call.expression.name.text && ['POST','PUT','PATCH'].includes(s.http_method));
        for (const serviceCall of calls) for (const route of routes.filter(r => r.method === serviceCall.http_method && r.normalised_path === serviceCall.normalised_path && r.origin !== 'swagger-only')) {
          let model = null, storeSource = null, storeCall = null, relation = 'evidenced';
          const bindings = modelBindings(project, route.registration.file, models);
          if (route.origin === 'finale') { model = bindings.get(route.model); storeSource = route.registration; relation = 'inferred'; }
          else if (route.handler && project.has(route.handler.file)) {
            const hsf = project.source(route.handler.file), hb = modelBindings(project, route.handler.file, models);
            walk(hsf, n => { if (inRange(hsf, n, route.handler) && ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && ['create','update','upsert'].includes(n.expression.name.text)) { const m = hb.get(text(n.expression.expression)); if (m) { model = m; storeSource = coord(hsf, n); storeCall = n; } } });
          }
          if (!model) continue;
          for (const input of form.inputs ?? []) for (const payload of payloadFields(project, info, method, call, input, serviceCall)) {
            const field = model.fields.find(f => f.name === payload.field); if (!field) continue;
            if (storeCall) {
              const argument = storeCall.arguments[0];
              if (!argument) continue;
              const directBody = text(argument) === 'req.body';
              const member = ts.isObjectLiteralExpression(argument) && argument.properties.some(p => name(p) === field.name && ts.isPropertyAssignment(p) && text(p.initializer) === `req.body.${field.name}`);
              if (!directBody && !member) continue;
            }
            const id = `model:${model.name}.${field.name}`;
            const steps = [step(id, 'Collect', 'form', input.source), step(id, 'Collect', 'component', coord(sf, payload.node)), step(id, 'Collect', 'service', serviceCall.source), step(id, 'Collect', 'route', route.registration, `${route.method} ${route.path}`, route.origin === 'finale' ? 'inferred' : 'evidenced')];
            // Explicit registrations on the same method/path precede finale's generated handler.
            if (route.origin === 'finale') for (const prior of routes.filter(r => r.origin === 'explicit' && r.method === route.method && r.normalised_path === route.normalised_path)) steps.push(step(id, 'Collect', 'middleware', prior.registration, `Explicit route before finale: ${prior.method} ${prior.path}`));
            for (const middleware of route.middleware ?? []) if (middleware.scope === 'route' || middleware.role === 'authentication' || middleware.role === 'identity') steps.push(step(id, 'Collect', 'middleware', middleware.source, `${middleware.role}: ${middleware.name}`));
            steps.push(step(id, 'Collect', 'handler', route.handler ?? route.registration, relation === 'inferred' ? 'finale generated handler' : '', relation));
            steps.push(step(id, 'Store', 'model', field.source, relation === 'inferred' ? 'finale generated model write' : `model write at ${storeSource.file}:${storeSource.start_line}`, relation));
            for (const r of responses(project, inventory, model, field.name)) steps.push(step(id, 'Expose', 'response', r.source, r.note));
            // Finale list/read response defaults apply only where an explicit handler does not intercept the same endpoint.
            for (const read of routes.filter(r => r.origin === 'finale' && r.method === 'GET' && r.model === route.model && !(r.finale?.exclude_attributes ?? []).includes(field.name))) {
              if (routes.some(r => r.origin === 'explicit' && r.method === 'GET' && r.normalised_path === read.normalised_path && r.handler)) continue;
              steps.push(step(id, 'Expose', 'response', read.registration, 'finale generated read response', 'inferred'));
              const hook = finaleResponseHook(project, read);
              if (hook) steps.push(step(id, 'Expose', 'response', hook, 'finale generated read response wrapper', 'inferred'));
            }
            flows.push({ element_id: id, steps });
          }
        }
      });
    });
  }
  return { flows };
}
