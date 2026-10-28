import assert from "node:assert/strict";
import test from "node:test";
import { assertSameOrigin, errorResponse, PublicError, readFixture, validRunId } from "../lib/http";
import { requestWorker, workerConfiguration } from "../lib/worker";

function mutation(origin?: string, body = '{"fixture":"outbreak"}') {
  return new Request("http://127.0.0.1:3000/api/runs", {
    method: "POST",
    headers: { Host: "127.0.0.1:3000", "Content-Type": "application/json", ...(origin ? { Origin: origin } : {}) },
    body,
  });
}

test("mutations require exact same origin, including port", () => {
  assert.doesNotThrow(() => assertSameOrigin(mutation("http://127.0.0.1:3000")));
  for (const origin of [undefined, "null", "https://attacker.example", "http://127.0.0.1:8000", "http://localhost:3000"]) {
    assert.throws(() => assertSameOrigin(mutation(origin)), (error) => error instanceof PublicError && error.status === 403);
  }
  const crossSite = mutation("http://127.0.0.1:3000");
  crossSite.headers.set("sec-fetch-site", "cross-site");
  assert.throws(() => assertSameOrigin(crossSite));
  const rebound = new Request("http://attacker.example:3000/api/runs", { method: "POST", headers: { Origin: "http://attacker.example:3000" } });
  assert.throws(() => assertSameOrigin(rebound));
});

test("Next's internal hostname normalization does not reject the real same-origin browser", () => {
  const request = new Request("http://localhost:3000/api/runs", {
    method: "POST",
    headers: { Host: "127.0.0.1:3000", Origin: "http://127.0.0.1:3000", "Sec-Fetch-Site": "same-origin" },
  });
  assert.doesNotThrow(() => assertSameOrigin(request));
  request.headers.set("Origin", "http://127.0.0.1:3001");
  assert.throws(() => assertSameOrigin(request), (error) => error instanceof PublicError && error.status === 403);
  request.headers.set("Origin", "http://localhost:3000");
  assert.throws(() => assertSameOrigin(request), (error) => error instanceof PublicError && error.status === 403);
});

test("Host must be a single loopback authority and cannot be replaced with forwarded headers", () => {
  for (const host of ["attacker.example:3000", "localhost.evil.test:3000", "localhost:3000/path", "user@localhost:3000", "localhost:99999", "localhost:3000, attacker.example", "127.0.0.1:3000#"]) {
    const request = mutation("http://127.0.0.1:3000");
    request.headers.set("Host", host);
    request.headers.set("X-Forwarded-Host", "127.0.0.1:3000");
    assert.throws(() => assertSameOrigin(request), (error) => error instanceof PublicError && error.status === 403);
  }
  const request = mutation("http://127.0.0.1:3000");
  request.headers.delete("Host");
  assert.throws(() => assertSameOrigin(request), (error) => error instanceof PublicError && error.status === 403);
});

test("run input accepts only the documented fixtures with no extra arguments", async () => {
  assert.equal(await readFixture(mutation(undefined)), "outbreak");
  assert.equal(await readFixture(mutation(undefined, '{"fixture":"control"}')), "control");
  for (const body of ['{}', 'null', '[]', '{"fixture":"bad"}', '{"fixture":"outbreak","url":"http://attacker.example"}', '{']) {
    await assert.rejects(readFixture(mutation(undefined, body)), PublicError);
  }
  await assert.rejects(readFixture(mutation(undefined, JSON.stringify({ fixture: "x".repeat(1024) }))), (error) => error instanceof PublicError && error.status === 413);
  const wrongType = mutation();
  wrongType.headers.set("Content-Type", "text/plain");
  await assert.rejects(readFixture(wrongType), (error) => error instanceof PublicError && error.status === 415);
});

test("worker target stays on loopback and cannot contain credentials, paths or queries", () => {
  for (const url of ["http://127.0.0.1:8000", "http://localhost:8001/", "http://[::1]:8000"]) {
    assert.equal(workerConfiguration({ WORKER_URL: url }).origin, new URL(url).origin);
  }
  for (const url of ["https://api.example.com", "http://192.168.1.2:8000", "http://localhost.evil.test", "http://user:secret@localhost:8000", "http://localhost:8000/private", "http://localhost:8000/?token=secret", "http://localhost:8000/#fragment", "file:///etc/passwd"]) {
    assert.throws(() => workerConfiguration({ WORKER_URL: url }), PublicError);
  }
  assert.throws(() => workerConfiguration({ WORKER_TOKEN: "x\r\nInjected: yes" }), PublicError);
});

test("run ids cannot escape into another path", () => {
  assert.equal(validRunId("run-123_abc"), "run-123_abc");
  for (const id of ["../health", "a/dispatch", "a?token=x", "a%2fsubmit", "", "a".repeat(81)]) assert.throws(() => validRunId(id), PublicError);
});

test("worker calls carry server token, reject redirects and do not forward provider errors", async () => {
  const secret = "test-secret-never-send-to-browser";
  let called = false;
  const fakeFetch: typeof fetch = async (input, init) => {
    called = true;
    assert.equal(String(input), "http://127.0.0.1:8000/run");
    assert.equal(new Headers(init?.headers).get("Authorization"), `Bearer ${secret}`);
    assert.equal(init?.redirect, "error");
    assert.equal(init?.body, '{"fixture":"control"}');
    return new Response(`Provider traceback api_key=${secret}`, { status: 500 });
  };
  let caught: unknown;
  try {
    await requestWorker("/run", { method: "POST", body: { fixture: "control" } }, { env: { WORKER_TOKEN: secret }, fetcher: fakeFetch });
  } catch (error) { caught = error; }
  assert.equal(called, true);
  const response = errorResponse(caught);
  assert.equal(response.status, 502);
  const output = await response.text();
  assert.equal(output.includes(secret), false);
  assert.equal(output.includes("traceback"), false);
});

test("network errors and unexpected exceptions remain private", async () => {
  const secret = "private-key-value";
  await assert.rejects(
    requestWorker("/health", {}, { env: {}, fetcher: async () => { throw new Error(secret); } }),
    (error) => error instanceof PublicError && error.status === 503 && !error.message.includes(secret),
  );
  assert.equal((await errorResponse(new Error(secret)).text()).includes(secret), false);
  await assert.rejects(requestWorker("//attacker.example", {}, { env: {}, fetcher: async () => { throw new Error("must not run"); } }), (error) => error instanceof PublicError && error.status === 400);
});
