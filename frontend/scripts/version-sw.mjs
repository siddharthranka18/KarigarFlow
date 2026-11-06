import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const index = await readFile(new URL('../dist/index.html', import.meta.url));
const version = createHash('sha256').update(index).digest('hex').slice(0, 12);
const path = new URL('../dist/sw.js', import.meta.url);
await writeFile(path, (await readFile(path, 'utf8')).replace('karigarflow-shell-v1', `karigarflow-shell-${version}`));
