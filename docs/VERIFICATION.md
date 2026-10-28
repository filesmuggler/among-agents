# Weryfikacja M0 Foundation

Data: 28.10.2026 (America/Los_Angeles). Zmiany wykonano bezpośrednio w `/Users/kris/SF/among-agents`, na istniejącym niezacommitowanym starterze. Nie tworzono drugiego szkieletu, nie resetowano Git, nie wykonywano commitów. Lockfiles, fixtures, UI i licencja pozostały bez zmian. Na późniejsze polecenie właściciela uzupełniono lokalny `.env`, zachowując istniejące klucze API i pozostałe ustawienia poza jawnie wskazanym celem Discorda.

## Zmiany

- `.env.example` i `.gitignore`: puste klucze/cel Discorda, domyślne demo, ochrona plików env także backupów oraz prywatnych dowodów.
- `worker/among_agents/config.py`, `app.py`, `integrations.py`: osobne, domyślnie wyłączone `SCENARIO_ALLOW_TICK`, `SCENARIO_ALLOW_SUBMIT`, `DISCORD_SEND_ENABLED`. One wymaga prywatnego celu na allowliście i jawnych connection keys; oficjalny kanał jest odrzucany. Kanał z ticka nie przekierowuje wysyłki.
- `worker/among_agents/doctor.py`, `scripts/common.mjs`: diagnostyka wyłącznie nazw/statusów i pomijanie dotenv w izolowanych testach.
- `scripts/smoke.mjs`, `scripts/verify.mjs`, `package.json`: powtarzalna weryfikacja w tymczasowej kopii źródeł bez `.env`, ze sztucznymi znacznikami, własną bazą, blokadą zewnętrznych socketów Python i sprzątaniem procesów.
- Rozszerzone testy Pythona oraz README, kontrakt API, audyt konfiguracji, specyfikacja, macierz scoringu i decyzje. Historyczny master plan zachowano z datowaną korektą.

## Wyniki bieżącego wykonania

| Kontrola | Wynik i zakres |
| --- | --- |
| Offline `npm run doctor` w docelowym repo | PASS; nazwy i statusy bez wartości; wszystkie trzy bramki efektów wyłączone |
| `npm run verify` z docelowego repo | PASS; 8 testów Next/API + 34 testy Python |
| Produkcyjny build Next.js | PASS w izolowanej kopii bez `.env`, webpack |
| TypeScript | PASS |
| Rzeczywisty HTTP Next → worker | PASS; outbreak/control, 3 symulowane role, oba sektory, symulowane efekty, auth, Origin i walidacja wejścia |
| Restart i odczyt historii | PASS; ta sama baza, runda i potwierdzenia; ponowny start na tych samych portach |
| Izolacja i cleanup | PASS; brak zewnętrznych prób połączeń workera, syntetyczne sekrety nieobecne w odpowiedziach i plikach klienta; procesy zatrzymane, porty zwolnione |
| Czyste npm/Python z obu lockfileów | PASS w nowym katalogu; `npm ci` i `uv sync --frozen --extra dev`, Python 3.12 |
| `npm run smoke` na świeżych zależnościach | PASS; Next dev z webpack, bez użytkowego `.env` |
| Standardowe `npm run dev` na czystej instalacji | PASS; Next Turbopack + worker, `/api/health` zwraca demo; Ctrl+C zatrzymuje oba procesy, porty 3000/8000 wolne |
| Ochrona plików Git | PASS; `.env` nieśledzony i ignorowany, szablon dozwolony, żadnego usuniętego pliku bazowego ani zmiany lockfileów |
| Kontrola wybranych wzorców poświadczeń w zmienionych plikach | Bez trafień; nie jest to audyt całej historii Git |

Wersje: lokalny Node **24.22.1**, Python **3.12.14**, Next.js **16.4.3**, CrewAI **1.15.2**, MCP **1.26.0**. Testy CrewAI emitują 10 ostrzeżeń deprecacyjnych bibliotek; konstrukcja realnych obiektów CrewAI jest testowana, inferencja jest zastąpiona atrapą.

Pierwsza próba czystej instalacji offline ujawniła niepełny cache npm/Python. Pobranie brakujących zależności z rejestrów i ponowna instalacja zakończyły się sukcesem. Npm zgłosił ostrzeżenie o starszym globalnym Node podczas bootstrapu, po czym zainstalował przypięty lokalny Node. Nie zmieniono globalnego runtime ani lockfileów. Pierwszy samodzielny smoke ujawnił inną ścieżkę plików klienta w Next dev; poprawiono `.next/dev/static` i ponowiony smoke przeszedł. Początkowa blokada bind loopback w sandboxie została rozwiązana uruchomieniem lokalnej weryfikacji z odpowiednim uprawnieniem.

## Konfiguracja i blokery live

W `.env` potwierdzono nazwy: `YDC_API_KEY`, `PARASAIL_API_KEY`, `ONE_API_KEY`, `DISCORD_CHANNEL_ID`, `SCENARIO_MCP`, `TEAM_HANDLE`. Wartości kluczy zachowano bez ujawniania.

Na polecenie właściciela wygenerowano i zapisano `WORKER_TOKEN`, dopisano `ONE_CONNECTION_KEYS` oraz `DISCORD_ALLOWED_CHANNEL_IDS`, a `DISCORD_CHANNEL_ID` ustawiono na prywatny kanał podany przez użytkownika. Wpisy `RUN_MODE=demo`, `DISCORD_SEND_ENABLED=false`, `SCENARIO_ALLOW_TICK=false`, `SCENARIO_ALLOW_SUBMIT=false` są jawnie zapisane. `.env` ma uprawnienia 0600, jest ignorowany i nieśledzony. Końcowy offline doctor i czysto lokalna walidacja konfiguracji dispatch przeszły; rzeczywisty dispatch nadal blokuje wyłączona bramka.

One w trybie wyłącznie odczytu potwierdził jedyne połączenie Discord, wskazany serwer i własność konta (lista serwerów HTTP 200). Odczyt listy kanałów oraz metadata podanego kanału zwraca HTTP 401. Kanał skonfigurowano na podstawie jawnego potwierdzenia użytkownika; metadata, przyczyna błędu i uprawnienia wysyłki pozostają do weryfikacji w M1. Nie odczytano ani nie wysłano wiadomości. Dowód: `evidence/AA-00/config-completion.txt`. Obecność klucza nie potwierdza modelu, salda ani pełnego działania integracji.

Nie wykonano inferencji Parasail, płatnego You.com Search, live scenario discovery/tick, submission ani wysyłki Discord. Rzeczywiste działanie partnerów pozostaje do sprawdzenia w M1. Instalowanie bibliotek z rejestrów nie jest testem tych integracji.

**One pozostaje wybraną integracją projektu zgodnie z decyzją użytkownika.** Jednocześnie najnowszy odczytany przewodnik §3.4 wymaga webhooka i wyklucza One w oficjalnym dispatch Track 1. Tę rozbieżność zapisano jako otwartą kwestię konkursową; nie zastąpiono One innym transportem i nie obiecujemy punktów za samą integrację. Źródło: [przewodnik, commit 424320d](https://github.com/youdotcom-oss/halloween-hack-2026/blob/424320dbc9b217849df85f54cca20e493861692a/index.html), aktualizacja 28.10.2026 o 15:02:57 PDT; [§11 verification notes](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes).

## Linear

Zaktualizowano istniejące zadania, bez duplikatów:

- [SKY-39 / AA-00](https://linear.app/skymoondev/issue/SKY-39): **Done** — kod i testy ochrony, lokalny token oraz konfiguracja prywatnego celu One ukończone; istniejące klucze zachowane. Otwarty błąd odczytu kanału HTTP 401 opisano jako warunek M1, bez deklarowania PASS_LIVE.
- [SKY-40 / AA-01](https://linear.app/skymoondev/issue/SKY-40): **Done** — specyfikacja, scoring, kontrakt i jawne otwarte kwestie.
- [SKY-41 / AA-02](https://linear.app/skymoondev/issue/SKY-41): **Done** — starter, czysta instalacja, build, testy, smoke i cleanup.

Wszystkie trzy zadania M0 mają status Done. M1–M4 pozostają osobnymi etapami; konfiguracja M0 nie jest potwierdzeniem integracji live.

## Uruchomienie

```sh
cd /Users/kris/SF/among-agents
npm run dev
```

Panel: `http://127.0.0.1:3000`. Weryfikacja: `npm run verify`; krótszy test HTTP: `npm run smoke`; diagnostyka nazw/statusów: `npm run doctor`. Zależności są już zainstalowane. Przy nowym checkoutcie najpierw `npm run setup` (wymaga dostępu do rejestrów). W tej sesji wszystkie uruchomione serwery zostały zatrzymane.

---

# Zastany raport wcześniejszego startera — zapis historyczny

Poniższy tekst zachowano z istniejącej pracy. Nie jest wynikiem nowej sesji M0; aktualne wyniki i polityka są powyżej.

# Weryfikacja lokalnego setupu

Data: 2026-10-28. Instalacja, 25 testów i build powtórzone pomyślnie w docelowym repozytorium `/Users/kris/SF/among-agents`. Zakres: lokalny starter, bez publikacji i bez zewnętrznych akcji zapisu.

## Potwierdzone

- Instalacja przypiętych zależności npm i Python 3.12; lokalny Node 24.22.1 spełnia wymagania WithOne.
- Build Next.js 16.4.3 i kontrola TypeScript.
- 8 testów Next/API: walidacja wejścia, Origin/Host i porty, normalizacja adresu Next.js, blokada forwarded-host, ochrona danych dostawcy, loopback worker.
- 17 testów workera: oba oficjalne fixtures, wszystkie sektory, budżet, brak kluczy/live bez fallbacku, uwierzytelnianie, deduplikacja, retry przed wysyłką, niepewny wynik Discord, zachowanie ticka po błędzie, związanie rundy z konfiguracją, schematy MCP i CrewAI.
- Konstrukcja rzeczywistych Agent/Task/Crew/LLM z zainstalowanego CrewAI 1.15.2; wykonanie inferencji zastąpione w teście. Nie jest to potwierdzenie odpowiedzi Parasail.
- Przepływ demo Next → worker → zapis lokalny, testowe zgłoszenie i testowy Discord; w demo żadne z nich nie wysyła danych do partnerów.
- Oficjalny scenario MCP: read-only initialize + tools/list, serwer `halloween-hack-26-scenario` 4.0.7. Dodatkowo potwierdzono initialize + tools/list przez gotowy adapter Python z tego projektu. Odczyt potwierdził wymagane argumenty `team` i `scenario` oraz podstawowe narzędzia. Nie pobrano ticka, nie przesunięto kursora i nie przekazano decyzji.
- Ochrona `.env`, `.env.*`, `.onerc`, kluczy, logów i bazy w `.gitignore`. Istniejący plik `.env` oraz licencja zachowane; README rozszerzony z zachowaniem dotychczasowej treści.

## Nieweryfikowane na koncie użytkownika

| Integracja | Co zostało zrobione | Co pozostaje do potwierdzenia |
| --- | --- | --- |
| Parasail | Natywny provider OpenAI CrewAI, prawidłowy base URL i model ID | Prawdziwa inferencja, kredyty, dostępność modelu, latency i limity |
| You.com | Adapter Search + testy/kontrakt dokumentacji, wymagana obecność źródeł w decyzji | Zapytanie z kluczem użytkownika i jakość źródeł |
| WithOne/Discord | Przypięty lokalny MCP, sprawdzanie schemas i uprawnień, walidacja potwierdzenia wysyłki | Prawdziwe połączenie Discord, event role, write access, odbiór wiadomości |
| Scenario MCP | Połączenie i discovery działają | Pobranie ticka dla własnego zespołu, wynik containment, aktualizacja scoreboardu |
| Pełny przepływ live | Gotowe adaptery i sekwencyjne role, blokady i ręczne akcje | End-to-end po uzupełnieniu `.env`, bez zastąpionych usług |

Nie uruchomiono zewnętrznej inferencji, płatnego Search ani wysyłki Discord. `npm run doctor -- --network` jest osobnym krokiem użytkownika i może zużyć kredyty Search; nie wykonuje inferencji ani zapisów. Dopiero udana analiza live i świadome kliknięcia publikacji weryfikują cały przebieg.

## Ograniczenia

Demo jest deterministyczną demonstracją na danych organizatora, a nie rojem kwalifikującym się do oceny. Starter live ma trzy sekwencyjne role; nie implementuje całej referencyjnej architektury Track 1 (embeddings, indeks lore, pamięć semantyczna, ciągły autonomiczny loop). Wyniku konkursowego nie zweryfikowano. CrewAI emituje ostrzeżenia deprecacyjne z własnego kodu; testy przechodzą.

Oficjalny przewodnik: https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes. Źródła i konkretne różnice wobec pseudokodu organizatora opisano w README.
