import { run, environment } from './common.mjs';
try {
  await run('uv', ['run', '--project', 'worker', '--frozen', 'python', '-m', 'among_agents.doctor', ...process.argv.slice(2)], { env: environment() });
} catch (error) { console.error(error.message); process.exitCode = 1; }
