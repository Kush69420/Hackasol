import { readFileSync } from 'node:fs';
import { createProject } from './project.mjs';
import { extractFlows } from './flows.mjs';

const { root, files, inventory } = JSON.parse(readFileSync(0, 'utf8'));
process.stdout.write(JSON.stringify(extractFlows(createProject(root, files), inventory)));
