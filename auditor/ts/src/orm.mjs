// Mongoose schemas and ORM Processing Operations (Mongoose, Prisma client).
// Models are resolved by import identity (the file that declares or exports the model), never by field
// name. A Prisma delegate (`prisma.user`) is emitted as-is; the Python join resolves it against the
// parsed `schema.prisma`. A call whose receiver cannot be traced to a model or client is not emitted.
import path from 'node:path';
import { ts, coord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const lit = n => n && ts.isStringLiteralLike(n) ? n.text : null;
const unwrap = n => { while (n && (ts.isParenthesizedExpression(n) || ts.isAsExpression(n) || ts.isNonNullExpression(n) || ts.isAwaitExpression(n))) n = n.expression; return n; };
const key = p => p.name && (ts.isIdentifier(p.name) || ts.isStringLiteralLike(p.name)) ? p.name.text : null;
const object = (o, k) => o && ts.isObjectLiteralExpression(o) ? o.properties.find(p => key(p) === k) : null;
const parse = (project, file) => ts.createSourceFile(file, project.text(file), ts.ScriptTarget.Latest, true, /\.[cm]?js$/.test(file) ? ts.ScriptKind.JS : ts.ScriptKind.TS);
const SOURCE = /\.(?:[cm]?[jt]s)$/;
const READS = new Set(['find', 'findOne', 'findById', 'findMany', 'findUnique', 'findFirst', 'findUniqueOrThrow', 'findFirstOrThrow']);
const MONGOOSE_WRITES = new Set(['create', 'insertMany', 'updateOne', 'updateMany', 'findOneAndUpdate', 'findByIdAndUpdate', 'replaceOne', 'upsert']);
const PRISMA_WRITES = new Set(['create', 'createMany', 'update', 'updateMany', 'upsert']);

export function extractOrm(project) {
  const models = [], orm_operations = [], orm_connections = [];
  const files = project.files.filter(f => SOURCE.test(f) && !f.endsWith('.d.ts'));
  const sources = new Map(files.map(f => [f, parse(project, f)]));

  const isMongooseModelCall = (n, sf) => ts.isCallExpression(n) && /^(?:mongoose\.)?model$/.test(n.expression.getText(sf)) && lit(n.arguments[0]) !== null;
  const isSchemaNew = (n, sf) => ts.isNewExpression(n) && /^(?:mongoose\.|mongoose\.default\.)?Schema$/.test(n.expression.getText(sf));
  const hasPrismaClient = (n, sf) => { let hit = false; walk(n, x => { if (ts.isNewExpression(x) && x.expression.getText(sf) === 'PrismaClient') hit = true; }); return hit; };

  // Pass 1: Mongoose schemas -> models; per-file symbol tables of locals and exports.
  const locals = new Map(), exportsOf = new Map();
  function schemaFields(obj, sf, file, prefix = '') {
    const out = [];
    for (const p of obj.properties) {
      const name = key(p); if (!name || !ts.isPropertyAssignment(p)) continue;
      const v = unwrap(p.initializer), full = prefix + name;
      if (ts.isObjectLiteralExpression(v) && !object(v, 'type')) { out.push(...schemaFields(v, sf, file, full + '.')); continue; }
      const options = ts.isObjectLiteralExpression(v) ? v : null;
      const type = options ? propText(object(options, 'type'), sf) : v.getText(sf);
      const required = options && object(options, 'required');
      const def = options && object(options, 'default');
      out.push({
        name: full, type: type?.replace(/\s+/g, ' ').slice(0, 60) ?? null,
        allow_null: !(required && (propExpr(required)?.kind === ts.SyntaxKind.TrueKeyword || (propExpr(required) && ts.isArrayLiteralExpression(propExpr(required))))),
        // A default may be a secret: presence only.
        default: def ? '<default>' : null,
        unique: !!(options && propExpr(object(options, 'unique'))?.kind === ts.SyntaxKind.TrueKeyword) || null,
        validators: options ? ['match', 'validate', 'enum', 'minlength', 'maxlength', 'min', 'max'].filter(k => object(options, k)) : [],
        source: coord(sf, p),
      });
    }
    return out;
  }
  const propExpr = p => p && ts.isPropertyAssignment(p) ? unwrap(p.initializer) : null;
  const propText = (p, sf) => propExpr(p)?.getText(sf) ?? null;

  for (const [file, sf] of sources) {
    const schemas = new Map(), table = new Map(), exportsHere = new Map();
    walk(sf, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) {
        const init = unwrap(n.initializer);
        if (isSchemaNew(init, sf) && init.arguments?.[0] && ts.isObjectLiteralExpression(unwrap(init.arguments[0]))) schemas.set(n.name.text, { node: init, fields: schemaFields(unwrap(init.arguments[0]), sf, file), source: coord(sf, n) });
      }
    });
    function modelFrom(call) {
      const name = lit(call.arguments[0]);
      let schema = call.arguments[1] && unwrap(call.arguments[1]);
      const entry = schema && ts.isIdentifier(schema) ? schemas.get(schema.text)
        : schema && isSchemaNew(schema, sf) && schema.arguments?.[0] && ts.isObjectLiteralExpression(unwrap(schema.arguments[0])) ? { fields: schemaFields(unwrap(schema.arguments[0]), sf, file), source: coord(sf, schema) } : null;
      if (!entry) return null;
      const record = { name, table: null, kind: 'mongoose', source: entry.source, options: {}, fields: entry.fields };
      if (!models.some(m => m.name === name && m.source.file === file)) models.push(record);
      return { name, file };
    }
    const here = new Map();
    walk(sf, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer) {
        const init = unwrap(n.initializer);
        let call = isMongooseModelCall(init, sf) ? init : null;
        // `mongoose.models.User || mongoose.model('User', schema)` (hot-reload guard)
        if (!call && ts.isBinaryExpression(init)) { const r = unwrap(init.right); if (isMongooseModelCall(r, sf)) call = r; }
        if (call) { const m = modelFrom(call); if (m) here.set(n.name.text, { model: m }); }
        else if (hasPrismaClient(init, sf)) here.set(n.name.text, { prisma: true });
        else if (ts.isIdentifier(init) && here.has(init.text)) here.set(n.name.text, here.get(init.text));
      }
    });
    // Exports (ES and CommonJS).
    const exportable = (expr) => { const e = unwrap(expr); if (!e) return null; if (ts.isIdentifier(e)) return here.get(e.text) ?? null; if (isMongooseModelCall(e, sf)) { const m = modelFrom(e); return m ? { model: m } : null; } return hasPrismaClient(e, sf) ? { prisma: true } : null; };
    for (const s of sf.statements) {
      if (ts.isVariableStatement(s) && s.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword)) for (const d of s.declarationList.declarations) if (ts.isIdentifier(d.name) && here.has(d.name.text)) exportsHere.set(d.name.text, here.get(d.name.text));
      if (ts.isExportAssignment(s)) { const v = exportable(s.expression); if (v) exportsHere.set('default', v); }
      if (ts.isExportDeclaration(s) && s.exportClause && ts.isNamedExports(s.exportClause) && !s.moduleSpecifier) for (const e of s.exportClause.elements) { const v = here.get((e.propertyName ?? e.name).text); if (v) exportsHere.set(e.name.text, v); }
      if (ts.isExpressionStatement(s) && ts.isBinaryExpression(s.expression) && s.expression.operatorToken.kind === ts.SyntaxKind.EqualsToken) {
        const left = s.expression.left.getText(sf), right = unwrap(s.expression.right);
        if (left === 'module.exports') {
          const v = exportable(right);
          if (v) exportsHere.set('default', v);
          else if (ts.isObjectLiteralExpression(right)) for (const p of right.properties) { const name = key(p); const val = ts.isShorthandPropertyAssignment(p) ? here.get(p.name.text) : ts.isPropertyAssignment(p) ? exportable(p.initializer) : null; if (name && val) exportsHere.set(name, val); }
        } else if (/^(?:module\.)?exports\.\w+$/.test(left)) { const v = exportable(right); if (v) exportsHere.set(left.split('.').at(-1), v); }
      }
    }
    locals.set(file, here); exportsOf.set(file, exportsHere);
  }

  function resolveFile(from, spec) {
    if (!spec.startsWith('.')) return null;
    const base = path.posix.normalize(path.posix.join(path.posix.dirname(from), spec)).replace(/\.[cm]?js$/, '');
    return ['.ts', '.js', '.mjs', '.cjs', '/index.ts', '/index.js'].map(e => base + e).find(f => sources.has(f)) ?? (sources.has(base) ? base : null);
  }

  // Pass 2: bindings per file, then operations.
  for (const [file, sf] of sources) {
    const bound = new Map(locals.get(file));
    for (const s of sf.statements) {
      if (ts.isImportDeclaration(s) && s.importClause && ts.isStringLiteral(s.moduleSpecifier)) {
        const target = resolveFile(file, s.moduleSpecifier.text); if (!target) continue;
        const ex = exportsOf.get(target), c = s.importClause;
        if (c.name && ex.has('default')) bound.set(c.name.text, ex.get('default'));
        if (c.namedBindings && ts.isNamedImports(c.namedBindings)) for (const e of c.namedBindings.elements) { const v = ex.get((e.propertyName ?? e.name).text); if (v) bound.set(e.name.text, v); }
      }
      if (ts.isVariableStatement(s)) for (const d of s.declarationList.declarations) {
        const init = d.initializer && unwrap(d.initializer);
        if (init && ts.isCallExpression(init) && init.expression.getText(sf) === 'require' && lit(init.arguments[0])) {
          const target = resolveFile(file, lit(init.arguments[0])); if (!target) continue;
          const ex = exportsOf.get(target);
          if (ts.isIdentifier(d.name) && ex.has('default')) bound.set(d.name.text, ex.get('default'));
          else if (ts.isObjectBindingPattern(d.name)) for (const e of d.name.elements) { const v = ex.get((e.propertyName ?? e.name).text); if (v) bound.set(e.name.text, v); }
        }
      }
    }
    // Transaction callbacks: prisma.$transaction(async tx => ...) binds tx to the client.
    walk(sf, n => {
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && n.expression.name.text === '$transaction' && ts.isIdentifier(n.expression.expression) && bound.get(n.expression.expression.text)?.prisma) {
        const cb = n.arguments[0] && unwrap(n.arguments[0]);
        if (cb && (ts.isArrowFunction(cb) || ts.isFunctionExpression(cb)) && cb.parameters[0] && ts.isIdentifier(cb.parameters[0].name)) bound.set(cb.parameters[0].name.text, { prisma: true });
      }
      if (ts.isCallExpression(n) && /^(?:mongoose\.)?connect$/.test(n.expression.getText(sf)) && /mongoose/.test(sf.text)) {
        const arg = n.arguments[0] && unwrap(n.arguments[0]);
        const env = arg && /^process\.env\.(\w+)$/.exec(arg.getText(sf));
        orm_connections.push({ orm: 'mongoose', env: env ? env[1] : null, source: coord(sf, n) });
      }
    });

    // Request keys: `req.body.x`, `req.body['x']`, or an identifier destructured from req.body.
    function requestKeys(fn) {
      const aliases = new Map(), req = new Set(['req', 'request']);
      if (fn && fn.parameters?.[0] && ts.isIdentifier(fn.parameters[0].name)) req.add(fn.parameters[0].name.text);
      const isBody = e => { e = unwrap(e); return e && ts.isPropertyAccessExpression(e) && e.name.text === 'body' && ts.isIdentifier(e.expression) && req.has(e.expression.text); };
      if (fn) walk(fn, n => {
        if (ts.isVariableDeclaration(n) && n.initializer && ts.isObjectBindingPattern(n.name) && isBody(n.initializer))
          for (const e of n.name.elements) if (ts.isIdentifier(e.name)) aliases.set(e.name.text, (e.propertyName ?? e.name).getText(sf));
      });
      return { isBody, aliases };
    }
    function enclosingFunction(n) { for (let p = n.parent; p; p = p.parent) if (ts.isFunctionLike(p)) return p; return null; }
    function valueKey(v, rk) {
      let found = null, whole = false;
      const visit = x => {
        if (!x || found) return;
        if (ts.isPropertyAccessExpression(x) && rk.isBody(x.expression)) { found = x.name.text; return; }
        if (ts.isElementAccessExpression(x) && rk.isBody(x.expression) && lit(x.argumentExpression)) { found = lit(x.argumentExpression); return; }
        if (ts.isIdentifier(x) && rk.aliases.has(x.text)) { found = rk.aliases.get(x.text); return; }
        ts.forEachChild(x, visit);
      };
      visit(v);
      if (!found && rk.isBody(v)) whole = true;
      return { request_key: found, whole_body: whole };
    }
    function dataFields(obj, rk, skip = new Set()) {
      const out = [];
      obj = obj && unwrap(obj);
      if (!obj || !ts.isObjectLiteralExpression(obj)) return obj && rk.isBody(obj) ? [{ field: null, request_key: null, whole_body: true, source: coord(sf, obj) }] : out;
      for (const p of obj.properties) {
        if (ts.isSpreadAssignment(p)) { if (rk.isBody(p.expression)) out.push({ field: null, request_key: null, whole_body: true, source: coord(sf, p) }); continue; }
        const name = key(p); if (!name) continue;
        if (name === '$set' && ts.isPropertyAssignment(p)) { out.push(...dataFields(p.initializer, rk)); continue; }
        if (name.startsWith('$') || skip.has(name)) continue;
        const v = ts.isShorthandPropertyAssignment(p) ? p.name : ts.isPropertyAssignment(p) ? p.initializer : null;
        out.push({ field: name, ...(v ? valueKey(v, rk) : { request_key: null, whole_body: false }), source: coord(sf, p) });
      }
      return out;
    }

    walk(sf, n => {
      // Prisma: <client>.<delegate>.<method>(...)
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && ts.isPropertyAccessExpression(n.expression.expression)) {
        const method = n.expression.name.text, delegate = n.expression.expression, client = delegate.expression;
        if (ts.isIdentifier(client) && bound.get(client.text)?.prisma && !delegate.name.text.startsWith('$')) {
          const rk = requestKeys(enclosingFunction(n)), arg = n.arguments[0] && unwrap(n.arguments[0]);
          let fields = [];
          const write = PRISMA_WRITES.has(method);
          if (write && arg && ts.isObjectLiteralExpression(arg)) {
            for (const k of ['data', 'create', 'update']) { const p = object(arg, k); if (p) fields.push(...dataFields(ts.isPropertyAssignment(p) ? p.initializer : p.name, rk)); }
          }
          if (write || READS.has(method)) orm_operations.push({ orm: 'prisma', model: null, delegate: delegate.name.text, model_file: null, operation: method, access: write ? 'write' : 'read', binding: client.text, data_fields: fields, source: coord(sf, n) });
        }
      }
      // Mongoose: Model.<method>(...) and new Model(...)
      if (ts.isCallExpression(n) && ts.isPropertyAccessExpression(n.expression) && ts.isIdentifier(n.expression.expression)) {
        const b = bound.get(n.expression.expression.text), method = n.expression.name.text;
        if (b?.model && (MONGOOSE_WRITES.has(method) || READS.has(method))) {
          const rk = requestKeys(enclosingFunction(n));
          const write = MONGOOSE_WRITES.has(method);
          let fields = [];
          if (write) {
            const args = ['create', 'insertMany'].includes(method) ? [n.arguments[0]] : [n.arguments[1]];
            for (const a of args) { const u = a && unwrap(a); if (u && ts.isArrayLiteralExpression(u)) for (const el of u.elements) fields.push(...dataFields(el, rk)); else fields.push(...dataFields(u, rk)); }
          }
          orm_operations.push({ orm: 'mongoose', model: b.model.name, delegate: null, model_file: b.model.file, operation: method, access: write ? 'write' : 'read', binding: n.expression.expression.text, data_fields: fields, source: coord(sf, n) });
        }
      }
      if (ts.isNewExpression(n) && ts.isIdentifier(n.expression)) {
        const b = bound.get(n.expression.text);
        if (b?.model) {
          const rk = requestKeys(enclosingFunction(n));
          orm_operations.push({ orm: 'mongoose', model: b.model.name, delegate: null, model_file: b.model.file, operation: 'new', access: 'write', binding: n.expression.text, data_fields: dataFields(n.arguments?.[0], rk), source: coord(sf, n) });
        }
      }
    });
  }
  return { models, orm_operations, orm_connections };
}
