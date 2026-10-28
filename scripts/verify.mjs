// smoke --verify runs the full suite in a disposable source copy without .env.
process.argv.push('--verify');
await import('./smoke.mjs');
