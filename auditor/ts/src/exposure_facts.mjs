import { ts, coord } from './project.mjs';

// Facts used by the route-exposure Rules: statically served directories, file writes and
// Sequelize/MarsDB model queries. Literal values are not emitted except path-like strings,
// which are needed to relate a write to the directory it lands in.
const SERVERS = new Set(['serveIndex', 'express.static', 'serveStatic']);
const WRITES = /(?:^|\.)(createWriteStream|writeFile|writeFileSync|appendFile|appendFileSync)$/;
const QUERIES = new Set(['findAll', 'findOne', 'findByPk', 'findAndCountAll', 'find', 'findById']);
const VERBS = new Set(['use', 'get', 'post', 'put', 'delete', 'patch']);
const strLit = n => n && (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) ? n.text : null;
const AUTH = /(?:^|\.)(isAuthorized|denyAll)$/;

function walk(node, fn) { fn(node); ts.forEachChild(node, c => walk(c, fn)); }

const receiverName = r => ts.isIdentifier(r) ? r.text : ts.isPropertyAccessExpression(r) ? r.name.text : null;
const FUNCTIONS = n => ts.isFunctionDeclaration(n) || ts.isFunctionExpression(n) || ts.isArrowFunction(n) || ts.isMethodDeclaration(n);
const RESPONSE = new Set(['json', 'send', 'jsonp']);
// Calls that keep the identity of a model row: the returned value is the same instance.
const SAME_ROW = new Set(['update', 'save', 'reload']);
const stripWrappers = n => { while (n && (ts.isAwaitExpression(n) || ts.isParenthesizedExpression(n) || ts.isAsExpression(n) || ts.isNonNullExpression(n))) n = n.expression; return n; };

function functionOf(node) { for (let n = node.parent; n; n = n.parent) if (FUNCTIONS(n)) return n; return null; }

// Bind the existing AST with TypeScript's lexical resolver, without loading libraries,
// following imports, or giving the compiler access to any other file.
function localBindings(sf) {
  let checker, uses;
  function symbol(node) {
    checker ??= ts.createProgram([sf.fileName], { noLib: true, noResolve: true, allowJs: true }, {
      getSourceFile: name => name === sf.fileName ? sf : undefined,
      getDefaultLibFileName: () => '',
      fileExists: name => name === sf.fileName,
      readFile: name => name === sf.fileName ? sf.text : undefined,
      getCurrentDirectory: () => '',
      getCanonicalFileName: name => name,
      useCaseSensitiveFileNames: () => true,
    }).getTypeChecker();
    return ts.isShorthandPropertyAssignment(node.parent) && node.parent.name === node
      ? checker.getShorthandAssignmentValueSymbol(node.parent)
      : checker.getSymbolAtLocation(node);
  }
  function declaration(node) {
    const d = symbol(node)?.valueDeclaration;
    return d && (ts.isVariableDeclaration(d) || ts.isParameter(d)) ? d : null;
  }
  function references(d) {
    if (!uses) {
      uses = new Map();
      walk(sf, node => {
        if (!ts.isIdentifier(node)) return;
        const binding = declaration(node);
        if (!binding || node === binding.name) return;
        if (!uses.has(binding)) uses.set(binding, []);
        uses.get(binding).push(node);
      });
    }
    return uses.get(d) ?? [];
  }
  return { declaration, references };
}

// Only follow values actually written to the response body. A row in a returned
// array/object or passed to a known serializer is evidence; a count, predicate, or
// argument to an opaque function is not.
function serializedBindings(expr, declaration, emit, how = 'direct', inRowMapper = false) {
  expr = stripWrappers(expr);
  if (ts.isIdentifier(expr)) { emit(declaration(expr), how); return; }
  if (inRowMapper && ts.isPropertyAccessExpression(expr) && expr.name.text === 'dataValues') {
    serializedBindings(expr.expression, declaration, emit, how, inRowMapper);
  } else if (ts.isObjectLiteralExpression(expr)) {
    for (const p of expr.properties) {
      const value = ts.isShorthandPropertyAssignment(p) ? p.name :
        ts.isPropertyAssignment(p) ? p.initializer : ts.isSpreadAssignment(p) ? p.expression : null;
      if (value) serializedBindings(value, declaration, emit, how === 'direct' ? 'wrapped' : how, inRowMapper);
    }
  } else if (ts.isArrayLiteralExpression(expr)) {
    for (const item of expr.elements) serializedBindings(ts.isSpreadElement(item) ? item.expression : item,
      declaration, emit, how === 'direct' ? 'wrapped' : how, inRowMapper);
  } else if (ts.isCallExpression(expr) && expr.arguments[0]) {
    const callee = expr.expression;
    const method = receiverName(callee);
    if (method === 'queryResultToJson' || (ts.isPropertyAccessExpression(callee) && method === 'stringify' &&
        ts.isIdentifier(callee.expression) && callee.expression.text === 'JSON')) {
      serializedBindings(expr.arguments[0], declaration, emit, 'serialized', inRowMapper);
    } else if (method === 'map' && ts.isPropertyAccessExpression(callee)) {
      const cb = expr.arguments[0];
      const row = (ts.isArrowFunction(cb) || ts.isFunctionExpression(cb)) && cb.parameters[0];
      if (!row || !ts.isIdentifier(row.name)) return;
      function serializesRow(result) {
        let found = false;
        if (result) serializedBindings(result, declaration, d => { found ||= d === row; }, 'serialized', true);
        return found;
      }
      function returnsRow(node) {
        if (ts.isReturnStatement(node)) return serializesRow(node.expression);
        if (!ts.isFunctionLike(node)) return ts.forEachChild(node, returnsRow);
      }
      if (ts.isBlock(cb.body) ? returnsRow(cb.body) : serializesRow(cb.body)) {
        serializedBindings(callee.expression, declaration, emit, 'serialized', inRowMapper);
      }
    }
  }
}

// Visit each response once. Cache same-row alias origins rather than scanning the
// enclosing function for every query or comparing names across nested scopes.
function connectResponses(calls, queries, declaration, sf) {
  const origins = new Map();
  function queryFor(binding) {
    const chain = [];
    while (binding && !queries.has(binding) && !origins.has(binding)) {
      origins.set(binding, null); // Also stops self-references and alias cycles.
      chain.push(binding);
      let value = stripWrappers(binding.initializer);
      if (value && ts.isCallExpression(value) && ts.isPropertyAccessExpression(value.expression) &&
          SAME_ROW.has(value.expression.name.text)) value = stripWrappers(value.expression.expression);
      binding = value && ts.isIdentifier(value) ? declaration(value) : null;
    }
    const query = queries.get(binding) ?? origins.get(binding);
    for (const alias of chain) origins.set(alias, query);
    return query;
  }
  for (const call of calls) {
    const sent = new Map();
    serializedBindings(call.arguments[0], declaration, (binding, how) => {
      const query = queryFor(binding);
      if (query && (!sent.has(query) || how !== 'serialized')) sent.set(query, how);
    });
    if (sent.size) {
      const source = coord(sf, call);
      for (const [query, how] of sent) query.responses.push({ how, source });
    }
  }
}

// True when `expr` is (transitively, through local variables) computed from request input.
function fromRequest(expr, declaration, depth = 0, seen = new Set()) {
  let hit = false;
  seen.add(expr);
  walk(expr, n => {
    if (hit) return;
    if (ts.isPropertyAccessExpression(n) && /^(query|body|params)$/.test(n.name.text)) hit = true;
    if (!ts.isIdentifier(n) || (ts.isPropertyAccessExpression(n.parent) && n.parent.name === n)) return;
    if (/^(query|body|params)$/.test(n.text)) hit = true;
    else if (depth <= 4) {
      const init = declaration(n)?.initializer;
      if (init && !seen.has(init)) hit = fromRequest(init, declaration, depth + 1, seen);
    }
  });
  return hit;
}

function declaredType(d, sf) {
  return d?.type && ts.isTypeReferenceNode(d.type) ? d.type.typeName.getText(sf) : null;
}

function maskLiterals(node, sf) {
  const start = node.getStart(sf), spans = [];
  walk(node, n => { if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n) || ts.isNumericLiteral(n)) spans.push([n.getStart(sf) - start, n.end - start]); });
  let text = node.getText(sf);
  for (const [a, b] of spans.reverse()) text = text.slice(0, a) + '<literal>' + text.slice(b);
  return text;
}

function enclosingFunction(node, sf) {
  const fn = functionOf(node);
  return fn ? coord(sf, fn) : null;
}

// Resolve only earlier local const declarations, stopping at shadowing bindings. The
// disambiguation proof below deliberately does not follow mutable or imported values.
function constValue(node) {
  node = stripWrappers(node);
  while (node && ts.isIdentifier(node)) {
    const name = node.text;
    let value;
    for (let child = node; child.parent; child = child.parent) {
      const scope = child.parent;
      if (FUNCTIONS(scope) && scope.parameters.some(p => ts.isIdentifier(p.name) && p.name.text === name)) break;
      if (!ts.isBlock(scope)) continue;
      for (let i = scope.statements.indexOf(child) - 1; i >= 0 && value === undefined; i--) {
        const stmt = scope.statements[i];
        if (!ts.isVariableStatement(stmt)) continue;
        const decl = stmt.declarationList.declarations.find(d => ts.isIdentifier(d.name) && d.name.text === name);
        if (decl) value = stmt.declarationList.flags & ts.NodeFlags.Const ? decl.initializer ?? null : null;
      }
      if (value !== undefined) break;
    }
    if (!value) break;
    node = stripWrappers(value);
  }
  return node;
}

function principal(node, sf) {
  if (ts.isPropertyAccessExpression(node) && /^(?:(?:req|request)\.user|(?:res|response)\.locals\.user)$/.test(node.getText(sf))) return node.getText(sf);
  if (!ts.isCallExpression(node) || !/(?:^|\.)authenticatedUsers\.get$/.test(node.expression.getText(sf))) return null;
  if (!node.arguments[0] || !/^(?:req|request)\??\.(?:cookies|headers|session)\b/.test(constValue(node.arguments[0]).getText(sf))) return null;
  return node;
}

const STRING_TRANSFORMS = new Set(['replace', 'replaceAll', 'slice', 'substring', 'substr', 'trim', 'toLowerCase', 'toUpperCase']);
const DIGEST = /^(?:[\w$]+\.)*(?:hash|digest)$/;
const NUMBER_KEY = `${ts.SyntaxKind.NumericLiteral}:`;
const literalKey = node => ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node) ? `string:${node.text}` :
  ts.isNumericLiteral(node) || ts.isRegularExpressionLiteral(node) ? `${node.kind}:${node.text}` : null;

// Describe a key as one owner's field plus a sequence of deterministic, literal-parameter
// transforms. For a candidate account the same field and transforms must be checked.
function ownerKey(expr, sf, account = null) {
  const node = constValue(expr);
  if (!node) return null;
  if (ts.isPropertyAccessExpression(node) && !node.questionDotToken) {
    let root = constValue(node.expression);
    if (!account && ts.isPropertyAccessExpression(root) && !root.questionDotToken && root.name.text === 'data') root = constValue(root.expression);
    const owner = account ? (ts.isIdentifier(root) && root.text === account.text ? account : null) : principal(root, sf);
    if (owner) return { owner, field: node.name.text, steps: [] };
  }
  if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const right = literalKey(node.right);
    if (!right?.startsWith('string:')) return null;
    const base = ownerKey(node.left, sf, account);
    if (base) base.steps.push(['+', right]);
    return base;
  }
  if (!ts.isCallExpression(node) || node.questionDotToken) return null;
  const callee = node.expression;
  let base, operation, args = node.arguments;
  if (ts.isPropertyAccessExpression(callee) && !callee.questionDotToken && STRING_TRANSFORMS.has(callee.name.text)) {
    base = ownerKey(callee.expression, sf, account);
    operation = callee.name.text;
  } else if (args[0] && DIGEST.test(callee.getText(sf))) {
    base = ownerKey(args[0], sf, account);
    operation = callee.getText(sf);
    args = args.slice(1);
  }
  if (!base) return null;
  const literals = args.map(literalKey);
  if (literals.includes(null)) return null;
  base.steps.push([operation, ...literals]);
  return base;
}

const sameKey = (left, right) => left.field === right.field && left.steps.length === right.steps.length &&
  left.steps.every((step, i) => step.length === right.steps[i].length && step.every((part, j) => part === right.steps[i][j]));

// Unequal variable-length prefixes can both match the same row. Equality of
// the derived keys rules out overlap for a fixed slice of a digest instead.
function fixedDigestPrefix(key) {
  if (!key) return false;
  const [digest, slice, suffix] = key.steps;
  return key.steps.length <= 3 && DIGEST.test(digest?.[0] ?? '') &&
    slice?.length === 3 && slice[0] === 'slice' && slice[1] === `${NUMBER_KEY}0` &&
    slice[2].startsWith(NUMBER_KEY) && Number(slice[2].slice(NUMBER_KEY.length)) > 0 &&
    (!suffix || suffix[0] === '+');
}

function predicate(call) {
  if (call.arguments.length !== 1) return null;
  const cb = call.arguments[0];
  if (!(ts.isArrowFunction(cb) || ts.isFunctionExpression(cb)) || cb.modifiers?.some(m => m.kind === ts.SyntaxKind.AsyncKeyword)) return null;
  const param = cb.parameters[0]?.name;
  const body = ts.isBlock(cb.body) && cb.body.statements.length === 1 && ts.isReturnStatement(cb.body.statements[0]) ?
    cb.body.statements[0].expression : cb.body;
  return param && ts.isIdentifier(param) && body && !ts.isBlock(body) ? { param, body: stripWrappers(body) } : null;
}

function rowKey(expr, row) {
  expr = stripWrappers(expr);
  return ts.isPropertyAccessExpression(expr) && !expr.questionDotToken && ts.isIdentifier(expr.expression) && expr.expression.text === row.text ? expr.name.text : null;
}

function filterKey(filter, sf, firstField) {
  const pred = predicate(filter);
  if (!pred) return null;
  const { param, body } = pred;
  if (ts.isCallExpression(body) && !body.questionDotToken && ts.isPropertyAccessExpression(body.expression) &&
      !body.expression.questionDotToken && body.expression.name.text === 'startsWith' && body.arguments.length === 1) {
    const field = rowKey(body.expression.expression, param);
    const key = field && field !== firstField ? ownerKey(body.arguments[0], sf) : null;
    return fixedDigestPrefix(key) ? key : null;
  }
  if (ts.isBinaryExpression(body) && body.operatorToken.kind === ts.SyntaxKind.EqualsEqualsEqualsToken) {
    for (const [row, value] of [[body.left, body.right], [body.right, body.left]]) {
      const field = rowKey(row, param);
      if (field && field !== firstField) return ownerKey(value, sf);
    }
  }
  return null;
}

// Only an unscoped account enumeration, including soft-deleted accounts, can
// support this proof. A projection is safe only if it includes the compared fields.
function allAccounts(expr, fields) {
  const call = constValue(expr);
  if (!ts.isCallExpression(call) || call.questionDotToken || !ts.isPropertyAccessExpression(call.expression) ||
      call.expression.questionDotToken || call.expression.name.text !== 'findAll' || call.arguments.length !== 1) return false;
  const options = call.arguments[0];
  if (!ts.isObjectLiteralExpression(options)) return false;
  let includeDeleted = false;
  for (const option of options.properties) {
    if (!ts.isPropertyAssignment(option)) return false;
    const name = ts.isIdentifier(option.name) ? option.name.text : strLit(option.name);
    if (name === 'paranoid' && option.initializer.kind === ts.SyntaxKind.FalseKeyword) includeDeleted = true;
    else if (name !== 'attributes' || !ts.isArrayLiteralExpression(option.initializer) ||
             !fields.every(field => option.initializer.elements.some(el => strLit(el) === field))) return false;
  }
  return includeDeleted;
}

function rejectsCollision(stmt, first, second, sf) {
  if (!ts.isIfStatement(stmt)) return false;
  const exit = ts.isBlock(stmt.thenStatement) ? stmt.thenStatement.statements.at(-1) : stmt.thenStatement;
  if (!exit || !(ts.isReturnStatement(exit) || ts.isThrowStatement(exit))) return false;
  const test = constValue(stmt.expression);
  if (!ts.isCallExpression(test) || test.questionDotToken || !ts.isPropertyAccessExpression(test.expression) ||
      test.expression.questionDotToken || test.expression.name.text !== 'some') return false;
  const pred = predicate(test);
  if (!pred) return false;
  let matchedFirst = false, matchedSecond = false, identity = null;
  function matchesTerms(node) {
    node = stripWrappers(node);
    if (ts.isBinaryExpression(node)) {
      const op = node.operatorToken.kind;
      if (op === ts.SyntaxKind.AmpersandAmpersandToken) return matchesTerms(node.left) && matchesTerms(node.right);
      for (const [candidate, expected] of [[node.left, node.right], [node.right, node.left]]) {
        const key = ownerKey(candidate, sf, pred.param), own = ownerKey(expected, sf);
        if (!key || own?.owner !== first.owner || !sameKey(key, own)) continue;
        if (op === ts.SyntaxKind.EqualsEqualsEqualsToken) {
          if (sameKey(own, first)) { matchedFirst = true; return true; }
          if (sameKey(own, second)) { matchedSecond = true; return true; }
        }
        if (op === ts.SyntaxKind.ExclamationEqualsEqualsToken && !identity && !own.steps.length &&
            /^(?:_?id|uuid|(?:user|account|owner|principal)Id)$/i.test(own.field)) { identity = own.field; return true; }
      }
      return false;
    }
    return rowKey(node, pred.param) === first.field;
  }
  return matchesTerms(pred.body) && matchedFirst && matchedSecond && identity &&
    allAccounts(test.expression.expression, [first.field, second.field, identity]);
}

// The raw rows must have no uses other than narrowing them. The refusal must
// precede the query in the same statement list so that it cannot be bypassed.
function disambiguatedOwnerKeys(query, props, sf, references) {
  let value = query;
  while (stripWrappers(value.parent) === query) value = value.parent;
  const decl = value.parent;
  if (!ts.isVariableDeclaration(decl) || !ts.isIdentifier(decl.name) || !(decl.parent.flags & ts.NodeFlags.Const)) return [];
  const statement = decl.parent.parent, block = statement.parent;
  if (!ts.isVariableStatement(statement) || !ts.isBlock(block)) return [];
  const keys = [];
  for (const prop of props) {
    const field = prop.name && (ts.isIdentifier(prop.name) ? prop.name.text : strLit(prop.name));
    const expr = ts.isPropertyAssignment(prop) ? prop.initializer : ts.isShorthandPropertyAssignment(prop) ? prop.name : null;
    if (!field || !expr || !ts.isIdentifier(expr)) continue;
    const first = ownerKey(expr, sf);
    if (first?.steps[0]?.[0] === 'replace') keys.push({ field, first });
  }
  if (!keys.length) return [];
  const [use, otherUse] = references(decl);
  if (otherUse) return [];
  if (!use || !ts.isPropertyAccessExpression(use.parent) || use.parent.expression !== use || use.parent.questionDotToken ||
      use.parent.name.text !== 'filter' || !ts.isCallExpression(use.parent.parent) || use.parent.parent.expression !== use.parent ||
      use.parent.parent.questionDotToken || functionOf(use) !== functionOf(query)) return [];
  const filter = use.parent.parent, out = [];
  for (const { field, first } of keys) {
    const second = filterKey(filter, sf, field);
    if (!second || second.owner !== first.owner || sameKey(first, second)) continue;
    for (const stmt of block.statements) {
      if (stmt === statement) break;
      if (rejectsCollision(stmt, first, second, sf)) { out.push(field); break; }
    }
  }
  return out;
}

export function extractExposureFacts(project) {
  const static_mounts = [], file_writes = [], model_queries = [], token_payloads = [], dynamic_field_reads = [];
  const signers = new Set();
  for (const file of project.files.filter(f => /\.(ts|js|mjs)$/.test(f))) {
    walk(project.source(file), c => {
      // A function that signs one of its own parameters is a token issuer. Starting from the
      // sign call and climbing keeps this linear; walking every function body is quadratic in nesting.
      if (!ts.isCallExpression(c) || !ts.isPropertyAccessExpression(c.expression) || c.expression.name.text !== 'sign' || !c.arguments[0] || !ts.isIdentifier(c.arguments[0])) return;
      for (let n = c.parent; n; n = n.parent) {
        if (!FUNCTIONS(n) || !n.parameters[0] || !ts.isIdentifier(n.parameters[0].name) || n.parameters[0].name.text !== c.arguments[0].text) continue;
        const holder = n.parent && ts.isVariableDeclaration(n.parent) ? n.parent.name.getText() : n.name?.getText();
        if (holder) signers.add(holder);
      }
    });
  }
  for (const file of project.files.filter(f => /\.(ts|js|mjs)$/.test(f))) {
    const sf = project.source(file);
    const guards = [], mounts = [], responseCalls = [], boundQueries = new Map();
    const { declaration, references } = localBindings(sf);
    walk(sf, n => {
      if (ts.isForOfStatement(n)) {
        const fn = functionOf(n);
        const loopVar = ts.isVariableDeclarationList(n.initializer) && ts.isIdentifier(n.initializer.declarations[0].name) ? n.initializer.declarations[0].name.text : null;
        if (fn && loopVar && fromRequest(n.expression, declaration)) {
          walk(n.statement, r => {
            if (!ts.isElementAccessExpression(r) || !(ts.isAsExpression(r.argumentExpression) ? r.argumentExpression.expression : r.argumentExpression).getText?.(sf).startsWith(loopVar)) return;
            if (r.parent && ts.isBinaryExpression(r.parent) && r.parent.left === r) return;
            dynamic_field_reads.push({ source: coord(sf, n), read: coord(sf, r), source_text: maskLiterals(r.expression, sf), enclosing: coord(sf, fn) });
          });
        }
      }
      if (ts.isCallExpression(n)) {
        const callee = n.expression, name = ts.isIdentifier(callee) ? callee.text : ts.isPropertyAccessExpression(callee) ? callee.name.text : null;
        if (name && signers.has(name) && n.arguments[0]) {
          let payload = stripWrappers(n.arguments[0]);
          if (ts.isIdentifier(payload)) payload = stripWrappers(declaration(payload)?.initializer) ?? payload;
          const members = [];
          if (ts.isObjectLiteralExpression(payload)) for (const p of payload.properties) {
            const value = ts.isShorthandPropertyAssignment(p) ? p.name : ts.isPropertyAssignment(p) ? stripWrappers(p.initializer) : ts.isSpreadAssignment(p) ? stripWrappers(p.expression) : null;
            if (value && ts.isIdentifier(value)) members.push({ name: value.text, type: declaredType(declaration(value), sf) });
          }
          token_payloads.push({ signer: callee.getText(sf), source: coord(sf, n), enclosing: enclosingFunction(n, sf), members });
        }
      }
      if (!ts.isCallExpression(n) || !ts.isPropertyAccessExpression(n.expression)) return;
      const method = n.expression.name.text, receiver = n.expression.expression;
      if (RESPONSE.has(method) && n.arguments[0]) {
        let root = receiver;
        while (ts.isCallExpression(root) && ts.isPropertyAccessExpression(root.expression)) root = root.expression.expression;
        if (ts.isIdentifier(root) && /^(res|response|reply)$/.test(root.text)) responseCalls.push(n);
      }
      if (VERBS.has(method) && ts.isIdentifier(receiver)) {
        const path = strLit(n.arguments[0]);
        if (path !== null) {
          const names = [];
          for (const a of n.arguments.slice(1)) walk(a, x => { if (ts.isCallExpression(x)) names.push(x.expression.getText(sf)); });
          if (names.some(name => AUTH.test(name))) guards.push(path);
          if (method === 'use') {
            let server = null;
            for (const a of n.arguments.slice(1)) walk(a, x => { if (!server && ts.isCallExpression(x) && SERVERS.has(x.expression.getText(sf))) server = x; });
            if (server) mounts.push({ path, kind: server.expression.getText(sf) === 'serveIndex' ? 'directory-listing' : 'static-files', directory: strLit(server.arguments[0]), source: coord(sf, n) });
          }
        }
      }
      if (WRITES.test(n.expression.getText(sf))) {
        const literals = [];
        if (n.arguments[0]) walk(n.arguments[0], x => { const s = strLit(x); if (s !== null) literals.push(s); });
        file_writes.push({ api: n.expression.name.text, path_literals: literals, enclosing: enclosingFunction(n, sf), source: coord(sf, n) });
      }
      if (QUERIES.has(method) && receiverName(receiver) && /^[A-Z]|Collection$|^db$/.test(receiverName(receiver))) {
        const options = n.arguments.find(a => ts.isObjectLiteralExpression(a)) ?? null;
        const key = k => options?.properties.find(p => p.name && p.name.getText(sf).replace(/^['"]|['"]$/g, '') === k);
        const where = key('where'), include = key('include'), attributes = key('attributes');
        // Document stores (MarsDB, Mongo) take the filter itself as the first argument.
        const direct = !where && !include && !attributes && !['findAll', 'findAndCountAll', 'findByPk'].includes(method) && options?.properties.length ? options : null;
        let result = n;
        while (stripWrappers(result.parent) === n) result = result.parent;
        const parent = result.parent;
        const bound = ts.isVariableDeclaration(parent) && parent.initializer === result && ts.isIdentifier(parent.name) ? parent : null;
        // A promise chain ending in .then((rows) => ...) binds the result to the callback parameter.
        let callback = null;
        if (ts.isPropertyAccessExpression(parent) && parent.name.text === 'then' && ts.isCallExpression(parent.parent) &&
            parent.parent.expression === parent) {
          const fn = parent.parent.arguments[0];
          if (fn && (ts.isArrowFunction(fn) || ts.isFunctionExpression(fn)) && fn.parameters[0] && ts.isIdentifier(fn.parameters[0].name)) callback = fn.parameters[0];
        }
        const predicates = direct?.properties ?? (where && ts.isPropertyAssignment(where) && ts.isObjectLiteralExpression(where.initializer) ? where.initializer.properties : []);
        const fact = {
          receiver: receiverName(receiver), method, source: coord(sf, n), enclosing: enclosingFunction(n, sf), result: (bound ?? callback)?.name.text ?? null,
          argument_count: n.arguments.length, filtered: Boolean(where) || Boolean(direct) || (!options && n.arguments.length > 0),
          where: where && ts.isPropertyAssignment(where) ? maskLiterals(where.initializer, sf) : null,
          where_properties: predicates.map(p => ({ name: p.name?.getText(sf) ?? null, expression: ts.isPropertyAssignment(p) ? maskLiterals(p.initializer, sf) : ts.isShorthandPropertyAssignment(p) ? p.name.text : null })),
          disambiguated_owner_keys: predicates.length ? disambiguatedOwnerKeys(n, predicates, sf, references) : [],
          responses: [],
          projected: Boolean(attributes), include: include && ts.isPropertyAssignment(include) && ts.isArrayLiteralExpression(include.initializer) ? include.initializer.elements.map(e => (ts.isObjectLiteralExpression(e) ? e.properties.find(p => p.name?.getText(sf) === 'model')?.initializer?.getText(sf) : e.getText(sf)) ?? null).filter(Boolean) : [],
        };
        model_queries.push(fact);
        if (bound || callback) boundQueries.set(bound ?? callback, fact);
      }
    });
    if (boundQueries.size) connectResponses(responseCalls, boundQueries, declaration, sf);
    for (const m of mounts) static_mounts.push({ ...m, authenticated: guards.some(g => m.path === g || m.path.startsWith(g.replace(/\/$/, '') + '/')) });
  }
  return { static_mounts, file_writes, model_queries, token_payloads, dynamic_field_reads };
}
