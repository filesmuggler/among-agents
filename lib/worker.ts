import { PublicError } from "./http";

type WorkerEnvironment = { WORKER_URL?: string; WORKER_TOKEN?: string };

export function workerConfiguration(env: WorkerEnvironment) {
  let url: URL;
  try {
    url = new URL(env.WORKER_URL || "http://127.0.0.1:8000");
  } catch {
    throw new PublicError(503, "Nieprawidłowa konfiguracja lokalnego workera. Sprawdź WORKER_URL w głównym pliku .env.");
  }
  if (url.protocol !== "http:" || !["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) || url.username || url.password || url.pathname !== "/" || url.search || url.hash) {
    throw new PublicError(503, "WORKER_URL musi wskazywać lokalny worker HTTP (127.0.0.1, localhost lub ::1), bez ścieżki i danych logowania.");
  }
  const token = env.WORKER_TOKEN || "";
  if (/[\r\n]/.test(token)) throw new PublicError(503, "Nieprawidłowa konfiguracja WORKER_TOKEN.");
  return { origin: url.origin, token };
}

export async function requestWorker(
  path: string,
  options: { method?: "GET" | "POST"; body?: unknown; timeoutMs?: number } = {},
  dependencies: { env?: WorkerEnvironment; fetcher?: typeof fetch } = {},
): Promise<unknown> {
  // Route handlers choose every path; user URLs are never forwarded.
  if (!/^\/(health|run|scoreboard|runs\/[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}(\/(submit|dispatch))?)$/.test(path)) {
    throw new PublicError(400, "Nieobsługiwana operacja workera.");
  }
  const config = workerConfiguration(dependencies.env ?? { WORKER_URL: process.env.WORKER_URL, WORKER_TOKEN: process.env.WORKER_TOKEN });
  const headers = new Headers({ Accept: "application/json" });
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (config.token) headers.set("Authorization", `Bearer ${config.token}`);
  let response: Response;
  try {
    response = await (dependencies.fetcher ?? fetch)(config.origin + path, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      redirect: "error",
      cache: "no-store",
      signal: AbortSignal.timeout(options.timeoutMs ?? 15_000),
    });
  } catch {
    throw new PublicError(503, "Lokalny worker nie odpowiada lub przekroczono czas oczekiwania. Uruchom go zgodnie z README i spróbuj ponownie.");
  }
  if (!response.ok) {
    const messages: Record<number, string> = {
      400: "Worker odrzucił dane operacji. Sprawdź wybrany scenariusz i konfigurację.",
      401: "Worker odrzucił uwierzytelnienie. Sprawdź WORKER_TOKEN we wspólnym pliku .env i uruchom ponownie oba procesy.",
      403: "Worker nie zezwolił na operację. Sprawdź konfigurację i uprawnienia integracji.",
      404: "Nie znaleziono rundy. Uruchom nową rundę.",
      409: "Operacja jest w toku lub runda nie pozwala na tę akcję. Odśwież jej stan.",
      422: "Dane scenariusza nie przeszły walidacji workera.",
      429: "Osiągnięto limit wywołań. Spróbuj ponownie później.",
      503: "Worker nie jest gotowy. Sprawdź klucze i ustawienia w lokalnym pliku środowiska.",
    };
    throw new PublicError([400, 401, 403, 404, 409, 422, 429, 503].includes(response.status) ? response.status : 502, messages[response.status] ?? "Integracja nie ukończyła operacji. Sprawdź lokalne logi workera; szczegóły dostawcy nie są udostępniane przeglądarce.");
  }
  try {
    return await response.json();
  } catch {
    throw new PublicError(502, "Worker zwrócił nieprawidłową odpowiedź.");
  }
}
