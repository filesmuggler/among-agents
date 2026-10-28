# Konfiguracja lokalna

M0 zachowuje istniejące klucze w `.env`; na polecenie właściciela dopisano token i ustawienia One oraz skonfigurowano wskazany prywatny kanał. `.env.example` jest pustym szablonem z publicznymi, niesekretnymi ustawieniami domyślnymi. Nie kopiuj szablonu na istniejący plik; uzupełniaj wyłącznie potrzebne wpisy. Wszystkie ustawienia integracji i workera są serwerowe, bez prefiksu `NEXT_PUBLIC_`.

## Start bez kluczy

`npm run setup` instaluje zależności z lockfiles; `npm run dev` uruchamia Next.js i lokalny worker. Domyślny `RUN_MODE=demo` używa fixtures i nie kontaktuje się z usługami zewnętrznymi. `npm run doctor` sprawdza lokalną konfigurację i wypisuje nazwy/statusy, bez wartości. Flaga `--network` jest oddzielnym, świadomie wybieranym sprawdzeniem usług; wykonuje między innymi płatne zapytanie You.com, więc nie jest częścią offline M0.

`npm run smoke` używa izolowanego środowiska, bez użytkowego `.env` i z tymczasową bazą; `npm run verify` uruchamia pełny lokalny zestaw kontroli. Samo `SKIP_DOTENV=1` pomija plik, lecz nie usuwa sekretów już obecnych w środowisku procesu. Smoke zapewnia również osobne, ograniczone środowisko. Więcej o rzeczywistych wynikach: [VERIFICATION.md](VERIFICATION.md).

## Ustawienia

| Zmienna | Domyślnie / znaczenie |
| --- | --- |
| `RUN_MODE` | `demo`; druga poprawna wartość to `live` |
| `WORKER_URL` | `http://127.0.0.1:8000`; tylko lokalny HTTP bez dodatkowej ścieżki |
| `WORKER_TOKEN` | puste; wspólny Bearer token Next.js/Python, wymagany dla live |
| `WORKER_DB` | nieustawione → `worker/.data/runs.sqlite3`; lokalny plik, ignorowany przez Git |
| `TEAM_HANDLE` | puste; dla live 2–32 małe litery/cyfry/myślniki, początek alfanumeryczny |
| `YDC_API_KEY` | puste; wymagane do You.com grounding |
| `PARASAIL_API_KEY` | puste; wymagane do inferencji live |
| `PARASAIL_BASE_URL` | `https://api.parasail.io/v1` |
| `PARASAIL_MODEL` | `parasail-glm-53-flash`; nazwa domyślna, faktyczny dostęp pozostaje do sprawdzenia |
| `ONE_API_KEY` | puste; wymagane do Discorda przez One |
| `ONE_CONNECTION_KEYS` | puste; jawna lista dozwolonych connection keys rozdzielona przecinkami, wymagana do dispatch |
| `DISCORD_CHANNEL_ID` | puste; jawnie skonfigurowany prywatny kanał, bez oficjalnego fallbacku |
| `DISCORD_ALLOWED_CHANNEL_IDS` | puste; lista zatwierdzonych prywatnych channel IDs rozdzielona przecinkami |
| `SCENARIO_MCP` | `https://api.you.com/mcp/halloween-hack-26` |
| `SCENARIO_NAME` | `outbreak-level-5`; alternatywa `control-tick` |
| `SCENARIO_TEAM_TOKEN` | puste; tylko jeśli wydany/wymagany przez organizatorów |
| `SKIP_DOTENV` | nieustawione; wartość `1` pomija ładowanie `.env` podczas izolowanych testów |

Nie każda operacja potrzebuje wszystkich kluczy. Live run wymaga Parasail, You.com i lokalnego tokenu. Submission/scoreboard wymagają konfiguracji scenariusza i tokenu workera, a nie kluczy do inferencji. Dispatch wymaga One, connection keys i dopuszczonego prywatnego celu. Walidacja live dodatkowo sprawdza format zespołu, nazwę scenariusza, HTTPS dla adresów integracji i limit tokenu scenariusza.

## Oddzielne przełączniki efektów

W szablonie wszystkie poniższe wartości to `false`. Tylko tekst `true` (bez względu na wielkość liter i otaczające spacje) włącza flagę; brak, literówka, `1` lub inne wartości pozostawiają ją wyłączoną. `RUN_MODE=live` nie włącza żadnej z nich.

| Flaga | Dopuszczana operacja po spełnieniu pozostałych warunków |
| --- | --- |
| `SCENARIO_ALLOW_TICK` | wykonanie live run i pobranie ticka; pobranie przesuwa kursor zespołu |
| `SCENARIO_ALLOW_SUBMIT` | submission zapisanej decyzji do oficjalnego feedu/scoreboardu |
| `DISCORD_SEND_ENABLED` | rzeczywista wysyłka przez One na skonfigurowany prywatny kanał |

Nieaktywna flaga blokuje właściwą operację przed wywołaniem integracji. Nie należy włączać ich zbiorczo w celu przejścia doctor. Ustalenie konfiguracji, pobranie scenariusza, submission i Discord są osobnymi działaniami. M0 pozostawia wszystkie zewnętrzne efekty wyłączone i nie wykonuje wysyłki.

Kanał Discorda musi być numerycznym ID i występować w `DISCORD_ALLOWED_CHANNEL_IDS`. Znany oficjalny kanał imprezy jest zawsze odrzucany przez prywatny adapter. Allowlista jest deklaracją operatora, a nie dowodem prywatności — wcześniej trzeba sprawdzić rzeczywisty serwer/kanał i uprawnienia. Kanał lub etykieta z ticka nigdy nie zastępuje lokalnego celu. Adapter One wybiera dokładnie jedno połączenie z właściwym dostępem w zadanej liście; niejednoznaczny wybór blokuje wysyłkę. Treść ma wyłączone wzmianki Discord.

Po zmianie `.env` uruchom oba procesy ponownie. Nie kasuj bazy przy problemach z dispatch: przechowuje rezerwacje efektów, potrzebne do uniknięcia duplikatów. Nieznany wynik wysyłki należy zweryfikować przed ręcznym ponowieniem.

## Opcjonalne wygenerowanie lokalnego tokenu

W lokalnym repozytorium token został już wygenerowany i zapisany na polecenie właściciela, bez wypisywania wartości. Nie uruchamiaj ponownie generatora dla tego pliku. Dla nowego checkoutu bez tokenu można uruchomić poniższy skrypt **z głównego katalogu repozytorium**. Dopisuje nowy token bez wypisywania wartości, zachowuje obecne wpisy i zatrzymuje się, jeśli jakikolwiek wpis `WORKER_TOKEN` już istnieje (również pusty). Nie jest to komenda potrzebna do demo ani smoke.

```sh
node --input-type=module <<'JS'
import { existsSync, readFileSync, openSync, writeSync, closeSync, chmodSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
const file = '.env';
const existing = existsSync(file) ? readFileSync(file, 'utf8') : '';
if (/^\s*(?:export\s+)?WORKER_TOKEN\s*=/m.test(existing)) {
  throw new Error('WORKER_TOKEN już ma wpis. Zachowano plik bez zmian.');
}
const fd = openSync(file, 'a', 0o600);
try {
  const separator = existing && !existing.endsWith('\n') ? '\n' : '';
  writeSync(fd, separator + 'WORKER_TOKEN=' + randomBytes(32).toString('hex') + '\n');
} finally {
  closeSync(fd);
}
chmodSync(file, 0o600);
console.log('Dodano lokalny WORKER_TOKEN bez wypisywania. Uruchom ponownie oba procesy.');
JS
```

Sprawdź ochronę pliku przez `git check-ignore .env`; `.env` nie może trafić do commita, logów, załączników ani wiadomości. Nie używaj szerokiego `git add .` do wybierania zmian M0. Nie wklejaj tokenu do przeglądarki: serwer Next.js pobierze go z konfiguracji.

## One i aktualne zasady konkursu

Zgodnie z wyborem użytkownika One jest docelową integracją Discorda projektu; M0 przygotowuje jej bezpieczną prywatną ścieżkę, bez wysyłki. Jednocześnie oficjalny przewodnik z 28.10.2026 (§3.4) wymaga webhooka i zabrania One do eskalacji Track 1. Zachowujemy tę rozbieżność jako jawne pytanie do organizatora przed oficjalnym przebiegiem, bez gwarancji punktacji za One. Nie zaimplementowano webhooka i nie zmieniono wybranej integracji na inną. Źródła: [datowana wersja przewodnika](https://github.com/youdotcom-oss/halloween-hack-2026/blob/424320dbc9b217849df85f54cca20e493861692a/index.html), [verification notes](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes).

Skrypty lokalne wyłączają telemetrię CrewAI/OpenTelemetry i Next.js przez `CREWAI_TRACING_ENABLED=false`, `OTEL_SDK_DISABLED=true`, `DO_NOT_TRACK=true`, `NEXT_TELEMETRY_DISABLED=1`. Wartości kluczy nie są przekazywane agentom w promptach. Szczegóły API i stanów efektów: [api-contract.md](api-contract.md).
