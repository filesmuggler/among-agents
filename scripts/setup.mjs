import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { root, run } from './common.mjs';

try {
  await run('uv', ['--version']);
  await run('npm', ['ci', '--no-fund', '--no-audit']);
  await run('uv', ['sync', '--project', 'worker', '--frozen', '--extra', 'dev', '--python', '3.12']);
  console.log('\nGotowe. npm run dev uruchamia panel i worker zgodnie z .env; domyślnie demo bez kluczy.');
  console.log(existsSync(resolve(root, '.env'))
    ? 'Zachowano istniejący .env. Dopisz brakujące ustawienia według .env.example.'
    : 'Do trybu live utwórz .env według .env.example i instrukcji w README.');
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
