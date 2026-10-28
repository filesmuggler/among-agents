# Kontrakt Next.js ↔ lokalny worker CrewAI

Stan: M0, 28 października 2026. Źródłem kontraktu są `app/api/`, `lib/http.ts`, `lib/worker.ts` oraz `worker/among_agents/{app,models,config,store}.py`. Next.js jest lokalnym pośrednikiem HTTP. CrewAI działa wewnątrz procesu Python, dopiero przy wykonaniu rundy `live`; nie jest osobnym serwisem chmurowym.

## Granica procesów i uwierzytelnianie

Przeglądarka → `http://127.0.0.1:3000/api/*` → lokalny FastAPI, domyślnie `http://127.0.0.1:8000`. Oba procesy czytają główny `.env`; zmienne procesu mają pierwszeństwo. `WORKER_URL` akceptuje wyłącznie HTTP z hostem `127.0.0.1`, `localhost` lub `[::1]`, bez ścieżki, danych logowania, query i fragmentu. Proxy nie przyjmuje adresu ani ścieżki workera od klienta i odrzuca przekierowania.

Next.js dołącza `Authorization: Bearer <WORKER_TOKEN>` wyłącznie na serwerze. FastAPI sprawdza token dla rund, efektów i scoreboardu, jeśli został ustawiony. Bez tokenu dozwolony jest lokalny `demo`; chronione endpointy `live` zwracają `503`. `/health` nie wymaga tokenu. Worker dopuszcza tylko lokalny nagłówek Host i odrzuca żądania z nagłówkiem Origin; przeglądarka ma korzystać z Next.js.

Każda mutacja Next.js wymaga Origin zgodnego z oryginalnym lokalnym Host i protokołem żądania. `Sec-Fetch-Site: cross-site` jest odrzucany. Same-origin nie jest zgodą na efekty zewnętrzne: osobne blokady konfiguracji obowiązują przed pobraniem ticka, submission i Discordem. Sekretów nie wolno umieszczać w `NEXT_PUBLIC_*`.

## Endpointy

Wszystkie poniższe operacje zwracają JSON. `id` w Next.js musi pasować do `[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}`; nowe rundy otrzymują UUID. Zwykłe GET ani odświeżenie strony nie uruchamiają rundy, submission lub dispatchu.

| Next.js | FastAPI | Wejście | Wynik | Timeout proxy |
| --- | --- | --- | --- | --- |
| `GET /api/health` | `GET /health` | brak | publiczny `Health` | 15 s |
| `POST /api/runs` | `POST /run` | dokładnie `{"fixture":"outbreak"}` albo `{"fixture":"control"}` | pełny `Run` | 600 s |
| `GET /api/runs/{id}` | `GET /runs/{id}` | id lokalnej rundy | zapisany `Run` | 15 s |
| `POST /api/runs/{id}/submit` | `POST /runs/{id}/submit` | bez body | `Run` z wynikiem submission | 90 s |
| `POST /api/runs/{id}/dispatch` | `POST /runs/{id}/dispatch` | bez body | `Run` z wynikiem dispatchu | 90 s |
| `GET /api/scoreboard` | `GET /scoreboard` | brak | `{mode, scoreboard, detail?}` | 30 s |

Tworzenie rundy w Next.js wymaga `Content-Type: application/json`, body do 1024 bajtów i jednego pola `fixture`. Dodatkowe pola, np. własny URL, token, kanał lub akcja, są odrzucane. Bezpośredni model FastAPI dopuszcza `{}` jako domyślne `outbreak`, lecz publiczny kontrakt Next.js wymaga jawnego wyboru. Submit i dispatch nie przekazują body klienta: akcja, tick i cel wynikają z zapisanej rundy oraz lokalnej konfiguracji.

Publiczny `Health` ma dokładnie `status: "ok"`, `mode: "demo" | "live"` oraz `integrations: Array<{name: string, configured: boolean, detail: string}>`. Next.js sprawdza ten kształt i usuwa dodatkowe pola. Bezpośredni `/health` workera zwraca dodatkowo `safety_gates` z trzema flagami opisanymi niżej; obecny proxy ich nie przekazuje. `configured` oznacza obecność konfiguracji lub dostępność lokalnego komponentu; nie potwierdza uprawnień, salda, połączenia ani udanej inferencji.

## Dane rundy i fixtures

Walidację wykonują modele Pydantic. `lib/types.ts` opisuje używany przez UI podzbiór i ma luźniejsze typy części ticka; nie zastępuje walidacji Python. Modele odrzucają dodatkowe pola i niefinitywne liczby. Adapter scenariusza usuwa zewnętrzne metadane koperty przed walidacją samego ticka.

| Pole `Run` | Kontrakt |
| --- | --- |
| `id`, `created_at` | identyfikator lokalnej rundy; czas ISO UTC |
| `mode` | `demo` lub `live` |
| `tick.tick_id` | dodatnia liczba całkowita |
| `tick.facility_id` | niepusty tekst, do 200 znaków |
| `tick.sector_reports` | 1–100 sektorów; przetwarzane są wszystkie sektory |
| `tick.swarm_budget` | nieujemne liczby całkowite `max_active_agents`, `api_credits_remaining` |
| `tick.escalation_channel` | `{app: "discord", channel: string, via: string}`; metadane scenariusza, nie autoryzacja celu |
| `decision.action` | dokładnie `contain`, `evacuate` lub `observe` |
| `decision.rationale` | 8–1500 znaków |
| `decision.evidence` | 1–12 identyfikatorów źródeł jako tekst |
| `agents` | `Array<{role: string, summary: string}>` |
| `submission`, `dispatch` | `{status: string, detail: string | null}` |

Każdy sektor zawiera `sector` (1–200 znaków), `sensors: {emf_milligauss: number >= 0, temp_c: number, motion_events: integer >= 0}`, `sighting: null | {entity_class: string, confidence: number 0..1, witness_count: integer >= 0}`, `civilian_status` (1–300 znaków) i `containment_state` (1–100 znaków). `sighting` może być pominięte i przyjmuje wtedy `null`.

Fixtures zachowują kopertę `{scenario, ticks: Tick[]}`. `outbreak` wybiera pierwszy tick z `fixtures/outbreak-level-5.json` (lokalna reguła daje `evacuate`), a `control` pierwszy tick z `fixtures/control-tick.json` (daje `observe`). Starter nie odtwarza jeszcze całej tablicy ticków. Pole `via` w fixtures może zachowywać historyczne `one-mcp`; nie wybiera ono transportu i nie omija aktualnej polityki Track 1.

## Demo, offline i live

`RUN_MODE=demo` to jedyny obecny tryb offline; nie ma oddzielnej wartości `RUN_MODE=offline`. Demo używa deterministycznych reguł lokalnych i opisuje role jako symulowane. Nie importuje CrewAI do inferencji, nie wywołuje partnerów, nie pobiera scenariusza z sieci. Submit/dispatch są tylko lokalną symulacją; control z `observe` ma dispatch `not_required`. Demo scoreboard jest pusty i jawnie oznaczony jako lokalny.

`RUN_MODE=live` korzysta z `SCENARIO_NAME`, a nie wyboru fixture z przeglądarki. Najpierw wykorzystuje zachowany pending tick dla tego kontekstu lub jawnie pobiera nowy tick, co przesuwa kursor zespołu. Następnie pobiera You.com grounding i uruchamia lokalnie trzy role CrewAI przez Parasail. Role działają sekwencyjnie, z częściowymi wejściami; nie otrzymują narzędzi write. Decyzja musi zawierać istniejące źródło You.com i identyfikator ticka. Błąd live nie przełącza systemu na demo. Samo utworzenie rundy nie uruchamia submission ani Discorda.

Live wymaga oddzielnych flag: `SCENARIO_ALLOW_TICK=true` przed rundą/pobraniem ticka, `SCENARIO_ALLOW_SUBMIT=true` przed submission oraz `DISCORD_SEND_ENABLED=true` przed dispatch. Domyślnie wszystkie są wyłączone. Discord dodatkowo wymaga One, jawnego `ONE_CONNECTION_KEYS` i prywatnego `DISCORD_CHANNEL_ID` obecnego w `DISCORD_ALLOWED_CHANNEL_IDS`; znany oficjalny kanał jest zabroniony także po dodaniu do allowlisty. Cel z ticka jest niezaufaną informacją i nigdy nie kieruje wysyłką. Blokady są sprawdzane przed rezerwacją efektu i ponownie w adapterach. Nieaktywna flaga lub brak wymaganej konfiguracji daje `503`, bez zewnętrznego requestu.

Pozytywne budżety są warunkiem uruchomienia; ograniczenia wywołań nie są jeszcze pełnym rozliczeniem zużycia oficjalnego budżetu. Smoke test demo potwierdza lokalny kontrakt, nie autentyczne użycie partnerów wymagane w konkursie.

## Błędy i trwałość

Next.js zawsze zwraca błędy jako `{"error":"bezpieczny komunikat"}`. Nie przekazuje surowego body dostawcy, adresów z poświadczeniami ani stack trace. FastAPI zwykle używa `{"detail": ...}`; błąd walidacji może mieć listę szczegółów. Proxy zastępuje je własnym komunikatem.

| HTTP | Znaczenie |
| --- | --- |
| `400` | nieprawidłowy JSON, fixture lub id; odrzucone dane operacji |
| `401` | niezgodny token workera |
| `403` | niedozwolony Origin lub zablokowana polityką operacja |
| `404` | nie ma takiej zapisanej rundy |
| `409` | trwa inna runda; zmienił się tryb lub kontekst zapisanej rundy |
| `413` / `415` | za duże body / nieprawidłowy Content-Type w Next.js |
| `422` | dane nie przechodzą walidacji workera |
| `429` | limit, jeśli worker zwróci ten status |
| `502` | błąd integracji albo niepoprawny JSON/health workera |
| `503` | worker niedostępny, timeout lub niegotowa konfiguracja |
| `500` | nieoczekiwany błąd lokalnego handlera Next.js |

SQLite przechowuje rundy, pending ticks i rezerwacje efektów. Stany efektów używane przez starter: `ready`, `not_required`, `in_progress`, `simulated`, `submitted`, `dispatched`, `duplicate`, `unknown`. Dodatni HTTP z `Run` nie musi oznaczać wykonania efektu — klient musi sprawdzić `status`. Rezerwacja jest zapisywana przed zewnętrznym wywołaniem; ponowne kliknięcie nie stanowi automatycznego retry. Niepotwierdzony dispatch pozostaje `unknown`, a przerwanie po rezerwacji może pozostawić `in_progress`; wymaga to sprawdzenia stanu przed ręcznym działaniem. Submission może wrócić do `ready` z opisem do ręcznego ponowienia tej samej rundy. Zmiana trybu, zespołu, scenariusza lub celu nie uprawnia do ponownego użycia starej rundy.

## Weryfikacja i ograniczenie Track 1

`npm run smoke` uruchamia izolowany lokalny scenariusz HTTP bez użytkowego `.env`; `npm run verify` łączy testy JS/Python, kontrolę typów, build i smoke. Wyniki bieżącego wykonania i blokery zapisuje `docs/VERIFICATION.md`. Żaden test M0 nie publikuje wiadomości ani oficjalnych submissions.

One pozostaje wybraną przez użytkownika integracją Discorda. Adapter jest gotowy do dalszej weryfikacji prywatnego celu, z wyłączonym domyślnie send. W M0 nie wykonano wysyłki. Jest przy tym rozbieżność z aktualnym przewodnikiem organizatora: §3.4 wskazuje webhook dla eskalacji Track 1, zabrania One w tej ścieżce i opisuje manualny fallback. Należy wyjaśnić ją z organizatorem przed oficjalnym przebiegiem; prywatny sukces One nie potwierdza automatycznie zgodności konkursowej ani punktacji. Webhook nie jest zaimplementowany w tym M0. Źródło: [przewodnik w zweryfikowanej wersji 424320d](https://github.com/youdotcom-oss/halloween-hack-2026/blob/424320dbc9b217849df85f54cca20e493861692a/index.html), commit z 28.10.2026, 15:02:57 PDT; [bieżące verification notes](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes).
