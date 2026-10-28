import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { cp, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import { delimiter, join } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { root } from './common.mjs';

// Tests use a disposable source copy, synthetic credentials and their own DB.
// Never read/copy .env, reuse a running service, or touch the user's run history.
const verify = process.argv.includes('--verify');
const temporary = await mkdtemp(join(tmpdir(), 'among-agents-m0-'));
const children = new Set();
const python = join(root, 'worker/.venv/bin/python');
const next = join(root, 'node_modules/next/dist/bin/next');
const sentinel = 'm0-synthetic-secret-never-publish';
const env = {
  PATH: process.env.PATH, HOME: join(temporary, 'home'), TMPDIR: temporary,
  LANG: 'en_US.UTF-8', SKIP_DOTENV: '1', RUN_MODE: 'demo',
  WORKER_TOKEN: sentinel, YDC_API_KEY: sentinel, PARASAIL_API_KEY: sentinel,
  ONE_API_KEY: sentinel, SCENARIO_ALLOW_TICK: 'false', SCENARIO_ALLOW_SUBMIT: 'false',
  DISCORD_SEND_ENABLED: 'false', NEXT_TELEMETRY_DISABLED: '1',
  CREWAI_TRACING_ENABLED: 'false', OTEL_SDK_DISABLED: 'true', DO_NOT_TRACK: 'true',
  PYTHONDONTWRITEBYTECODE: '1', WORKER_DB: join(temporary, 'runs.sqlite3'),
  PYTHONPATH: [join(temporary, 'guard'), join(temporary, 'worker')].join(delimiter),
  M0_NETWORK_MARKER: join(temporary, 'unexpected-network'),
};

function launch(command, args) {
  const child = spawn(command, args, { cwd: temporary, env, detached: true, stdio: ['ignore', 'pipe', 'pipe'] });
  child.output = '';
  child.failure = null;
  child.done = new Promise(resolve => {
    child.once('error', error => { child.failure = error; resolve(); });
    child.once('exit', resolve);
  });
  for (const stream of [child.stdout, child.stderr]) {
    stream.on('data', chunk => { child.output = (child.output + chunk).slice(-18000); });
  }
  children.add(child);
  return child;
}

async function command(command, args, label) {
  const child = launch(command, args);
  const timer = setTimeout(() => kill(child, 'SIGKILL'), 180000);
  await child.done;
  clearTimeout(timer);
  assert.equal(child.exitCode, 0, `${label} failed: ${child.failure?.message ?? child.output}`);
  children.delete(child);
  const count = child.output.match(/(?:# tests \d+|\d+ passed(?:, \d+ warnings)?)/)?.[0];
  console.log(`PASS: ${label}${count ? ` (${count})` : ''}`);
}

function kill(child, signal) {
  if (!child.pid) return;
  try { process.kill(-child.pid, signal); } catch (error) { if (error.code !== 'ESRCH') throw error; }
}

async function stop() {
  const active = [...children];
  for (const child of active) kill(child, 'SIGTERM');
  const timer = setTimeout(() => { for (const child of active) kill(child, 'SIGKILL'); }, 5000);
  await Promise.all(active.map(child => child.done));
  clearTimeout(timer);
  // A Next child can outlive its launcher: terminate the remaining process group.
  for (const child of active) kill(child, 'SIGKILL');
  children.clear();
}

async function port(preferred = 0) {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once('error', reject);
    server.listen(preferred, '127.0.0.1', () => {
      const selected = server.address().port;
      server.close(() => resolve(selected));
    });
  });
}

async function ready(url, child) {
  for (let attempt = 0; attempt < 240; attempt++) {
    if (child.failure || child.exitCode !== null) throw new Error(`Service exited: ${child.output}`);
    try { if ((await fetch(url, { signal: AbortSignal.timeout(2000) })).ok) return; } catch { /* booting */ }
    await delay(250);
  }
  throw new Error(`Local service did not become ready: ${child.output}`);
}

async function json(base, path, options = {}, expected = 200) {
  const response = await fetch(base + path, { ...options, signal: AbortSignal.timeout(30000) });
  const body = await response.text();
  assert.equal(response.status, expected, `${path}: ${body}`);
  assert.ok(!body.includes(sentinel), `${path}: server-only value leaked`);
  return JSON.parse(body);
}

async function inspectClientFiles(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await inspectClientFiles(path);
    else if (/\.(js|html|json|map)$/.test(entry.name)) assert.ok(!(await readFile(path, 'utf8')).includes(sentinel), 'Secret in client output');
  }
}

for (const signal of ['SIGINT', 'SIGTERM']) process.once(signal, async () => {
  await stop();
  await rm(temporary, { recursive: true, force: true });
  process.exit(signal === 'SIGINT' ? 130 : 143);
});

try {
  assert.ok(existsSync(python) && existsSync(next), 'Missing dependencies: run npm run setup first.');
  for (const name of ['app', 'lib', 'fixtures', 'tests', 'package.json', 'tsconfig.json', 'next.config.ts', 'next-env.d.ts', 'worker/among_agents', 'worker/tests', 'worker/pyproject.toml']) {
    await cp(join(root, name), join(temporary, name), { recursive: true, filter: source => !source.includes('__pycache__') });
  }
  await symlink(join(root, 'node_modules'), join(temporary, 'node_modules'), 'dir');
  await mkdir(env.HOME);
  await mkdir(join(temporary, 'guard'));
  // Every provider path runs in Python. Fail on any attempted non-loopback socket.
  await writeFile(join(temporary, 'guard/sitecustomize.py'), `import os, socket\nfrom pathlib import Path\n_original_connect = socket.socket.connect\n_original_connect_ex = socket.socket.connect_ex\ndef _check(address):\n    if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1', 'localhost'):\n        Path(os.environ['M0_NETWORK_MARKER']).touch()\n        raise RuntimeError('M0 smoke forbids external network')\ndef connect(self, address):\n    _check(address)\n    return _original_connect(self, address)\ndef connect_ex(self, address):\n    _check(address)\n    return _original_connect_ex(self, address)\nsocket.socket.connect = connect\nsocket.socket.connect_ex = connect_ex\n`);
  await command(python, ['-m', 'among_agents.doctor'], 'offline Python doctor');
  if (verify) {
    const tests = (await readdir(join(temporary, 'tests'))).filter(name => name.endsWith('.test.ts')).map(name => `tests/${name}`);
    await command(process.execPath, ['--import', 'tsx', '--test', ...tests], 'Next/API unit tests');
    await command(python, ['-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'worker/tests'], 'Python tests (external sockets blocked)');
    await command(process.execPath, [next, 'build', '--webpack'], 'Next production build without .env');
    await command(process.execPath, ['node_modules/typescript/bin/tsc', '--noEmit'], 'TypeScript');
  }
  const workerPort = await port();
  let webPort = await port();
  while (webPort === workerPort) webPort = await port();
  const workerBase = `http://127.0.0.1:${workerPort}`;
  const webBase = `http://127.0.0.1:${webPort}`;
  env.WORKER_URL = workerBase;
  const mutation = fixture => ({ method: 'POST', headers: { Origin: webBase, 'Content-Type': 'application/json' }, body: JSON.stringify({ fixture }) });
  let runId;
  for (let cycle = 0; cycle < 2; cycle++) {
    const worker = launch(python, ['-m', 'uvicorn', 'among_agents.app:app', '--host', '127.0.0.1', '--port', String(workerPort)]);
    const web = launch(process.execPath, [next, verify ? 'start' : 'dev', ...(!verify ? ['--webpack'] : []), '--hostname', '127.0.0.1', '--port', String(webPort)]);
    await ready(workerBase + '/health', worker);
    await ready(webBase + '/api/health', web);
    const health = await json(webBase, '/api/health');
    assert.equal(health.mode, 'demo');
    const html = await (await fetch(webBase)).text();
    assert.ok(html.includes('<html') && !html.includes(sentinel));
    if (cycle === 0) {
      const outbreak = await json(webBase, '/api/runs', mutation('outbreak'));
      runId = outbreak.id;
      assert.equal(outbreak.mode, 'demo');
      assert.equal(outbreak.decision.action, 'evacuate');
      assert.equal(outbreak.tick.sector_reports.length, 2);
      assert.equal(outbreak.agents.length, 3);
      const control = await json(webBase, '/api/runs', mutation('control'));
      assert.equal(control.decision.action, 'observe');
      assert.equal(control.dispatch.status, 'not_required');
      for (const [action, effect] of [['dispatch', 'dispatch'], ['submit', 'submission']]) {
        const result = await json(webBase, `/api/runs/${runId}/${action}`, { method: 'POST', headers: { Origin: webBase } });
        assert.equal(result[effect].status, 'simulated');
      }
      const rejected = mutation('outbreak');
      rejected.headers.Origin = 'https://invalid.example';
      await json(webBase, '/api/runs', rejected, 403);
      await json(webBase, '/api/runs', mutation('unknown'), 400);
      await json(workerBase, `/runs/${runId}`, {}, 401);
      const scoreboard = await json(webBase, '/api/scoreboard');
      assert.equal(scoreboard.mode, 'demo');
      console.log('PASS: Next → worker, outbreak/control, simulated effects, auth, Origin, validation');
    } else {
      const restored = await json(webBase, `/api/runs/${runId}`);
      assert.equal(restored.id, runId);
      assert.equal(restored.dispatch.status, 'simulated');
      console.log('PASS: restart on same ports, persisted run and receipts');
    }
    await stop();
    await port(workerPort);
    await port(webPort);
  }
  await inspectClientFiles(join(temporary, verify ? '.next/static' : '.next/dev/static'));
  assert.ok(!existsSync(env.M0_NETWORK_MARKER), 'An external network attempt occurred');
  console.log('PASS: no external worker requests, no secrets in client output, processes stopped and ports released');
} catch (error) {
  console.error(String(error.message).replaceAll(sentinel, '[REDACTED]'));
  process.exitCode = 1;
} finally {
  await stop();
  await rm(temporary, { recursive: true, force: true });
}
