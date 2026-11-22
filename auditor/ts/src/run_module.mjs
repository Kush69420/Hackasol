// Run one analyser module alone (used by focused tests).
// Usage: node auditor/ts/src/run_module.mjs <routes|models|frontend> < request.json
import { readFileSync } from 'node:fs';
import { createProject } from './project.mjs';

const fns = { routes: 'extractRoutes', models: 'extractModels', frontend: 'extractFrontend' };
const name = process.argv[2];
if (!fns[name]) throw new Error(`unknown module ${name}`);
const mod = await import(`./${name}.mjs`);
const request = JSON.parse(readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(mod[fns[name]](createProject(request.root, request.files))));
