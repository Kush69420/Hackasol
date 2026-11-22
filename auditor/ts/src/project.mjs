// Shared parsing helpers for the analyser modules.
import { readFileSync } from 'node:fs';
import path from 'node:path';
import ts from 'typescript';

/**
 * @param {string} root absolute Target root
 * @param {string[]} files Target-relative POSIX paths (already filtered by exclusions)
 */
export function createProject(root, files) {
  const allowed = new Set(files);
  const cache = new Map();
  return {
    root,
    files,
    /** True when the file is in scope (not excluded). */
    has(rel) {
      return allowed.has(rel);
    },
    /** Raw text of an in-scope file; throws for excluded/unknown files. */
    text(rel) {
      if (!allowed.has(rel)) throw new Error(`file not in scan scope: ${rel}`);
      return readFileSync(path.join(root, rel), 'utf8');
    },
    /** Parsed ts.SourceFile (TS/JS only), cached. */
    source(rel) {
      if (!cache.has(rel)) {
        const kind = rel.endsWith('.js') || rel.endsWith('.mjs') ? ts.ScriptKind.JS : ts.ScriptKind.TS;
        cache.set(rel, ts.createSourceFile(rel, this.text(rel), ts.ScriptTarget.Latest, true, kind));
      }
      return cache.get(rel);
    },
  };
}

/** Source coordinate for a node: {file, start_line, end_line} (1-based, inclusive). */
export function coord(sf, node) {
  const start = sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;
  const end = sf.getLineAndCharacterOfPosition(node.getEnd()).line + 1;
  return { file: sf.fileName, start_line: start, end_line: end };
}

/** Source coordinate for a 0-based character offset range in plain text files. */
export function textCoord(file, text, startOffset, endOffset = startOffset) {
  const line = (o) => text.slice(0, o).split('\n').length;
  return { file, start_line: line(startOffset), end_line: line(endOffset) };
}

export { ts };
