import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { spawn } from 'node:child_process';

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export function environment() {
  if (process.env.SKIP_DOTENV !== '1' && existsSync(resolve(root, '.env'))) process.loadEnvFile(resolve(root, '.env'));
  return { ...process.env, NEXT_TELEMETRY_DISABLED: '1', CREWAI_TRACING_ENABLED: 'false',
    OTEL_SDK_DISABLED: 'true', DO_NOT_TRACK: 'true' };
}
export function run(command, args, options = {}) {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(command, args, { cwd: root, stdio: 'inherit', ...options });
    child.on('error', () => reject(new Error(`Nie można uruchomić ${command}. Sprawdź instalację w README.`)));
    child.on('exit', (code) => code === 0 ? resolvePromise() : reject(new Error(`${command}: kod zakończenia ${code}.`)));
  });
}
