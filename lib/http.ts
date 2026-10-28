export class PublicError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
    this.name = "PublicError";
  }
}

export function assertSameOrigin(request: Request): void {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  const protocol = new URL(request.url).protocol;
  let expected: string | null = null;
  // Next may normalize Request.url to its bind hostname. Compare the browser's
  // Origin with the original HTTP Host instead; never trust forwarded headers.
  // Restrict the whole authority to loopback, also preventing DNS rebinding.
  if (host && /^(?:127\.0\.0\.1|localhost|\[::1\])(?::\d{1,5})?$/i.test(host) && ["http:", "https:"].includes(protocol)) {
    try { expected = new URL(`${protocol}//${host}`).origin; }
    catch { /* Invalid ports are rejected with the same public 403 below. */ }
  }
  if (!expected || !origin || origin !== expected || request.headers.get("sec-fetch-site") === "cross-site") {
    throw new PublicError(403, "Żądanie musi pochodzić z tej aplikacji. Odśwież stronę i spróbuj ponownie.");
  }
}

export async function readFixture(request: Request): Promise<"outbreak" | "control"> {
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    throw new PublicError(415, "Oczekiwany format żądania: JSON.");
  }
  // Read at most 1 KiB even when a caller does not provide Content-Length.
  const reader = request.body?.getReader();
  if (!reader) throw new PublicError(400, "Wybierz scenariusz testowy.");
  let size = 0;
  const parts: Uint8Array[] = [];
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 1024) {
        await reader.cancel();
        throw new PublicError(413, "Żądanie jest zbyt duże.");
      }
      parts.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  let body: unknown;
  try {
    body = JSON.parse(Buffer.concat(parts).toString("utf8"));
  } catch {
    throw new PublicError(400, "Nieprawidłowy JSON.");
  }
  if (!body || typeof body !== "object" || Array.isArray(body) || Object.keys(body).length !== 1 || !("fixture" in body) || (body.fixture !== "outbreak" && body.fixture !== "control")) {
    throw new PublicError(400, "Wybierz scenariusz outbreak lub control.");
  }
  return body.fixture;
}

export function validRunId(id: string): string {
  if (!/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$/.test(id)) {
    throw new PublicError(400, "Nieprawidłowy identyfikator rundy.");
  }
  return id;
}

export function errorResponse(error: unknown): Response {
  if (error instanceof PublicError) {
    return Response.json({ error: error.message }, { status: error.status });
  }
  // Upstream bodies, URLs, credentials and stack traces are never returned.
  return Response.json({ error: "Nie udało się obsłużyć żądania. Sprawdź lokalny worker i spróbuj ponownie." }, { status: 500 });
}
