// Entry point for the TypeScript AST analyser.
// Usage: node auditor/ts/src/main.mjs < request.json > inventory.json
// request: {"root": "/abs/target", "files": ["server.ts", ...]}  (Target-relative, exclusions already applied)
// Only files listed in the request may be read: exclusions are applied by the Python caller.
import { readFileSync } from 'node:fs';
import { extractRoutes } from './routes.mjs';
import { extractModels } from './models.mjs';
import { extractFrontend } from './frontend.mjs';
import { createProject } from './project.mjs';

const request = JSON.parse(readFileSync(0, 'utf8'));
const project = createProject(request.root, request.files);

const out = {
  ...extractRoutes(project),
  ...extractModels(project),
  ...extractFrontend(project),
};
process.stdout.write(JSON.stringify(out));
