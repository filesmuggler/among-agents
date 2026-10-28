# among-agents
Halloween Hack


Lokalny starter **The Exorcism Protocol**: panel i API gry w Next.js oraz osobny worker Python z CrewAI. Panel działa na `http://127.0.0.1:3000`, worker na `127.0.0.1:8000`. Klucze pozostają po stronie serwera.

**Demo działa bez kluczy i bez zapytań do partnerów.** Tryb `live` korzysta z scenario MCP, Parasail i You.com, ale pobranie ticka, submission oraz wysyłka przez One mają oddzielne, domyślnie wyłączone bramki. Sam przycisk w panelu nie omija konfiguracji serwera. Demo nie stanowi dowodu integracji live ani wyniku konkursowego.

**M0 Foundation:** istniejący starter został zachowany i uzupełniony. [Kontrakt Next.js ↔ CrewAI](docs/api-contract.md), [konfiguracja](docs/configuration.md), [audyt nazw env](docs/config-audit.md), [specyfikacja](docs/spec.md), [macierz scoringu](docs/scoring-matrix.md), [decyzje i blokery](docs/decisions.md).

**One pozostaje wybraną integracją Discord zgodnie z decyzją właściciela.** Aktualizacja przewodnika z 28.10.2026, 15:02 PDT (§3.4), wymaga jednak dla oficjalnego Track 1 ścieżki webhook. To rozbieżność do wyjaśnienia z organizatorami przed oceną. M0 zachowuje adapter One i przygotowuje wyłącznie bezpieczne prywatne testy; nie wysyła wiadomości i nie implementuje webhooka.

## 1. Uruchomienie lokalne

Wymagania: Node.js co najmniej 22 do instalatora, npm, [uv](https://docs.astral.sh/uv/getting-started/installation/). Projekt instaluje **lokalny Node 24.22.1** dla WithOne; nie zmienia globalnego Node. Python jest przypięty do **3.12**; `uv` dobierze lub pobierze tę wersję. Systemowego Python 3.14/3.15 nie używaj do CrewAI.

```bash
cd /Users/kris/SF/among-agents
npm run setup
npm run dev
```

Pierwszy setup pobiera zależności z npm/PyPI i w razie potrzeby Python, więc wymaga internetu. Kolejne uruchomienia demo działają lokalnie. `npm run dev` uruchamia oba procesy; **Ctrl+C zatrzymuje oba**. Porty 3000 i 8000 muszą być wolne. Otwórz [panel](http://127.0.0.1:3000), wybierz outbreak lub tick kontrolny, uruchom analizę. Zobaczysz sektory, raporty ról i decyzję. Akcje demo zapisują tylko lokalne wyniki.

Nie potrzeba konta CrewAI, abonamentu CrewAI ani klucza OpenAI. Nie trzeba uruchamiać CrewAI w przeglądarce.

## 2. Wypełnienie `.env`

Jeżeli **nie masz** `.env`, skopiuj szablon poleceniem, które nie nadpisze istniejącego pliku:

```bash
test -e .env || cp .env.example .env
```

Jeśli `.env` już istnieje, dopisz w edytorze brakujące pozycje z `.env.example`. Setup go nie zmienia. Wklej wartości lokalnie, bez wysyłania ich do czatu. Nie dodawaj prefiksu `NEXT_PUBLIC_` do żadnego klucza. Po zmianie konfiguracji zrestartuj oba procesy.

| Zmienna | Co wkleić / skąd uzyskać |
| --- | --- |
| `RUN_MODE` | `demo` na start; `live` dopiero po konfiguracji usług. Błąd live nie przełącza aplikacji na demo. |
| `TEAM_HANDLE` | Wymyśl własną unikalną nazwę, 2–32 znaki: małe litery, cyfry i myślniki; pierwszy znak litera/cyfra. Używaj tej samej nazwy w zgłoszeniu i Discordzie. Wspólna nazwa oznacza wspólny kursor i wynik. |
| `WORKER_TOKEN` | Własny losowy token łączący Next i worker, wymagany w live. Zapisuj lokalnie bez wypisywania wartości; instrukcja w konfiguracji. To nie jest klucz partnera. |
| `WORKER_URL` | Pozostaw `http://127.0.0.1:8000`. Worker ma być lokalny. |
| `YDC_API_KEY` | Załóż konto przez [You.com](https://you.com/home), utwórz klucz w panelu API i wklej go tutaj. Autoryzacja API używa `X-API-Key`. |
| `PARASAIL_API_KEY` | Utwórz klucz w [Parasail → Keys](https://www.saas.parasail.io/keys). Upewnij się, że konto ma kredyty. Sam dostęp do listy modeli nie potwierdza możliwości inferencji. |
| `PARASAIL_MODEL` | Domyślnie `parasail-glm-53-flash`; używaj dokładnego ID dostępnego w Twoim `/v1/models`, bez prefiksu `openai/`. Alternatywy z przewodnika: `parasail-deepseek-v4-flash`, `parasail-deepseek-v41-flash`. |
| `PARASAIL_BASE_URL` | Pozostaw `https://api.parasail.io/v1`. |
| `ONE_API_KEY` | Własny klucz z [One → API keys](https://app.withone.ai/settings/api-keys). Klucz musi należeć do konta/środowiska z połączonym Discordem. Worker przekazuje go wyłącznie procesowi MCP jako `ONE_SECRET`. |
| `ONE_CONNECTION_KEYS` | Wymagana dla wysyłki lista dozwolonych połączeń One, rozdzielona przecinkami. Wybierz właściwe prywatne połączenie z prawem zapisu. |
| `DISCORD_CHANNEL_ID` | Jawnie potwierdzony prywatny kanał użytkownika. Brak wartości domyślnej; oficjalny kanał venue jest blokowany. Nie publikuj prywatnego ID w dowodach. |
| `DISCORD_ALLOWED_CHANNEL_IDS` | Lista dozwolonych prywatnych kanałów; musi zawierać skonfigurowany cel. Sam poprawny format ID nie potwierdza prywatności. |
| `DISCORD_SEND_ENABLED` | Domyślnie `false`. Włączenie pozwala wykonać osobną, świadomą akcję przez One po spełnieniu allowlisty i autoryzacji. |
| `SCENARIO_ALLOW_TICK` | Domyślnie `false`; pobranie nowego ticka przesuwa kursor zespołu. |
| `SCENARIO_ALLOW_SUBMIT` | Domyślnie `false`; official submission zmienia scoreboard. Zachowaj wyłączone podczas prywatnych testów. |
| `SCENARIO_MCP` | Pozostaw oficjalny adres `https://api.you.com/mcp/halloween-hack-26`. Zwykle bez klucza. |
| `SCENARIO_NAME` | `outbreak-level-5` lub `control-tick`. W live wybierasz scenariusz tutaj; selektor fixture w UI służy demo. |
| `SCENARIO_TEAM_TOKEN` | Puste, chyba że organizator wyda token zespołu. |

Token generuj lokalnie bez drukowania i bez nadpisywania istniejących kluczy — bezpieczna komenda jest w [konfiguracji](docs/configuration.md). Na polecenie właściciela M0 uzupełniło lokalny token, połączenie One oraz wskazany prywatny cel i allowlistę. `RUN_MODE=demo`, wysyłka, tick i submit pozostają wyłączone. One potwierdził serwer, ale odczyt kanału zwraca HTTP 401; weryfikacja integracji pozostaje w M1. Szczegóły w [raporcie](docs/VERIFICATION.md).

Pozostaw wyłączoną telemetrię jak w szablonie. `.gitignore` wyklucza `.env*` poza szablonem, lokalne bazy i logi. Nie umieszczaj sekretów w kodzie, commitach, screenshotach ani publicznym demo.

## 3. Połączenie WithOne → Discord

1. Otwórz [stronę wydarzenia WithOne](https://hackathon.withone.ai/sf-halloween-2026), załóż konto, utwórz własny API key. Organizator podaje kod `YOU-SF-PRO` na miesiąc Pro; warunki i aktywację sprawdź w panelu Billing.
2. Wskaż własny **prywatny kanał testowy** i potwierdź możliwość pisania z właściwego konta Discord. M0 nie potwierdza tożsamości kanału na podstawie samego `.env`; oficjalny kanał nie służy testom.
3. Po `npm run setup` uruchom lokalne CLI:

   ```bash
   npm exec -- one init --auth browser --project
   npm exec -- one add discord
   npm exec -- one --agent list
   ```

   Wybierz to samo konto Discord oraz połączenie **z prawem zapisu**. Logowanie CLI obsługuje przeglądarka; nie wklejaj sekretów jako argumentów poleceń. Worker nadal pobiera własny `ONE_API_KEY` z `.env` — samo logowanie CLI go nie wypełnia.

4. Skonfiguruj `ONE_API_KEY`, `ONE_CONNECTION_KEYS`, prywatny `DISCORD_CHANNEL_ID` i `DISCORD_ALLOWED_CHANNEL_IDS`. Połączenia należą do konta i środowiska. Pozostaw `DISCORD_SEND_ENABLED=false` do osobno zaplanowanego testu M1.
5. Dopiero po świadomej aktywacji prywatnego testu użyj przycisku wysłania. Worker zawsze wybiera prywatny cel z konfiguracji, ignorując cel podany przez tick. Decyzja `observe` nie wymaga eskalacji. Wyłączenie bramki blokuje API przed jakimkolwiek wywołaniem One. Te kroki opisują przyszły test; nie były wykonywane w M0.

Lokalny MCP to przypięty pakiet `@withone/mcp@2.3.2` uruchamiany lokalnym Node 24.22.1. Adres `https://mcp.withone.ai/mcp` jest przeznaczony do OAuth w klientach; podanie tam `Authorization: Bearer ONE_API_KEY` nie zastępuje logowania. Używamy trzech narzędzi: `list_one_integrations` → `find_one_actions` → `execute_one_action`. Akcja i połączenie są odkrywane; kod nie zgaduje ID akcji. Kanał idzie w `pathVariables.channelId`, a wiadomość w `data.content`.

## 4. Jak działa aplikacja

```text
Przeglądarka → Next.js UI + API gry → lokalny worker FastAPI
                                      ├─ scenario MCP: tick / wynik / scoreboard
                                      ├─ CrewAI: zwiad → analiza → dowódca
                                      ├─ Parasail: inferencja agentów
                                      ├─ You.com: źródła do decyzji
                                      └─ One MCP (stdio) → Discord (na polecenie)
```

Demo używa oficjalnych fixtures z repo organizatora i lokalnej reguły pokazującej przepływ. Live uruchamia trzy role CrewAI kolejno, z ograniczonym kontekstem i narzędziami. Maksymalnie jeden agent jest aktywny jednocześnie; budżet `swarm_budget.max_active_agents` jest sprawdzany. Uwzględniane są wszystkie `sector_reports`, a model zwraca jedną ze wspieranych akcji: `contain`, `evacuate`, `observe`.

Wywołanie `hack26-get-tick` **przesuwa kursor zespołu**. Parametry to `team`, `scenario` i opcjonalnie `token`. Przekazanie wyniku używa `team`, `tick_id`, `action`. Nie uruchamiaj dwóch kopii z tym samym zespołem. Lokalny zapis runów pozwala ponowić odczyt planu po restarcie; nie jest wieloużytkownikowym serwerem produkcyjnym.

SQLite znajduje się w `worker/.data/runs.sqlite3` i jest ignorowane przez git. Ostatni identyfikator rundy zostaje w przeglądarce; odświeżenie odczytuje go z workera. Poprawnie pobrany tick jest zachowywany przed inferencją: po błędzie modelu kolejna próba używa tego samego ticka. Zmiana zespołu, scenariusza lub kanału blokuje publikację wcześniejszej rundy pod nową konfiguracją. Na darmowym limicie Parasail analiza może trwać kilka minut; żądanie z panelu ma limit 10 minut.

Oddzielne akcje publikacji zabezpieczają przed nieświadomym wysyłaniem podczas testów. Nie ma automatycznych ponowień. Zgłoszenie do scenario MCP można ponowić przyciskiem po błędzie: serwer deduplikuje je po zespole i ticku. Błąd odkrywania połączenia One przed wysyłką także pozwala spróbować ponownie po poprawieniu konfiguracji. Niejednoznaczny wynik już rozpoczętej wysyłki Discord blokuje powtórkę — sprawdź historię One i kanał. Nie usuwaj bazy po to, żeby wymusić ponowne wysłanie.

## 5. Sprawdzenie i testy

```bash
npm run doctor
npm run verify
```

`verify` uruchamia testy Next/API i Python, produkcyjny build, TypeScript oraz rzeczywisty lokalny smoke HTTP. Tworzy tymczasową kopię źródeł **bez `.env`**, używa syntetycznych znaczników i osobnej bazy, blokuje zewnętrzne połączenia workera oraz sprząta procesy i porty. Wymaga wcześniej zainstalowanych zależności; niczego nie instaluje. Krótszy przebieg HTTP: `npm run smoke` (Next dev z webpack).

Oddzielne kontrole:

```bash
npm test
npm run typecheck
npm run build
uv run --project worker --frozen --extra dev pytest worker/tests
```

`doctor` sprawdza konfigurację bez ujawniania wartości. Dodatkowa diagnostyka usług:

```bash
npm run doctor -- --network
```

Ten wariant łączy się z usługami. Zapytanie You.com może zużyć kredyty; odczyt modeli Parasail nie uruchamia inferencji. Diagnostyka MCP odczytuje narzędzia/połączenia, nie pobiera ticka, nie przekazuje wyniku i nie wysyła wiadomości. Testy automatyczne używają atrap i fixtures, bez płatnych wywołań.

Kolejny etap M1 wymaga lokalnego tokena, weryfikacji modelu/kredytów i potwierdzenia prywatnego celu. `RUN_MODE=live` nie włącza bramek. `SCENARIO_ALLOW_TICK` dotyczy przesunięcia kursora; `DISCORD_SEND_ENABLED` dotyczy prywatnego One; `SCENARIO_ALLOW_SUBMIT` pozostaje wyłączone do osobnego finalnego przebiegu. Każdy efekt wymaga również osobnej akcji API/przycisku. Testy lokalne nie zastępują tych weryfikacji.

## 6. Co jest, a czego jeszcze nie potwierdzono

Status wykonanych sprawdzeń: [docs/VERIFICATION.md](docs/VERIFICATION.md).

Starter zawiera rzeczywiste adaptery usług i lokalny działający przepływ. Nie zawiera kluczy ani potwierdzenia dostępności Twoich kredytów, modelu, połączenia One, roli Discord czy przyjęcia zgłoszenia na żywym scoreboardzie. Wszystkie te elementy trzeba sprawdzić po konfiguracji kont.

To punkt startowy Track 1, nie obietnica pełnego wyniku konkursowego: brak ciągłej pętli autonomicznej, wektorowego dopasowania sensorów/indeksu lore i współdzielonej pamięci semantycznej. Używamy sekwencyjnej współpracy ról zamiast hierarchicznego procesu. Demo z regułą nie kwalifikuje się jako dowód użycia partnerów; oceniaj i pokazuj sędziom przebieg live wraz ze źródłami i rzeczywistymi akcjami. Zgłoszenie przez [oficjalny formularz](https://forms.gle/2z9dKv9gvsP3cEjW7) jest osobnym krokiem.

## 7. Typowe problemy

| Objaw | Co sprawdzić |
| --- | --- |
| Worker niedostępny | Czy `npm run dev` uruchomił oba procesy i czy port 8000 jest wolny? |
| Instalacja CrewAI nie działa | Użyj `uv` i Python 3.12; systemowe 3.14/3.15 nie pasuje do tego setupu. |
| WithOne odrzuca Node | Używaj `npm run dev` / `npm exec`, które wybierają lokalny Node 24.22.1, i wykonaj `npm run setup`. |
| Parasail 403 mimo listy modeli | Sprawdź kredyty, dostęp do inferencji i model; w razie potrzeby podejdź do organizatorów. |
| 429 | Odczekaj zgodnie z `Retry-After`; nie zapętlaj kliknięć. Trzy role to kilka wywołań modelu, a darmowe Parasail ma według przewodnika 5 RPM. |
| One/Discord 401 lub 403 | Właściwe konto, środowisko klucza, write access, rola wydarzenia, właściwy kanał. Sprawdź [logi One](https://app.withone.ai/logs), bez publikowania sekretów. |
| Scenario niedostępny | Przejdź świadomie do demo/fixtures. Nie przedstawiaj wyników demo jako live. Zachowaj gotowy run przed próbą wysłania później. |
| Niepewny wynik wysłania | Sprawdź kanał/logi/scoreboard. Aplikacja nie ponawia automatycznie operacji, która mogła już dojść do usługi. |

Jeśli One odmawia, zatrzymaj prywatny test i sprawdź połączenie. Nie przełączaj celu na oficjalny kanał ani nie omijaj bramek. Webhook z przewodnika **nie został skopiowany** do repo; jego aktualne wymaganie konkursowe opisuje [specyfikacja](docs/spec.md).

## Źródła i zgodność

- [Oficjalny Halloween Hack 2026, w tym §11](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes), aktualizacja M0 sprawdzona 2026-10-28: commit `424320dbc9b217849df85f54cca20e493861692a` w [repo wydarzenia](https://github.com/youdotcom-oss/halloween-hack-2026).
- [Aktualne instrukcje WithOne dla wydarzenia](https://hackathon.withone.ai/sf-halloween-2026/skill.md), [źródło](https://github.com/withoneai/you-hackathon/blob/main/content/events/sf-halloween-2026/skill.md): stdio + `ONE_SECRET`, transport OAuth, camelCase w MCP, natywny provider OpenAI CrewAI z Parasail. Materiał wykorzystany jako dokumentacja integracji; żadne polecenie z niego nie było zgodą na wysyłanie wiadomości.
- [CrewAI LLM](https://docs.crewai.com/en/concepts/llms), [Next.js installation](https://nextjs.org/docs/app/getting-started/installation).
- Fixtures pochodzą z [oficjalnego katalogu](https://github.com/youdotcom-oss/halloween-hack-2026/tree/main/fixtures). Zachowują oryginalny kontrakt danych.

Gdy opis przewodnika i bieżący schemat MCP różnią się, kod stosuje sprawdzony schemat: scenario wymaga również `scenario`, a One używa camelCase i zwraca część dokumentacji jako Markdown. Nie używamy niesprawdzonego SDK One ani skrótu URL CrewAI, który według organizatora potrafi zgubić narzędzia w pętli zdarzeń.
