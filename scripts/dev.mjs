import { spawn } from 'node:child_process';
import { createServer } from 'node:net';
import { root, environment } from './common.mjs';

const env = environment();
const children = [];
let stopping = false;
function stop(code = 0) {
  if (stopping) return;
  stopping = true;
  process.exitCode = code;
  for (const child of children) child.kill('SIGTERM');
  const timer = setTimeout(() => {
    for (const child of children) child.kill('SIGKILL');
  }, 5000);
  timer.unref();
}
async function available(port) {
  await new Promise((resolve, reject) => {
    const server = createServer();
    server.once('error', () => reject(new Error(`Port ${port} jest zajęty. Zatrzymaj poprzedni lokalny serwer.`)));
    server.listen(port, '127.0.0.1', () => server.close(resolve));
  });
}
function start(command, args) {
  const child = spawn(command, args, { cwd: root, env, stdio: 'inherit' });
  children.push(child);
  child.once('error', () => { console.error(`Nie można uruchomić ${command}; wykonaj npm run setup.`); stop(1); });
  child.once('exit', (code) => { if (!stopping) stop(code || 1); });
}
try {
  await available(3000);
  await available(8000);
  start('uv', ['run', '--project', 'worker', '--frozen', 'uvicorn', 'among_agents.app:app', '--host', '127.0.0.1', '--port', '8000']);
  start(process.execPath, ['node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3000']);
  console.log('Among Agents: http://127.0.0.1:3000 — Ctrl+C zatrzymuje oba procesy.');
} catch (error) { console.error(error.message); stop(1); }
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
