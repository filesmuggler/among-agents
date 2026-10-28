# Audyt konfiguracji M0

Data: 28 października 2026, America/Los_Angeles. Repozytorium: lokalne `SF/among-agents`. Audyt obejmuje nazwy konfiguracji i ochronę plików; nie potwierdza poprawności poświadczeń ani integracji live.

## Zastany stan

Gałąź `main` śledzi `origin/main`. Przed M0 `README.md` był zmodyfikowany, a istniejący starter Next.js/Python, fixtures, testy, lockfiles i konfiguracja były nieśledzone. Śledzone pliki obejmowały `LICENSE` i `README.md`. Istniejący starter jest punktem wyjścia: nie należy zastępować go drugim scaffoldem ani resetować working tree.

`git check-ignore` potwierdził ochronę `.env`, `.env.local`, `worker/.env` oraz lokalnych `.venv`, `.next`, `node_modules` i bazy SQLite. `git ls-files` dla nazw `.env`/`.env.*` nie zwrócił plików. `.env.example` ma pozostać dozwolonym szablonem do wersjonowania. Te kontrole nazw nie są skanem całej historii Git pod kątem każdego rodzaju sekretu.

## Historyczny stan nazw przed uzupełnieniem `.env`

| Nazwa | Wynik audytu |
| --- | --- |
| `YDC_API_KEY` | nazwa obecna; uprawnienia i działanie niezweryfikowane |
| `PARASAIL_API_KEY` | nazwa obecna; model, dostęp i billing niezweryfikowane |
| `ONE_API_KEY` | nazwa obecna; połączenia i uprawnienia niezweryfikowane |
| `DISCORD_CHANNEL_ID` | nazwa obecna; prywatny charakter i tożsamość celu niepotwierdzone |
| `SCENARIO_MCP` | nazwa obecna; live discovery/tick niewykonane w M0 |
| `TEAM_HANDLE` | nazwa obecna; oficjalna rejestracja i poprawność nieweryfikowane |
| `WORKER_TOKEN` | brak; wymagany przed chronionymi operacjami live |

Wartości, długości i hashe istniejących sekretów nie są częścią raportu. Nie skopiowano ustawień użytkownika do szablonu, dokumentacji ani Linear. Powyższa tabela opisuje stan początkowy. Na późniejsze, wyraźne polecenie właściciela uzupełniono konfigurację, jak opisano poniżej. Instrukcja wygenerowania tokenu dla nowego checkoutu bez wypisywania jest w [configuration.md](configuration.md).

## Ukończenie konfiguracji — 28.10.2026

- Wygenerowano lokalny `WORKER_TOKEN` bez wypisywania. Istniejące klucze API i pozostałe ustawienia zachowano.
- Wybrano jedyne połączenie Discord dostępne przez One i zapisano `ONE_CONNECTION_KEYS`. Odczyt serwerów HTTP 200 potwierdził wskazany serwer i własność konta.
- Użytkownik podał ID prywatnego kanału. Zaktualizowano `DISCORD_CHANNEL_ID` i dodano `DISCORD_ALLOWED_CHANNEL_IDS`; prywatnych identyfikatorów nie zapisano w dokumentacji.
- Odczyt listy kanałów i metadata wskazanego kanału przez One zwraca HTTP 401. Tożsamość kanału opiera się na potwierdzeniu użytkownika; przyczyna błędu i uprawnienia do wysyłki pozostają niezweryfikowane w M1.
- Offline doctor i lokalny preflight PASS. `.env` ma uprawnienia 0600, pozostaje ignorowany i nieśledzony. `RUN_MODE=demo`; wszystkie bramki efektów są jawnie `false`. Nie wysłano ani nie odczytano wiadomości.

Dowód bez sekretów: [config-completion.txt](../evidence/AA-00/config-completion.txt).

## Bezpieczne ustawienia M0

Domyślne demo działa bez kluczy, bez `.env` i bez requestów do partnerów. Brak lokalnego tokenu nie blokuje tej weryfikacji. Obecność kluczy w `.env` nie włącza sama z siebie live, pobierania ticków ani zewnętrznych writes. Dokładne przełączniki i ich warunki opisuje [configuration.md](configuration.md).

Oficjalny kanał usunięto z domyślnego loadera i szablonu; później, na polecenie właściciela, zastaną lokalną wartość celu zastąpiono wskazanym przez niego prywatnym kanałem. Niepotwierdzony cel ma pozostać zablokowany przed requestem. Prywatnego channel ID ani connection key nie należy przenosić do dowodów.

One pozostaje wybraną integracją Discorda, a wysyłka wymaga jawnych ustawień prywatnego celu. Zaktualizowany przewodnik organizatora zabrania jednak One jako transportu eskalacji Track 1 i wskazuje webhook. To otwarta rozbieżność do wyjaśnienia przed oficjalnym przebiegiem; M0 nie zastępuje wybranej integracji inną. Samo posiadanie `ONE_API_KEY` nie potwierdza działania ani zgodności konkursowej. Szczegóły i datowane źródło: [api-contract.md](api-contract.md).

## Otwarte warunki przed live

- Przy kolejnym uruchomieniu oba procesy muszą wczytać uzupełnioną konfigurację; token jest już zapisany.
- Potwierdzić dostęp do Parasail, właściwy model/billing oraz You.com; stan `SET` w doctor to nie test credentials.
- Zweryfikować aktualny kontrakt scenariusza i ewentualny token zespołu; pobranie ticka przesuwa kursor.
- Wyjaśnić HTTP 401 w odczycie kanału One i potwierdzić rzeczywiste uprawnienia; wyjaśnić z organizatorem rozbieżność One/webhook przed oficjalnym przebiegiem. Wysyłka nie jest częścią M0.
- Potwierdzić finalne zasady, termin formularza i świadomą aktywację oficjalnego submission.

Wyniki testów, w tym ewentualne ograniczenia czystej instalacji lub środowiska, znajdują się w [VERIFICATION.md](VERIFICATION.md). Audit konfiguracji nie uprawnia do oznaczenia integracji live jako PASS. W M0 nie wysyłano wiadomości na Discord.
