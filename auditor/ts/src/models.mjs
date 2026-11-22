import { ts, coord } from './project.mjs';

const walk = (node, fn) => { fn(node); ts.forEachChild(node, child => walk(child, fn)); };
const name = node => node?.name && (ts.isIdentifier(node.name) || ts.isStringLiteral(node.name) || ts.isNumericLiteral(node.name)) ? node.name.text : null;
const prop = (obj, key) => ts.isObjectLiteralExpression(obj) ? obj.properties.find(p => name(p) === key) : undefined;
const init = p => p && ts.isPropertyAssignment(p) ? p.initializer : undefined;
const literal = n => !n ? null : n.kind === ts.SyntaxKind.TrueKeyword ? true : n.kind === ts.SyntaxKind.FalseKeyword ? false : ts.isNumericLiteral(n) ? Number(n.text) : ts.isStringLiteral(n) ? n.text : null;
// String defaults can contain Authentication Secrets. Emit their presence, not their value.
const defaultValue = n => !n ? null : ts.isStringLiteralLike(n) ? (n.text === '' ? '' : '<string>') : literal(n) ?? n.getText().replace(/(['"`])(?:\\.|(?!\1)[\s\S])*?\1/g, '<string>');
export function extractModels(project) {
  const models = [], collections = [], byName = new Map();
  for (const file of project.files.filter(f => f.endsWith('.ts'))) {
    const sf = project.source(file);
    walk(sf, n => {
      if (ts.isVariableDeclaration(n) && ts.isIdentifier(n.name) && n.initializer && ts.isNewExpression(n.initializer) && n.initializer.expression.getText(sf).endsWith('Collection') && /(?:^|\.)Collection$/.test(n.initializer.expression.getText(sf))) {
        const item = { name: n.name.text, kind: 'marsdb', source: coord(sf, n), fields: [] };
        collections.push(item); byName.set(item.name, item);
      }
      if (!file.startsWith('models/') || !ts.isCallExpression(n) || !ts.isPropertyAccessExpression(n.expression) || n.expression.name.text !== 'init' || !ts.isObjectLiteralExpression(n.arguments[0])) return;
      const opts = n.arguments[1], options = {};
      if (opts && ts.isObjectLiteralExpression(opts)) for (const p of opts.properties) {
        const key = name(p), value = literal(init(p));
        if (key && value !== null && key !== 'tableName' && key !== 'modelName') options[key] = value;
      }
      if (!('paranoid' in options)) options.paranoid = null;
      const fields = n.arguments[0].properties.filter(p => name(p)).map(p => {
        const value = init(p), type = init(prop(value, 'type')) ?? value;
        const validators = init(prop(value, 'validate'));
        return { name: name(p), type: type?.getText(sf) ?? null, allow_null: literal(init(prop(value, 'allowNull'))), default: defaultValue(init(prop(value, 'defaultValue'))), unique: literal(init(prop(value, 'unique'))), validators: validators && ts.isObjectLiteralExpression(validators) ? validators.properties.map(name).filter(Boolean) : [], source: coord(sf, p) };
      });
      models.push({ name: literal(init(prop(opts, 'modelName'))) ?? n.expression.expression.getText(sf), table: literal(init(prop(opts, 'tableName'))), kind: 'sequelize', source: coord(sf, n), options, fields });
    });
  }
  for (const file of project.files.filter(f => f.endsWith('.ts'))) {
    const sf = project.source(file);
    walk(sf, n => {
      if (!ts.isCallExpression(n) || !ts.isPropertyAccessExpression(n.expression) || !['insert', 'update', 'find', 'findOne', 'remove', 'upsert'].includes(n.expression.name.text)) return;
      const receiver = n.expression.expression;
      const collection = byName.get(ts.isPropertyAccessExpression(receiver) ? receiver.name.text : ts.isIdentifier(receiver) ? receiver.text : '');
      if (!collection) return;
      for (const arg of n.arguments) walk(arg, obj => {
        if (!ts.isObjectLiteralExpression(obj)) return;
        for (const p of obj.properties) {
          const field = name(p);
          if (field && !field.startsWith('$') && !collection.fields.some(f => f.name === field)) collection.fields.push({ name: field, source: coord(sf, p) });
        }
      });
    });
  }
  return { models, collections };
}
