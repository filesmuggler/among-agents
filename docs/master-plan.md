# Among Agents — master plan
Stan audytu: 28.10.2026, America/Los_Angeles. Owner: Kris, praca solo. Theme 1: The Exorcism Protocol.

> Aktualizacja wykonawcza M0 (28.10.2026): stan implementacji i nowe wyniki są w [VERIFICATION.md](VERIFICATION.md), kontrakt w [api-contract.md](api-contract.md), aktualne zasady w [spec.md](spec.md). Poniższy audyt jest zachowanym snapshotem planowania. Oficjalny kanał usunięto z domyślnych ustawień, dodano allowlistę i oddzielne bramki tick/submit/One; `.env` pozostaje bez zmian. Przewodnik commit `424320dbc9b217849df85f54cca20e493861692a` zmienił §3.4 na webhook dla Track 1. Właściciel nadal wybiera **One** dla projektu i prywatnych testów; nie gwarantujemy akceptacji tej ścieżki przez jurorów. Nie wysłano wiadomości ani submission. Wcześniejsze sformułowania o fallback One opisują starszą wersję przewodnika.

## Cel i zakres
Działający lokalny supervised swarm: CrewAI Python + Parasail inference + You.com grounding + WithOne MCP/private Discord oraz oficjalny scenario MCP. Next.js prezentuje rzeczywisty przebieg: mapę sektorów, statystyki agentów, shared chat i scoreboard. Priorytetem jest poprawność decyzji, brak false alarms, szybkość oraz mierzalny wkład partnerów. AWS/deployment, rozbudowana mapa i wymagania Track 2 są poza podstawowym zakresem.

Ten dokument jest jednym master planem, odwzorowanym w Linear i repo. Stories zawierają planowane kryteria, nie wyniki wykonanych testów. Podczas przygotowania planu nie uruchomiono provider inference, nie pobrano live ticka, nie wysłano wiadomości ani containment submission. Wykonano repo/env audit, odczyt źródeł oraz publiczne MCP initialize/tools/list.

## Stan zastany i pewność dowodów
Końcowy odczyt repo z 28.10.2026 uwzględnia nowy, niecommitowany starter, który pojawił się w trakcie przygotowania planu. Nie tworzyć równoległego szkieletu ani nadpisywać tej pracy.
- Repo: /Users/kris/SF/among-agents; main, początkowy commit eba6bec, zmodyfikowany README i nowe pliki robocze.
- Istnieje Next.js UI/API (app/, lib/), FastAPI worker (worker/among_agents/), CrewAI scout/analyst/commander, adaptery Parasail/You.com/scenario/WithOne, SQLite runs, fixtures, lockfiles, setup/dev/doctor.
- .gitignore i .env.example są już w working tree; git check-ignore potwierdza ochronę .env. AA-00 weryfikuje ochronę oraz usuwa domyślny oficjalny cel Discorda z kodu/template/instrukcji testowych.
- Aktualne .env ma sześć ustawionych nazw: YDC_API_KEY, PARASAIL_API_KEY, ONE_API_KEY, DISCORD_CHANNEL_ID, SCENARIO_MCP, TEAM_HANDLE. Set ≠ valid ≠ tested. Wartości nie zostały ujawnione; prywatna tożsamość skonfigurowanego kanału nadal wymaga potwierdzenia.
- Brakuje WORKER_TOKEN w aktualnym .env; istniejący live validator wymaga co najmniej 24 znaków. Wygenerować lokalnie bez wypisywania. Brak RUN_MODE daje demo; model/base URL korzystają z domyślnych ustawień, dostęp do modelu wymaga realnego testu. Optional ONE_CONNECTION_KEYS nie jest ustawione; wybór niejednoznacznej integracji ma pozostać fail-closed.
- Najważniejsza luka: config.py i template/README zawierają domyślny oficjalny kanał Discord. Kod sprawdza składnię kanału i writable connection, ale nie dowodzi, że cel jest zatwierdzonym prywatnym kanałem. AA-00/06/07 dodają allowlistę/deny-by-default przed jakąkolwiek wysyłką; nie zmieniać rzeczywistego .env na podstawie domysłów.
- Istnieją 8 testów API i 17 testów workera. docs/VERIFICATION.md zapisuje 25 passing tests, typecheck/build, lokalny demo flow oraz MCP initialize/tools-list. Są to wyniki odnotowane w repo; podczas tego planowania nie uruchamiano ich ponownie ani nie odczytano osobnych raw execution logs.
- Ten sam dokument jawnie pozostawia nieweryfikowane live Parasail inference, płatny You.com search, realny WithOne/Discord send, live tick, submission i wynik scoreboardu. Nie oznaczać M1 Done na podstawie mocków/builda.
- Istnieją częściowe wejścia agentów i sekwencyjne przekazywanie wyników, ale brak trwałego shared chat/timeline, autonomicznej pętli ticków i pełnej księgowości tokenów/kosztu. UI ma sector cards, role summaries i raw scoreboard JSON; brak docelowej mapy, pełnych statystyk i chat timeline.
- Obecne osobne przyciski/API dispatch i submit, run/config binding, dedup i ochrona unknown outcome są bazą do zachowania. Dopisać jawne rozdzielenie private-test/official; nie traktować samego RUN_MODE=live jako uprawnienia do oficjalnego publikowania.
- Linear: wykorzystany istniejący pusty AmongUsAI w Skymoondev (SKY), teraz Among Agents. Przed tworzeniem nie było issues/milestones/docs; sprawdzono wyszukiwania Among/Halloween/Exorcism/CrewAI/Parasail.
- Publiczne MCP discovery w tym audycie zwróciło server 4.0.7 i 5 narzędzi; to potwierdzenie schematów/opisów, nie runtime test get-tick/submit. get_agent_context zwracało Tool not found; nie założono treści niedostępnych notatek.

## Oficjalny scoring i mapowanie
| Kryterium | Pkt | Implementacja / dowód |
| --- | ---: | --- |
| Containment speed vs baseline | 30 | AA-12 pętla i budżety; AA-14 porównanie czasów; AA-20 tick→scoreboard w finalnym runie |
| False-alarm rate | 20 | AA-07, AA-10, AA-12, AA-14: control oraz warianty wysokiego motion; zero nieuzasadnionych dispatch |
| Civilians saved / escalation correctness | 20 | AA-11–13: zakresy wiedzy, właściwa akcja, właściwy cel, dedup; AA-20 finalna ścieżka |
| Czterej partnerzy użyci autentycznie | 20 | AA-03 Parasail, AA-05 You.com, AA-06–07 One, AA-08/11 CrewAI; AA-13/14 trace wkładu i ablation |
| Code quality & reproducible demo | 10 | AA-00/02/10/18/19: lockfiles, seeded replay, jedno polecenie, evidence pack |

Źródło: [oficjalny przewodnik, §4 i §8](https://youdotcom-oss.github.io/halloween-hack-2026/). Rubryka 100 pkt jest odrębna od wyniku feedu za odpowiedź: poprawna 1, zamiana contain/evacuate 0,5, observe na breach 0; control action daje false alarm. Nie wyświetlać totals feedu jako automatycznie wyliczonego 100/100. Tie-break: najszybszy czysty tick→scoreboard. Dyskwalifikatory: pojedynczy agent udający swarm, odpowiedzi hardcoded, partner tylko jako passthrough.

Aktualizacja organizatorów z 28.10 dopuszcza webhook/manual fallback przy awarii One 401 i traktuje One jako opcjonalne do potwierdzenia działania. Zachować dowód próby i fallbacku; nie obiecywać pełnych 20 punktów za partnerów. W testach fallback może prowadzić WYŁĄCZNIE do potwierdzonego prywatnego celu użytkownika.

## Kontrakt i najważniejsze decyzje
- Zachować tick_id, facility_id, sector_reports[], swarm_budget, escalation_channel oraz civilian_status/containment_state. Nie zakładać jednego sektora. Oficjalne pliki mają envelope {scenario,ticks:[]}; control obejmuje wysoki motion wywołany przez ludzi.
- Bazować na istniejących trzech rolach scout, analyst i commander; odrębny grounded researcher jest opcją dopiero gdy poprawia wynik. Odrębne projekcje danych i narzędzia, wspólny audytowalny czat; zakaz globalnego pełnego kontekstu u każdego agenta. Maksymalna liczba aktywnych agentów pochodzi z bieżącego ticka.
- Scenario MCP: odkryto hack26-list-scenarios, hack26-get-tick, hack26-submit-containment, hack26-get-scoreboard, hack26-ask-oracle. Oracle nie zastępuje You.com.
- get-tick wymaga team+scenario i przesuwa kursor; exhausted:true powtarza ostatni tick. Dostępne scenario według schematu: outbreak-level-5, control-tick. Token tylko jeśli włączony przez organizatorów. Handle 2–32 znaki, regex ^[a-z0-9][a-z0-9-]*$; kolizja współdzieli stan.
- submit wymaga team, dodatniego tick_id, contain|evacuate|observe. Opis schematu deklaruje jedną zaakceptowaną odpowiedź/team/tick i duplicate:true zwracające pierwszą; brak reset tool. Sprawdzić lokalnym fake server; nie zmieniać action przy retry. get-scoreboard przyjmuje {}, filtrować lokalnie.
- Osobny handle próbny NIE jest prywatnym sandboxem. M1 domyślnie discovery/list-scenarios/read scoreboard i fixtures; kontrolowany live get-tick wyłącznie po świadomej aktywacji oraz potwierdzeniu tożsamości/semantyki. Live submit odkładamy do finalnego gate AA-20.
- One: aktualny [event reference](https://hackathon.withone.ai/sf-halloween-2026/skill.md) rozróżnia hosted OAuth i lokalny @withone/mcp stdio. Istniejący ONE_API_KEY mapować w pamięci procesu do ONE_SECRET; nie kopiować wartości do dokumentów. Zweryfikować camelCase local vs snake_case remote i action docs; nie instalować zgadywanego SDK.
- CrewAI guide 1.13.0 i aktualny One reference 1.15.2 różnią się. AA-02 przypina dopiero zgodny, sprawdzony komplet. Python wspierany przez przewodnik: 3.10–3.13. Parasail model wybierany z bieżącej dostępności; sukces /models nie dowodzi inference.
- Stan domeny i outbox w lokalnym Python; official dedup (team,tick_id), private dispatch po stabilnej tożsamości tick/effect/target, run_id tylko metadata; Next.js tylko bezpieczny read model, bez sekretów. SSE można zastąpić pollingiem. Żaden zewnętrzny tekst nie daje agentowi prawa do zmiany trybu/targetu.
- Tryby: offline (fixtures, zero sieci); private-test (prawdziwi partnerzy, allowlist prywatnego Discorda, official submit off); official (jawny finalny opt-in). Tick.escalation_channel nie może ominąć prywatnej polityki.
- Finalny oficjalny Discord, containment submit i formularz to oddzielne efekty. Przygotowanie tego planu nie uruchamia żadnego z nich; testów nigdy nie publikować na oficjalny Discord.

## Kolejność i bramki
M0 → M1 → M2 → M3 → M4. Relacje blockedBy w Linear są źródłem kolejności na poziomie stories.
1. AA-00–02: ochrona sekretów, kontrakt i minimum runtime.
2. AA-03–09: małe próby; równoległe zależności oznaczają możliwość zmiany kolejności przez solo developera, nie dodatkowych wykonawców. Najpierw Parasail i scenario, potem You.com/One/private send, shared chat i submit gate.
3. AA-10–14: fixtures, role, pętla, adaptery, harness. M2 może użyć udokumentowanego fallbacku One lub pending live tick, ale nie nazywa go pełnym PASS integracji.
4. AA-15–17: reprezentacyjny Next.js na prawdziwym read modelu.
5. AA-18–20: failure modes, odtwarzalność, demo i dopiero świadomy finalny run/formularz.

M1 wyniki: PASS_LIVE, PASS_OFFLINE, FALLBACK, BLOCKED/PENDING. Akceptacja fallbacku wymaga dowodu i opisu ograniczenia; nie zmienia testu mock w live. Wszystkie stories startują jako planowane; samo zapisanie planu nie zamyka implementacji.

## Estymaty i plan solo
Konserwatywna estymata walidacji i domknięcia wszystkich stories na istniejącym starterze: **15,5 h** skupionej pracy + nieznany czas oczekiwania na auth/organizatorów. To estymata, nie gwarancja. Native estimate: 1 ≤ 0,5 h; 2 ≤ 1 h; 3 ≤ 1,5 h; opis zawiera dokładne godziny. Priorytety Linear: P1/Urgent=1, P2/High=2, P3/Medium=3 (nazwy P1/P2/P3 oznaczają tu poziomy Linear, nie severity błędu).

Wariant sprintu: timeboxy stories sumują się do **420 min + 60 min bufora = 8 h**, przy minimalnym UI, prostym message bus, polling i bez dodatków. Timebox nie obniża kryteriów bezpieczeństwa/poprawności i nie gwarantuje ukończenia — po jego upływie wybrać opisany fallback albo oznaczyć blokadę. Odkładać animacje, pełną geometrię mapy, zaawansowany czat, tuning wielu modeli, embeddings i deploy. Nie wycinać control tests, współpracy wielu agentów, realnych partnerów ani dowodów.

Przewodnik podaje event **28.10, 09:00–20:30 w San Francisco**, ale NIE dokładny termin zgłoszenia. 20:30 nie jest potwierdzonym deadlinem formularza. Plan powstaje po rozpoczęciu eventu; pełnego 8-godzinnego sprintu nie należy zakładać jako dostępnego czasu. AA-01 natychmiast ustala cutoff; jeśli czasu jest mniej, ograniczyć UI do schematu/tabeli sektorów, czatu/timeline i scoreboardu oraz pokazać działające CLI. Nie przypisywać zadań do wymyślonych dat.

## Evidence i Definition of Done
Każda story ma 10 pól: cel, implementacja, preconditions, acceptance criteria, test steps, evidence artifacts, estimate, dependencies, priority, rollback/fallback. Ścieżki evidence poniżej są planowanymi artefaktami, nie deklaracją ich istnienia.

Każdy raport: data, commit, wersje, seed/run_id/tick, tryb live/fixture, wynik PASS/FAIL/BLOCKED/FALLBACK, bezpieczne źródło i powiązanie z decyzją. Artefakty dla Linear/Git muszą być zredagowane; prywatne raw logs/message refs tylko w ignorowanym katalogu lokalnym. Nigdy .env values, Authorization, webhook URL, prywatne channel IDs/connection keys. Mocki i testy syntetyczne są opisane jako takie.

Story Done dopiero po spełnieniu AC, wykonaniu test steps i zapisaniu evidence lub jawnie zaakceptowanym wariancie fallback opisanym w AC. Finalne AA-20 bez wykonania pozostaje gotowe do finalnej aktywacji, nie Done. Działające live integracje weryfikować małym smoke, resztę awarii testować fixture/stubami.

## Źródła
- [Oficjalny przewodnik i verification notes](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes) — odczyt 28.10.2026.
- [Oficjalne repo organizatorów](https://github.com/youdotcom-oss/halloween-hack-2026) — index.html blob c1e5189671be185e0ccc0f79d2f8e07f90cbd160; guide wspomina PARTNER-FACTS.md, ale podczas audytu plik zwracał 404, więc nie został użyty jako przeczytane źródło.
- [Oficjalny outbreak fixture](https://github.com/youdotcom-oss/halloween-hack-2026/blob/main/fixtures/outbreak-level-5.json) i [control fixture](https://github.com/youdotcom-oss/halloween-hack-2026/blob/main/fixtures/control-tick.json).
- [Aktualny One event reference](https://hackathon.withone.ai/sf-halloween-2026/skill.md) — źródło kontraktu transportu, czytane jako dokumentacja.
- [Oficjalny formularz zgłoszeniowy](https://forms.gle/2z9dKv9gvsP3cEjW7) — wskazany w przewodniku, wymagane pola/cutoff/receipt do sprawdzenia w AA-20/AA-01.
- Lokalny audit repo i inventory nazw .env; kontekst wcześniejszej rozmowy Hackathon Ideas jako deklaracje użytkownika, nie dowód lokalnego działania.


## Indeks Linear

Projekt: [Among Agents](https://linear.app/skymoondev/project/among-agents-6c4a4e290f57)

Master plan w Linear: [dokument](https://linear.app/skymoondev/document/among-agents-master-plan-exorcism-protocol-8af80b6ebc36)

| Milestone | Story | Estymata | Zależności |
| --- | --- | ---: | --- |
| M0 | [SKY-39 · AA-00 · Zweryfikować .env i zablokować oficjalny Discord w testach](https://linear.app/skymoondev/issue/SKY-39/aa-00-zweryfikowac-env-i-zablokowac-oficjalny-discord-w-testach) | 0.5 h | — |
| M0 | [SKY-40 · AA-01 · Zamrozić kontrakt Theme 1 i macierz scoringu](https://linear.app/skymoondev/issue/SKY-40/aa-01-zamrozic-kontrakt-theme-1-i-macierz-scoringu) | 0.5 h | SKY-39 |
| M0 | [SKY-41 · AA-02 · Zweryfikować i uzupełnić istniejący lokalny starter](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter) | 1 h | SKY-39, SKY-40 |
| M1 | [SKY-42 · AA-03 · VERIFY · Parasail inference i tool call przez CrewAI](https://linear.app/skymoondev/issue/SKY-42/aa-03-verify-parasail-inference-i-tool-call-przez-crewai) | 0.5 h | SKY-41 |
| M1 | [SKY-43 · AA-04 · VERIFY · Scenario MCP discovery, kontrakt i kontrolowany tick](https://linear.app/skymoondev/issue/SKY-43/aa-04-verify-scenario-mcp-discovery-kontrakt-i-kontrolowany-tick) | 0.5 h | SKY-41 |
| M1 | [SKY-44 · AA-05 · VERIFY · You.com Search + grounding wpływający na decyzję](https://linear.app/skymoondev/issue/SKY-44/aa-05-verify-youcom-search-grounding-wplywajacy-na-decyzje) | 0.5 h | SKY-41 |
| M1 | [SKY-45 · AA-06 · VERIFY · WithOne transport, integrations i action discovery](https://linear.app/skymoondev/issue/SKY-45/aa-06-verify-withone-transport-integrations-i-action-discovery) | 0.5 h | SKY-41 |
| M1 | [SKY-46 · AA-07 · VERIFY · Runtime action i wiadomość na prywatny Discord](https://linear.app/skymoondev/issue/SKY-46/aa-07-verify-runtime-action-i-wiadomosc-na-prywatny-discord) | 0.5 h | SKY-45, SKY-42 |
| M1 | [SKY-47 · AA-08 · VERIFY · CrewAI shared chat i częściowe obserwacje](https://linear.app/skymoondev/issue/SKY-47/aa-08-verify-crewai-shared-chat-i-czesciowe-obserwacje) | 0.75 h | SKY-42, SKY-43 |
| M1 | [SKY-48 · AA-09 · VERIFY · Bezpieczny submission contract i odczyt scoreboard](https://linear.app/skymoondev/issue/SKY-48/aa-09-verify-bezpieczny-submission-contract-i-odczyt-scoreboard) | 0.5 h | SKY-43 |
| M2 | [SKY-49 · AA-10 · Uzupełnić kontrakty, oficjalne fixtures i deterministyczny replay](https://linear.app/skymoondev/issue/SKY-49/aa-10-uzupelnic-kontrakty-oficjalne-fixtures-i-deterministyczny-replay) | 0.75 h | SKY-42, SKY-43, SKY-44, SKY-46, SKY-47, SKY-48 |
| M2 | [SKY-50 · AA-11 · Role agentów, scoped context i wspólny dziennik](https://linear.app/skymoondev/issue/SKY-50/aa-11-role-agentow-scoped-context-i-wspolny-dziennik) | 0.75 h | SKY-49 |
| M2 | [SKY-51 · AA-12 · Pętla supervisora: decyzja, budżety i ochrona przed false alarms](https://linear.app/skymoondev/issue/SKY-51/aa-12-petla-supervisora-decyzja-budzety-i-ochrona-przed-false-alarms) | 1.5 h | SKY-50 |
| M2 | [SKY-52 · AA-13 · Adaptery E2E, prywatna eskalacja i trwały outbox](https://linear.app/skymoondev/issue/SKY-52/aa-13-adaptery-e2e-prywatna-eskalacja-i-trwaly-outbox) | 1 h | SKY-51 |
| M2 | [SKY-53 · AA-14 · Harness jakości, latency i dowodów scoringu](https://linear.app/skymoondev/issue/SKY-53/aa-14-harness-jakosci-latency-i-dowodow-scoringu) | 0.75 h | SKY-52 |
| M3 | [SKY-54 · AA-15 · Lokalny read model/API dla Next.js](https://linear.app/skymoondev/issue/SKY-54/aa-15-lokalny-read-modelapi-dla-nextjs) | 0.75 h | SKY-53 |
| M3 | [SKY-55 · AA-16 · Mapa obiektu i statystyki agentów w Next.js](https://linear.app/skymoondev/issue/SKY-55/aa-16-mapa-obiektu-i-statystyki-agentow-w-nextjs) | 1 h | SKY-54 |
| M3 | [SKY-56 · AA-17 · Shared chat, timeline decyzji i prawdziwy scoreboard](https://linear.app/skymoondev/issue/SKY-56/aa-17-shared-chat-timeline-decyzji-i-prawdziwy-scoreboard) | 0.75 h | SKY-55 |
| M4 | [SKY-57 · AA-18 · Hardening: timeout, retry, restart, privacy i budżety](https://linear.app/skymoondev/issue/SKY-57/aa-18-hardening-timeout-retry-restart-privacy-i-budzety) | 1 h | SKY-56 |
| M4 | [SKY-58 · AA-19 · Jedno polecenie, evidence pack i 3-minutowe demo](https://linear.app/skymoondev/issue/SKY-58/aa-19-jedno-polecenie-evidence-pack-i-3-minutowe-demo) | 1 h | SKY-57 |
| M4 | [SKY-59 · AA-20 · Finalny gate: oficjalny run, scoreboard i formularz](https://linear.app/skymoondev/issue/SKY-59/aa-20-finalny-gate-oficjalny-run-scoreboard-i-formularz) | 0.5 h | SKY-58 |

## 0 · Audit repo/env + spec
Punkt wejścia do istniejącego startera. AA-00–02: ochrona env i prywatnego Discorda, spec/scoring oraz weryfikacja lokalnego setup. Gate: doctor offline, brak oficjalnego fallbacku w testach, potwierdzony kontrakt i bezpieczne konfiguracje. Nie tworzyć drugiego scaffolda.

Linear: [SKY-39](https://linear.app/skymoondev/issue/SKY-39/aa-00-zweryfikowac-env-i-zablokowac-oficjalny-discord-w-testach)

## AA-00 · Zweryfikować .env i zablokować oficjalny Discord w testach

**Milestone:** M0
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 10 min.
**Dependency:** brak.
**Priority:** 1 — Urgent.

### Stan w repo
Istnieją ignore/template/doctor; brak WORKER_TOKEN i ochrony prywatnego targetu. Oficjalny default musi zostać usunięty przed send.

### Cel
Zabezpieczyć aktualny starter i doprowadzić politykę testów Discord do wymogu użytkownika przed pierwszą live wysyłką.

### Implementacja
Zachować istniejące .gitignore/.env.example i sprawdzić ich kompletność; ignorować prywatne raw logs/evidence. Użyć istniejącego doctor do inventory nazw/statusów bez sieci. W config.py, template i README usunąć oficjalny kanał jako fallback dla testów; brak potwierdzonego prywatnego celu ma blokować send. Wprowadzić allowlistę/tryb testowy bez kopiowania wartości .env do dokumentów. Dodać lokalny WORKER_TOKEN (min. 24 znaki) generowany bez wypisywania; nie zmieniać pozostałych wartości na podstawie domysłów. Nie dodawać sekretów do NEXT_PUBLIC_*.

### Preconditions
Końcowy audyt: .env jest już ignorowany, .env.example i doctor istnieją. Sześć nazw ustawionych, WORKER_TOKEN brak. config.py/README/template zawierają oficjalny fallback Discord, a prywatna tożsamość aktualnego DISCORD_CHANNEL_ID nie została potwierdzona.

### Acceptance criteria
git check-ignore potwierdza ochronę .env; git ls-files nie obejmuje sekretów; .env.example zawiera puste klucze i bezpieczne niesekretne defaults/opisy, bez oficjalnego targetu dla testów. Raport nie pokazuje wartości, długości ani hashy sekretów. Brak kluczy w NEXT_PUBLIC_*. Oficjalny default usunięty z ścieżki testowej; niezweryfikowany/nieprywatny kanał blokowany przed requestem. WORKER_TOKEN przechowywany wyłącznie lokalnie, bez wartości w logach/Linear. README opisuje prywatne testy i odrębny finalny tryb.

### Test steps
1. Uruchom istniejący lokalny doctor bez sieci; sprawdź tylko nazwy/status, brak wartości.
2. Sprawdź ignorowanie i listę śledzonych plików; nie używaj git add .
3. Na syntetycznym pliku sprawdź brakujące/puste ustawienie oraz redakcję nagłówków i webhooka.
4. Negatywny test: brak targetu, oficjalny target i niepotwierdzony target → zero requestów Discord; prywatny potwierdzony cel dopiero w AA-07.

### Evidence artifacts
- docs/config-audit.md
- docs/configuration.md
- .env.example
- evidence/AA-00/doctor-redacted.txt

### Rollback / fallback
Nie zmieniaj .env. Przy wykryciu śledzonego sekretu zatrzymaj commit i obsłuż konkretny wyciek; odtwórz tylko poprzednią konfigurację loadera.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-40](https://linear.app/skymoondev/issue/SKY-40/aa-01-zamrozic-kontrakt-theme-1-i-macierz-scoringu)

## AA-01 · Zamrozić kontrakt Theme 1 i macierz scoringu

**Milestone:** M0
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 10 min.
**Dependency:** [SKY-39 · AA-00](https://linear.app/skymoondev/issue/SKY-39/aa-00-zweryfikowac-env-i-zablokowac-oficjalny-discord-w-testach).
**Priority:** 1 — Urgent.

### Stan w repo
README i docs/VERIFICATION.md zawierają źródła; skonsolidować z master planem i wymaganiami prywatnych testów.

### Cel
Pracować według aktualnych zasad Theme 1, z mapowaniem każdego punktowanego wymagania na implementację i dowód.

### Implementacja
Zapisać źródła i datę w docs/spec.md: 30 speed, 20 false alarms, 20 civilians/escalation, 20 autentyczne użycie partnerów, 10 reproducibility. Rozdzielić wynik 0–1 z feedu od pełnej oceny 100 pkt. Zapisać fixed fields, action enum, budżety, prywatną politykę Discord i osobną ścieżkę finalnego zgłoszenia. Udokumentować rozbieżność przewodnik/aktualny skill One i wersje do sprawdzenia.

### Preconditions
AA-00; oficjalny przewodnik i schematy discovery. Użytkownik deklarował wcześniejszą próbę Parasail→CrewAI, ale w repo brak dowodów.

### Acceptance criteria
Każda pozycja rubryki ma story i artefakt; wymienione dyskwalifikatory: pojedynczy agent, hardcoded odpowiedzi, partner passthrough. Otwarte kwestie mają właściciela/gate: tożsamość prywatnego kanału, model/billing, token scenariusza jeśli wymagany, termin formularza. Nie ma wymyślonych URL ani gwarancji pełnej punktacji za fallback One.

### Test steps
1. Porównaj spec z §4, §8, §10–11 i aktualnym event skill One.
2. Sprawdź pola sector_reports, civilian_status, containment_state oraz obsługę wielu sektorów.
3. Sprawdź, że formularz, scoreboard i Discord to odrębne efekty; ustal termin z organizatorami zamiast go wymyślać.

### Evidence artifacts
- docs/spec.md
- docs/scoring-matrix.md
- docs/decisions.md

### Rollback / fallback
Przy rozbieżnościach zachowaj datowane źródła; zablokuj tylko zależny efekt zewnętrzny. Nie dodawaj AWS/deploymentu ani osobnego Track 2.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-41](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter)

## AA-02 · Zweryfikować i uzupełnić istniejący lokalny starter

**Milestone:** M0
**Estymata:** 1 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-39 · AA-00](https://linear.app/skymoondev/issue/SKY-39/aa-00-zweryfikowac-env-i-zablokowac-oficjalny-discord-w-testach), [SKY-40 · AA-01](https://linear.app/skymoondev/issue/SKY-40/aa-01-zamrozic-kontrakt-theme-1-i-macierz-scoringu).
**Priority:** 2 — High.

### Stan w repo
app/, lib/, worker/, scripts/, fixtures/, lockfiles i 25 testów istnieją w working tree; wyniki repo są zapisane, nie ponownie wykonane w tym audycie.

### Cel
Potwierdzić odtwarzalny setup istniejącego Next.js/FastAPI/CrewAI, bez tworzenia drugiej struktury projektu.

### Implementacja
Zachować app/, lib/, worker/among_agents/, fixtures/, tests/ oraz scripts/setup.mjs, dev.mjs i doctor.mjs. Sprawdzić package-lock.json, worker/uv.lock, .nvmrc i .python-version oraz zgodny zestaw CrewAI/MCP; przypiąć wyłącznie faktycznie sprawdzony komplet. Uzupełnić brakujące doctor/verify/replay, nie odtwarzać apps/web ani services/orchestrator. Domyślnie demo/offline, zapisy zewnętrzne wyłączone; env jako dane. Zachować sprzątanie subprocess.

### Preconditions
AA-00–01. W working tree istnieją starter i zapisane wyniki setup/test/build w docs/VERIFICATION.md; wymagana powtórka/rejestr evidence, nie ponowne scaffoldowanie.

### Acceptance criteria
Czysta instalacja startuje health page i Python doctor; tryb offline nie wysyła żadnych requestów. Zamknięcie procesu sprząta MCP subprocess. Jest jedna instrukcja uruchomienia; brak kluczy po stronie Next.js client.

### Test steps
1. Zainstaluj z lockfiles i uruchom doctor oraz minimalny lokalny start.
2. Uruchom bez .env w offline: czytelny komunikat, bez crashu/wycieku.
3. Przerwij i ponów start; sprawdź brak wiszących procesów/portów.

### Evidence artifacts
- lockfiles
- scripts/verify entrypoint
- evidence/AA-02/bootstrap.txt
- README.md

### Rollback / fallback
Utrzymaj CLI Python jako główną ścieżkę, jeśli Next.js blokuje setup; odłóż UI do M3. Nie odtwarzaj wersji z pamięci.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

## 1 · Verification stories
Po M0, przed dużymi funkcjami. AA-03–09 potwierdzają Parasail przez CrewAI, scenario MCP, You.com, WithOne i prywatny Discord, wspólny czat/częściowe obserwacje oraz bezpieczny kontrakt zgłoszenia. Gate: PASS albo jawny, zweryfikowany fallback; mock nigdy nie potwierdza integracji live. Brak testów na oficjalnym Discordzie.

Linear: [SKY-42](https://linear.app/skymoondev/issue/SKY-42/aa-03-verify-parasail-inference-i-tool-call-przez-crewai)

## AA-03 · VERIFY · Parasail inference i tool call przez CrewAI

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-41 · AA-02](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter).
**Priority:** 1 — Urgent.

### Stan w repo
crew.py buduje realne CrewAI Agent/Task/Crew/LLM z Parasail providerem. Testy konstrukcji nie wykonują live inference.

### Cel
Udowodnić rzeczywistą inferencję Parasail wykonaną przez CrewAI, wraz z narzędziem i kontrolą czasu/kosztu.

### Implementacja
Z aktualnej listy modeli wybierz dostępny model o niskiej latencji wspierający wymagany tool calling. Uruchom małego agenta CrewAI z lokalnym deterministycznym narzędziem i strukturalną odpowiedzią. Zapisać użyty model/SDK, pomiary i zredagowane request metadata; model/base URL z udokumentowanego źródła, nie z domysłu.

### Preconditions
AA-02; PARASAIL_API_KEY obecny; aktywne konto/billing/model wymagają testu. Wcześniejsza deklaracja użytkownika jest wskazówką, nie lokalnym PASS.

### Acceptance criteria
Co najmniej 3 małe wywołania: realna odpowiedź, jedno rzeczywiste wywołanie narzędzia przez CrewAI, poprawny wynik strukturalny. Zapisane latencje/tokeny jeśli API je zwraca; żaden cichy fallback do innego dostawcy. Models list sama nie wystarcza.

### Test steps
1. Uruchom inference przez CrewAI na syntetycznym, nieoficjalnym prompt.
2. Zweryfikuj trace narzędzia, parsowanie i provider metadata.
3. Zasymuluj 401/429/timeout; sprawdź limit ponowień i brak sekretów w błędzie.

### Evidence artifacts
- evidence/AA-03/parasail-crewai.json
- tests/integration/test_parasail_crewai.py
- docs/verification.md

### Rollback / fallback
Raz zmień model na rzeczywiście dostępny szybszy model i zapisz powód. Brak billing/auth oznacza BLOCKED; mock pozwala rozwijać offline, ale nie zalicza integracji.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-43](https://linear.app/skymoondev/issue/SKY-43/aa-04-verify-scenario-mcp-discovery-kontrakt-i-kontrolowany-tick)

## AA-04 · VERIFY · Scenario MCP discovery, kontrakt i kontrolowany tick

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-41 · AA-02](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter).
**Priority:** 1 — Urgent.

### Stan w repo
integrations.py wysyła team+scenario+[token]; doctor discovery nie pobiera ticka. Użyć istniejącego adaptera.

### Cel
Potwierdzić narzędzia oficjalnego feedu i poprawny odczyt ticka bez zużywania właściwego przebiegu konkursowego.

### Implementacja
Zweryfikować lokalny SCENARIO_MCP z oficjalnym źródłem; sprawdzić istniejący klient w worker/among_agents/integrations.py; jeżeli używany wrapper CrewAI, jawny MCPServerHTTP streamable zamiast shorthand URL. Zrzut tools/list i inputSchema, lista scenariuszy. Tick wymaga team oraz scenario; get-tick przesuwa kursor. Osobny, unikalny handle próbny po sprawdzeniu zasad izolacji, nigdy domyślny konkursowy TEAM_HANDLE. Bez submit i bez Discord.

### Preconditions
AA-02; dostępny serwer; token wyłącznie jeśli discovery/organizator go wymaga. Schemat z audytu planu nie zastępuje testu przez lokalny CrewAI. Brak bezpiecznego handle próbnego blokuje live get-tick. Handle próbny nie zapewnia prywatnego scoreboardu; potrzebna świadoma aktywacja testowego get-tick i potwierdzenie semantyki kursora. Bez niej korzystamy z fixture.

### Acceptance criteria
Discovery pokazuje wymagane get-tick/submit/get-scoreboard, zapisuje też pozostałe narzędzia bez uruchamiania ich. Walidacja oficjalnych fixtures (w tym control, wiele sektorów, exhausted) PASS. Dopuszczone zamknięcie gate: DISCOVERY_PASS + FIXTURE_PASS + LIVE_TICK_PENDING, jawnie odroczone do AA-20; to pozwala odblokować M2, nie jest potwierdzeniem działania live ticka. Opcjonalny kontrolowany tick próbny tylko po świadomej aktywacji; zero submit i zero zmiany konkursowego kursora. UI nie nazywa get-tick read-only.

### Test steps
1. Odczytaj schematy i porównaj transport/auth; nie zakładaj dokładnie trzech narzędzi.
2. Waliduj fixtures offline, potem pojedynczy get-tick tylko dla potwierdzonego handle próbnego.
3. Sprawdź wielosektorowy payload, limit agentów, błąd scenariusza i exhausted; zapisuj jako replay, nie pobieraj w pętli.

### Evidence artifacts
- evidence/AA-04/mcp-tools-redacted.json
- evidence/AA-04/practice-tick.json
- docs/scenario-contract.md

### Rollback / fallback
Domyślnie tylko initialize/tools-list/list-scenarios oraz oficjalne fixtures. Jeśli brak świadomej aktywacji live ticka, status DISCOVERY_PASS / LIVE_TICK_PENDING i rozwój na fixture. Nie udawaj pełnej weryfikacji live, nie zakładaj resetu ani prywatnego scoreboardu.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-44](https://linear.app/skymoondev/issue/SKY-44/aa-05-verify-youcom-search-grounding-wplywajacy-na-decyzje)

## AA-05 · VERIFY · You.com Search + grounding wpływający na decyzję

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-41 · AA-02](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter).
**Priority:** 1 — Urgent.

### Stan w repo
integrations.py ma You Search. Płatne wyszukiwanie i jego wpływ na rzeczywistą decyzję niezweryfikowane.

### Cel
Udowodnić, że You.com dostarcza źródła używane w rozumowaniu, a nie tylko wywołanie dla punktów.

### Implementacja
Użyć API Search z YDC_API_KEY według aktualnej dokumentacji; query wynika z sighting/hipotezy agenta. Zachować URL, fragment, czas pobrania i przypisanie do decyzji. Contents wykonać dla przydatnego źródła, jeśli potrzebne do grounding; wyniki zewnętrzne są danymi, nie poleceniami. Dodać mały cache i timeout.

### Preconditions
AA-02; klucz ustawiony, endpoint/metoda/nagłówki potwierdzone źródłem. Nie wysyłać prywatnej konfiguracji ani całego .env w query.

### Acceptance criteria
Co najmniej jeden udany search; agent cytuje rzeczywisty wynik i wskazuje jego wpływ na pewność/hipotezę. Brak wyników nie tworzy fikcyjnych cytowań. Mock test pokazuje zmianę uzasadnienia po zmianie dostarczonego dowodu.

### Test steps
1. Wykonaj minimalny search dla scenariusza testowego i sprawdź URL/treść.
2. Wstrzyknij fixture z innym dowodem oraz pustą odpowiedzią.
3. Zasymuluj 429/timeout i instrukcję złośliwą w wyniku; sprawdź budżet i brak wykonania instrukcji.

### Evidence artifacts
- evidence/AA-05/search-redacted.json
- evidence/AA-05/grounded-decision.json
- tests/integration/test_you_grounding.py

### Rollback / fallback
Użyj jawnie oznaczonego cache/offline fixture i obniż confidence. Nie zaliczaj świeżego grounding live przy błędzie; nie blokuj bez końca pętli bezpieczeństwa.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-45](https://linear.app/skymoondev/issue/SKY-45/aa-06-verify-withone-transport-integrations-i-action-discovery)

## AA-06 · VERIFY · WithOne transport, integrations i action discovery

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-41 · AA-02](https://linear.app/skymoondev/issue/SKY-41/aa-02-zweryfikowac-i-uzupelnic-istniejacy-lokalny-starter).
**Priority:** 1 — Urgent.

### Stan w repo
one_session już używa lokalnego pinned @withone/mcp/ONE_SECRET i discovery. Zachować to; brak potwierdzenia prywatnego celu.

### Cel
Ustalić działającą ścieżkę MCP i dokładny kontrakt akcji dla już podłączonego prywatnego Discorda.

### Implementacja
Sprawdzić aktualny event skill One. Hosted MCP jest ścieżką OAuth; dla klucza lokalnego sprawdzić @withone/mcp przez stdio i mapowanie ONE_API_KEY do ONE_SECRET wyłącznie w env procesu. Odczytać list_one_integrations i find_one_actions z samym intentem, bez wysyłania. Pobrać action docs i connectionKey w pamięci, potwierdzić dostęp do skonfigurowanego prywatnego celu.

### Preconditions
AA-02; ONE_API_KEY i DISCORD_CHANNEL_ID ustawione; prywatny Discord według użytkownika jest połączony. Wartości i tożsamość nadal do lokalnej walidacji.

### Acceptance criteria
Udokumentowany transport/auth i rzeczywiste nazwy narzędzi. Wskazana właściwa integracja oraz schemat send; local execute camelCase vs remote snake_case sprawdzone przez discovery. Kanał potwierdzony jako dozwolony prywatny, identyfikatory nie trafiają do Linear. Brak wiadomości podczas discovery. Alternatywne zamknięcie gate przy awarii One: udokumentowany FAIL/FALLBACK One, sprawdzone oficjalne źródło ścieżki awarii i niezależnie zweryfikowany prywatny fallback/target z istniejących ustawień lub od właściciela. Brak dowodu prywatnego celu nadal blokuje AA-07; fallback nie zalicza One jako PASS.

### Test steps
1. Uruchom MCP i list integrations.
2. Wyszukaj intent send a message to a channel, odczytaj docs i wymagane path variables.
3. Zbuduj payload preview lokalnie; zweryfikuj requestConfig.url/target, tokeny i identyfikatory zredaguj w evidence.

### Evidence artifacts
- evidence/AA-06/discovery-redacted.json
- docs/withone-contract.md
- tests/integration/test_one_discovery.py

### Rollback / fallback
Nie przekazuj API key jako bearer do OAuth endpointu. Jeśli discovery/auth niedostępne, zapisz błąd, wybierz dozwolony prywatny fallback w AA-07 i zakończ timebox; nie instaluj zgadywanego SDK.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-46](https://linear.app/skymoondev/issue/SKY-46/aa-07-verify-runtime-action-i-wiadomosc-na-prywatny-discord)

## AA-07 · VERIFY · Runtime action i wiadomość na prywatny Discord

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-45 · AA-06](https://linear.app/skymoondev/issue/SKY-45/aa-06-verify-withone-transport-integrations-i-action-discovery), [SKY-42 · AA-03](https://linear.app/skymoondev/issue/SKY-42/aa-03-verify-parasail-inference-i-tool-call-przez-crewai).
**Priority:** 1 — Urgent.

### Stan w repo
Dispatch API/UI i ochrona unknown outcome istnieją. Brak potwierdzonego live send i private-channel identity/allowlist.

### Cel
Potwierdzić rzeczywisty efekt akcji wynikający z runtime state, wyłącznie w prywatnym kanale testowym.

### Implementacja
Zsyntetyzować dwa ticki: alarm i control. CrewAI generuje uzasadnienie; adapter allowlistuje prywatny DISCORD_CHANNEL_ID i ignoruje docelowy kanał z tick payload w trybie test. Payload preview przed jednym kontrolowanym send, correlation_id i trwały dedup. Powrót One sprawdzić pod kątem faktycznej platformy/akcji i błędu; nie uznawać samego HTTP 200 za sukces.

### Preconditions
AA-03 działa. AA-06 zakończone PASS discovery albo jawne FALLBACK One. Przed wysyłką zawsze potwierdzony prywatny kanał i właściwy kontrakt transportu; przy fallbacku można potwierdzić cel niezależnie od One z dostępnej konfiguracji/od właściciela. Jeśli prywatny cel nie daje się ustalić, zatrzymaj send i poproś właściciela o wskazanie; nie podstawiaj oficjalnego kanału.

### Acceptance criteria
Jedna wiadomość alarmowa widoczna w prywatnym kanale, message id/permalink przechowane prywatnie; control i replay nie wysyłają nic. Negatywny test oficjalnego/nieznanego targetu blokuje przed requestem. Wynik rozróżnia PASS One od FALLBACK private, z udokumentowanym wpływem na dowody partnera. Dopuszczone zamknięcie: FALLBACK_PRIVATE_VERIFIED z prawdziwą prywatną wiadomością i testami control/dedup; zachować osobny One_FAIL, nie twierdzić, że One send działa.

### Test steps
1. Zrób dry-run oraz negatywny test allowlisty.
2. Wyślij jeden oznaczony test z runtime rationale; potwierdź widoczność i correlation_id.
3. Powtórz ten sam event oraz control; sprawdź zero dodatkowych wiadomości. Przy 401 sprawdź requestConfig.url i najwyżej raz ostrożnie ponów.

### Evidence artifacts
- evidence/AA-07/dispatch-redacted.json
- prywatny manifest message reference
- tests/integration/test_private_dispatch.py

### Rollback / fallback
Po limicie prób One przejdź tylko na potwierdzony prywatny webhook lub ręczny post w prywatnym kanale. Gdy brak prywatnego fallbacku, BLOCKED send; nigdy nie używaj webhooka z przewodnika organizatorów.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-47](https://linear.app/skymoondev/issue/SKY-47/aa-08-verify-crewai-shared-chat-i-czesciowe-obserwacje)

## AA-08 · VERIFY · CrewAI shared chat i częściowe obserwacje

**Milestone:** M1
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 20 min.
**Dependency:** [SKY-42 · AA-03](https://linear.app/skymoondev/issue/SKY-42/aa-03-verify-parasail-inference-i-tool-call-przez-crewai), [SKY-43 · AA-04](https://linear.app/skymoondev/issue/SKY-43/aa-04-verify-scenario-mcp-discovery-kontrakt-i-kontrolowany-tick).
**Priority:** 1 — Urgent.

### Stan w repo
Scouting ma sensor-only input, analyst civilian/containment input, commander kontekst wyników. Brak trwałego chat bus i prompt-level evidence z prawdziwego runu.

### Cel
Pokazać realną współpracę wielu agentów, zanim powstanie pełny swarm.

### Implementacja
Minimalny spike: sensor scout i civilian analyst otrzymują różne projekcje tego samego fixture; supervisor zbiera ich wiadomości w wspólnym logu. Schemat wiadomości: run_id, tick_id, agent, observation_ref, confidence, rationale, time. Nie przekazywać pełnego ticka każdemu agentowi przez globalny prompt/history.

### Preconditions
AA-03; AA-04 dostarczył kontrakt lub oficjalne fixtures offline. Co najmniej dwa aktywne agenty robocze i supervisor w ramach budżetu.

### Acceptance criteria
Trace pokazuje odrębne wejścia i wymianę wiadomości. Decyzja supervisora wykorzystuje dwa niezależne wkłady; withheld fact nie występuje u niewłaściwego agenta przed udostępnieniem w czacie. Brak jednego agenta odgrywającego wszystkie role. Test znacznika obejmuje także pamięć/kontekst drugiego ticka.

### Test steps
1. Na seed fixture ukryj civilian_status przed scoutem, sensory przed analystą.
2. Sprawdź wejścia agentów i kolejność ujawniania faktów w logu.
3. Zmień tylko jedną obserwację; sprawdź wpływ na syntezę. Zasymuluj brak jednego agenta i ograniczony budżet.

### Evidence artifacts
- evidence/AA-08/agent-inputs-redacted.json
- evidence/AA-08/shared-chat.jsonl
- tests/test_partial_observations.py

### Rollback / fallback
Jeśli memory API komplikuje test, użyj jawnego append-only message bus w procesie Python i kontrolowanych projekcji. Nie zastępuj współpracy jednym LLM.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-48](https://linear.app/skymoondev/issue/SKY-48/aa-09-verify-bezpieczny-submission-contract-i-odczyt-scoreboard)

## AA-09 · VERIFY · Bezpieczny submission contract i odczyt scoreboard

**Milestone:** M1
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-43 · AA-04](https://linear.app/skymoondev/issue/SKY-43/aa-04-verify-scenario-mcp-discovery-kontrakt-i-kontrolowany-tick).
**Priority:** 1 — Urgent.

### Stan w repo
Submit API jest osobną akcją; schema team/tick/action+[token], scoreboard {} już są. Brak explicit official opt-in oraz live judgment evidence.

### Cel
Potwierdzić gotowość oficjalnego protokołu bez przypadkowego zapisania testu w konkursowym wyniku.

### Implementacja
Z discovery przypiąć schema submit/get-scoreboard i reguły team+tick+action. Tryby offline, private-test, official: submit domyślnie disabled; read scoreboard osobnym adapterem. Local fake server sprawdza poprawne akcje contain/evacuate/observe, dedup, timeout i niejednoznaczny wynik. Discovery opisuje jedną odpowiedź/tick/team i duplicate:true, bez resetu; runtime zweryfikować dopiero świadomie.

### Preconditions
AA-04; znany kontrakt oraz unikalność TEAM_HANDLE do potwierdzenia. Oficjalny kanał i live submit nie są objęte tą weryfikacją.

### Acceptance criteria
Read-only scoreboard parsuje się lub ma jawny status niedostępny; test spy potwierdza zero live submit. Payload preview walidowany; retry zachowuje dokładnie ten sam tick/action i correlation. Stan lokalny nie jest prezentowany jako oficjalna punktacja. Próba submit w private-test/offline blokowana przed siecią. Przy niedostępnym feedzie gate może zamknąć CONTRACT_PASS + SCOREBOARD_LIVE_PENDING z fixture testem; rzeczywisty live check pozostaje w AA-20.

### Test steps
1. Odczytaj scoreboard bez get-tick/submit.
2. Uruchom contract tests z fake MCP: success, duplicate, malformed, timeout po potencjalnym przyjęciu.
3. Sprawdź disabled flag, rozbieżność handle oraz niepoprawną akcję. Finalny live write pozostaw AA-20.

### Evidence artifacts
- evidence/AA-09/scoreboard-read-redacted.json
- tests/contracts/test_submission.py
- docs/official-run-gate.md

### Rollback / fallback
Przy braku feedu wykorzystaj oznaczony fixture scoreboard. Nie zgaduj resetu ani nie testuj poprawiania odpowiedzi drugim submit; odkładaj do outbox bez automatycznego wysyłania.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

## 2 · Core end-to-end swarm + fixtures
Po M1. AA-10–14: kontrakty i oficjalne fixtures, role z częściową wiedzą, supervisor, rzeczywiste adaptery i harness. Gate: autonomiczne E2E na outbreak/control, brak false alarm na control, przestrzegany swarm_budget i gotowe dowody partnerów. Wyniki lokalne oddzielone od oficjalnych.

Linear: [SKY-49](https://linear.app/skymoondev/issue/SKY-49/aa-10-uzupelnic-kontrakty-oficjalne-fixtures-i-deterministyczny-replay)

## AA-10 · Uzupełnić kontrakty, oficjalne fixtures i deterministyczny replay

**Milestone:** M2
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 20 min.
**Dependency:** [SKY-42 · AA-03](https://linear.app/skymoondev/issue/SKY-42/aa-03-verify-parasail-inference-i-tool-call-przez-crewai), [SKY-43 · AA-04](https://linear.app/skymoondev/issue/SKY-43/aa-04-verify-scenario-mcp-discovery-kontrakt-i-kontrolowany-tick), [SKY-44 · AA-05](https://linear.app/skymoondev/issue/SKY-44/aa-05-verify-youcom-search-grounding-wplywajacy-na-decyzje), [SKY-46 · AA-07](https://linear.app/skymoondev/issue/SKY-46/aa-07-verify-runtime-action-i-wiadomosc-na-prywatny-discord), [SKY-47 · AA-08](https://linear.app/skymoondev/issue/SKY-47/aa-08-verify-crewai-shared-chat-i-czesciowe-obserwacje), [SKY-48 · AA-09](https://linear.app/skymoondev/issue/SKY-48/aa-09-verify-bezpieczny-submission-contract-i-odczyt-scoreboard).
**Priority:** 2 — High.

### Stan w repo
models.py, root fixtures i testy wszystkich sektorów/control już istnieją; rozszerzyć replay/provenance i warianty.

### Cel
Mieć wspólne dane i powtarzalne testy całej pętli przed rozbudową agentów.

### Implementacja
Rozszerzyć worker/among_agents/models.py i istniejące fixtures/outbreak-level-5.json oraz control-tick.json; nie kopiować drugiego zbioru do nowego drzewa. Modele Tick/Sector/Observation/ChatMessage/Decision/Dispatch/Judgment; decyzje tylko contain|evacuate|observe. Loader oficjalnych envelopes {scenario,ticks:[]} i pojedynczego live ticka; provenance i wersja fixture. Repo przechowuje oficjalny outbreak/control i pochodne testowe: brak danych, wiele sektorów, kontrola z wysokim motion, niski budżet, exhausted. Fake MCP/adapters nie wysyłają sieci.

### Preconditions
M1 ma evidence i rozstrzygnięte fallbacki. Dopuszczony brak live ticka przy potwierdzonym kontrakcie/fixtures; brak realnego Parasail/You.com pozostaje jawną blokadą trybu live.

### Acceptance criteria
Replay z tym samym seed daje te same wejścia i kolejność zdarzeń; walidacja odrzuca błędny kontrakt. Oficjalne fixtures zachowują pola/ID, aplikacja nie wybiera odpowiedzi przez tick_id. Każde dane mają etykietę live/fixture/synthetic.

### Test steps
1. Odtwórz wszystkie ticki outbreak oraz control; zweryfikuj envelope i wiele sektorów.
2. Podaj malformed/null/missing fields i exhausted; sprawdź kontrolowane zachowanie.
3. Przemieszaj ID i sektory bez zmiany treści; decyzja nie może zależeć od identyfikatora.

### Evidence artifacts
- tests/fixtures/README.md
- fixtures/ + provenance
- tests/test_contracts.py
- evidence/AA-10/replay.jsonl

### Rollback / fallback
Przy zmianie kontraktu zachowaj poprzedni snapshot i osobny adapter. Nie modyfikuj oryginalnych fixtures w celu poprawy wyniku.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-50](https://linear.app/skymoondev/issue/SKY-50/aa-11-role-agentow-scoped-context-i-wspolny-dziennik)

## AA-11 · Role agentów, scoped context i wspólny dziennik

**Milestone:** M2
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-49 · AA-10](https://linear.app/skymoondev/issue/SKY-49/aa-10-uzupelnic-kontrakty-oficjalne-fixtures-i-deterministyczny-replay).
**Priority:** 2 — High.

### Stan w repo
3 role i częściowe wejścia już istnieją; brakuje wspólnego protokołu czatu/timeline i dowodów izolacji między tickami.

### Cel
Zbudować rzeczywisty supervised swarm z odrębną wiedzą, narzędziami i wkładem do decyzji.

### Implementacja
Rozszerzyć istniejące scout/analyst/commander w worker/among_agents/crew.py: oddzielne częściowe wejścia i sekwencyjny kontekst już istnieją. Dodać trwały schemat wiadomości i tabelę uprawnień/projekcji; odrębny researcher tylko jeśli daje korzyść. Wiadomości do append-only bus/store ze źródłami/confidence; commander widzi dozwolone współdzielone wnioski. Limity aktywnych agentów zależne od ticka. Nie przekazywać całego Ticka jako globalnego promptu.

### Preconditions
AA-10 oraz spike AA-08; ustalona maska obserwacji dla każdego agenta.

### Acceptance criteria
Co najmniej 2 role robocze plus supervisor w normalnym runie; każdy ma inny zakres wejścia i użyteczny wkład. Sentinel niedostępnej obserwacji nie wycieka przez prompt/history/memory przed dozwolonym share, także w następnym ticku. Narzędzie dispatch/submit dostępne tylko kontrolowanemu adapterowi.

### Test steps
1. Uruchom testy projekcji z prywatnym znacznikiem i sprawdź rzeczywiste zserializowane konteksty.
2. Przejdź dwa ticki, sprawdzając pamięć między nimi.
3. Obniż max_active_agents poniżej planowanej liczby: kolejkuj role, nie przekraczaj limitu; brak możliwości wymaganej współpracy oznacz degraded.

### Evidence artifacts
- worker/among_agents/crew.py + scopes
- tests/test_context_isolation.py
- evidence/AA-11/role-contributions.json

### Rollback / fallback
Zredukować równoległość, nie usuwać odrębnych ról. Przy kłopotach Memory użyć jawnego dziennika w procesie; brak pełnej historii u wszystkich.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-51](https://linear.app/skymoondev/issue/SKY-51/aa-12-petla-supervisora-decyzja-budzety-i-ochrona-przed-false-alarms)

## AA-12 · Pętla supervisora: decyzja, budżety i ochrona przed false alarms

**Milestone:** M2
**Estymata:** 1.5 h; native 3 pkt; sprint timebox 45 min.
**Dependency:** [SKY-50 · AA-11](https://linear.app/skymoondev/issue/SKY-50/aa-11-role-agentow-scoped-context-i-wspolny-dziennik).
**Priority:** 1 — Urgent.

### Stan w repo
Aktualnie sekwencyjny Crew, brak autonomicznego tick loop; dodatni budget i bounded calls są, pełny ledger kosztu/tokenów nie.

### Cel
Zamknąć autonomiczną pętlę tick→obserwacje→chat→grounding→decyzja z priorytetem na właściwe działania i szybkość.

### Implementacja
Rozbudować istniejące crew.py/app.py/store.py o autonomiczny state machine (CrewAI Flow tylko jeśli upraszcza implementację): ingest, validate, project, gather, deliberate, decide, validate, dispatch-intent, submit-intent, persist. Zależne od danych progi i jawne confidence; nie traktować ruchu jako dowodu zagrożenia. Równolegle wykonywać niezależne role w limicie; budżet tokenów/requests/time per tick. Commander zwraca akcję, rationale, evidence refs i potrzebę eskalacji.

### Preconditions
AA-11; obecne wartości budget i zweryfikowany model/grounding. Efekty zewnętrzne wciąż tylko intent do AA-13.

### Acceptance criteria
Control bez fałszywego alarmu; outbreak uwzględnia cywilów i wiele sektorów. Nigdy więcej niż max_active_agents; kredyty nie spadają poniżej lokalnego limitu przez niekontrolowane retry. Mierzony tick→decision; podany p50/p95 dla większej próbki lub wszystkie pomiary dla małej. Nie ma hardcoded odpowiedzi ani nieskończonej pętli na exhausted.

### Test steps
1. Uruchom fixture suite oraz warianty z inną liczbą cywilów, sensorami i budżetem.
2. Sprawdź brak danych/konflikt świadków/niski confidence oraz awarię jednego agenta.
3. Porównaj kolejność równoległą i sekwencyjną na tej samej próbce; zapisz jakość i czas, bez strojenia wyłącznie pod tick IDs.

### Evidence artifacts
- evidence/AA-12/decisions.jsonl
- evidence/AA-12/timing-budget.json
- tests/test_supervisor_flow.py

### Rollback / fallback
Po timeout wróć do jawnego stanu degraded/manual review; nie wybieraj observe automatycznie przy potwierdzonym breach. Użyj ostatniej potwierdzonej polityki; wyłącz tylko niedziałający adapter.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-52](https://linear.app/skymoondev/issue/SKY-52/aa-13-adaptery-e2e-prywatna-eskalacja-i-trwaly-outbox)

## AA-13 · Adaptery E2E, prywatna eskalacja i trwały outbox

**Milestone:** M2
**Estymata:** 1 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-51 · AA-12](https://linear.app/skymoondev/issue/SKY-51/aa-12-petla-supervisora-decyzja-budzety-i-ochrona-przed-false-alarms).
**Priority:** 1 — Urgent.

### Stan w repo
SQLite i ręczne publikowanie, run binding/dedup istnieją; private/official policy i trwałe rozliczenie replay do uzupełnienia.

### Cel
Połączyć działający swarm z rzeczywistymi partnerami i kontrolowanymi efektami, bez podwójnych wiadomości lub zgłoszeń.

### Implementacja
Zachować obecne SQLite runs, pending tick reuse, run/config binding, osobne API dispatch/submit oraz ochronę unknown outcome. Rozszerzyć, nie zastępować zweryfikowane zachowanie w store.py/app.py/integrations.py. Oddzielić pure decision od command handlers. Parasail i You.com w live path, WithOne prywatny dispatch przy uzasadnionym alarmie, scenario adapter. Trwały lokalny outbox/journal: official submit unique key (team,tick_id); private dispatch stable replay key (team,scenario,tick_id,effect,target) lub równoważny, stabilny między restartami/replay; run_id wyłącznie jako metadata; stan intended/attempted/ack/unknown. Private-test zawsze blokuje submit i wymusza prywatną allowlistę; official wymaga oddzielnej aktywacji AA-20. Nie odtwarzać automatycznie próbnych ticków do konkursu.

### Preconditions
AA-12; AA-07 potwierdził One lub jawny prywatny fallback, AA-09 bezpieczny submit. Zweryfikowane adaptery używane ponownie bez nowych ad hoc requestów.

### Acceptance criteria
Co najmniej jeden E2E outbreak z live Parasail/You.com i prywatnym efektem; control bez dispatch. Rationale/payload zależy od runtime state i ma source refs. Restart/replay nie duplikuje akcji; unknown outcome nie jest ślepo ponawiany. Zero oficjalnych testowych postów/submissions.

### Test steps
1. Wykonaj fixture→real providers→private Discord i oddzielny control.
2. Przerwij po wysłaniu, przed zapisem ack; uruchom ponownie i sprawdź reconciliation. Nowy run_id dla tego samego ticka nie może tworzyć nowego efektu.
3. Sprawdź status fallback oraz brak dispatch przy niedozwolonym celu; test spy sprawdza zero official submit.

### Evidence artifacts
- evidence/AA-13/e2e-redacted.jsonl
- evidence/AA-13/outbox-state.json
- tests/test_effects_idempotency.py

### Rollback / fallback
Wyłącz efekty, zachowaj outbox i replay. Przy niejednoznacznej wysyłce potwierdź wiadomość po correlation_id; nie ponawiaj treści bez ustalenia. Fallback One tylko prywatny.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-53](https://linear.app/skymoondev/issue/SKY-53/aa-14-harness-jakosci-latency-i-dowodow-scoringu)

## AA-14 · Harness jakości, latency i dowodów scoringu

**Milestone:** M2
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-52 · AA-13](https://linear.app/skymoondev/issue/SKY-52/aa-13-adaptery-e2e-prywatna-eskalacja-i-trwaly-outbox).
**Priority:** 1 — Urgent.

### Stan w repo
25 testów offline ma zapisane PASS w docs; benchmark jakości/latency i prawdziwe dowody partnerów pozostają otwarte.

### Cel
Ocenić swarm na powtarzalnych danych i wykazać, skąd bierze się poprawa wyniku.

### Implementacja
Harness CLI na oficjalnych i perturbowanych fixtures; zapis decyzji, false alarms, civilian/action correctness, liczby agentów, latency/tokenów/grounding/dispatch. Jedna zmienna eksperymentu naraz (model, timeout, równoległość). Wyniki lokalne oznaczone jako proxy i nigdy nie utożsamiane z oficjalną punktacją; osobny odczyt feed judgment.

### Preconditions
AA-13; ustalona referencyjna konfiguracja i oczekiwane zachowanie testów, nie lookup table w produkcji.

### Acceptance criteria
Control suite: zero nieuzasadnionych eskalacji; raport outbreak/action i budżetów bez ukrywania błędów. Każdy partner ma udokumentowany wkład, a jego usunięcie zmienia dane/uzasadnienie/efekt. Macierz 100 pkt wskazuje evidence i nieweryfikowane elementy; nikt nie raportuje gwarantowanych 100/100.

### Test steps
1. Uruchom seeded suite i mały, jawnie ograniczony kosztowo zestaw live smoke.
2. Zrób ablation grounding/rola/dispatch i porównaj wkład, nie tylko liczbę requestów.
3. Wybierz najszybszą konfigurację spełniającą poprawność; zachowaj baseline oraz liczność próbki.

### Evidence artifacts
- evidence/AA-14/benchmark.csv
- evidence/AA-14/scorecard.md
- tests/test_scoring_proxies.py

### Rollback / fallback
Zatrzymaj tuning po timeboxie; wróć do ostatniej konfiguracji przechodzącej control i budget. Oznacz małą próbkę, zamiast publikować pozornie wiarygodne percentyle.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

## 3 · Next.js representative dashboard
Po M2. AA-15–17: lokalny read model/API, mapa i statystyki agentów, shared chat i scoreboard. Gate: UI odwzorowuje ten sam run_id/tick co orchestrator, pokazuje tryb, źródło i świeżość danych; brak sekretów w przeglądarce.

Linear: [SKY-54](https://linear.app/skymoondev/issue/SKY-54/aa-15-lokalny-read-modelapi-dla-nextjs)

## AA-15 · Lokalny read model/API dla Next.js

**Milestone:** M3
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 20 min.
**Dependency:** [SKY-53 · AA-14](https://linear.app/skymoondev/issue/SKY-53/aa-14-harness-jakosci-latency-i-dowodow-scoringu).
**Priority:** 2 — High.

### Stan w repo
FastAPI + Next API z same-origin/loopback proxy istnieją. Rozbudować obecny read model zamiast tworzyć nowy backend.

### Cel
Udostępnić dashboardowi spójny stan orchestratora i zdarzenia bez ujawniania sekretów lub możliwości dowolnego dispatch.

### Implementacja
Rozszerzyć istniejące FastAPI oraz app/api/*, lib/worker.ts i lib/types.ts. Zachować same-origin/loopback proxy i prywatne błędy providerów. Python wystawia health, snapshot i stream SSE albo prosty polling. Wspólny kontrakt run/tick/events/mode/source/staleness; Next.js pobiera tylko dozwolone pola. Bind lokalny, kontrola origin i redakcja payloadów. Minimalne start/stop/replay tylko jeśli konieczne; nie wystawiać otwartego proxy MCP.

### Preconditions
AA-14; działający CLI E2E i znormalizowany dziennik.

### Acceptance criteria
UI czyta ten sam run_id i tick co CLI, potrafi reconnect/dedup zdarzeń. Sekrety, auth headers, prywatne channel/connection IDs nie znajdują się w API ani bundle. Mutacje i official mode nie uruchamiają się przez zwykły GET/przeładowanie strony.

### Test steps
1. Porównaj snapshot i journal.
2. Zerwij połączenie, wznowienie zachowuje kolejność i nie dubluje zdarzeń.
3. Sprawdź odpowiedzi API i bundle na syntetyczne znaczniki sekretów; próba dowolnego targetu odrzucona.

### Evidence artifacts
- docs/dashboard-contract.md
- evidence/AA-15/api-redacted.json
- tests/test_dashboard_projection.py

### Rollback / fallback
Jeśli streaming opóźnia pracę, polling tego samego read modelu. CLI pozostaje działającym demo; brak tworzenia drugiego stanu aplikacji.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-55](https://linear.app/skymoondev/issue/SKY-55/aa-16-mapa-obiektu-i-statystyki-agentow-w-nextjs)

## AA-16 · Mapa obiektu i statystyki agentów w Next.js

**Milestone:** M3
**Estymata:** 1 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-54 · AA-15](https://linear.app/skymoondev/issue/SKY-54/aa-15-lokalny-read-modelapi-dla-nextjs).
**Priority:** 3 — Medium.

### Stan w repo
UI ma sector cards i role summaries; brak przestrzennego schematu i pełnych agent stats.

### Cel
Pokazać jurorowi, gdzie jest zagrożenie, co robią agenci i dlaczego podjęto decyzję.

### Implementacja
Rozbudować istniejące app/page.tsx i app/globals.css (sector cards/role summaries już są). Jedna reprezentacyjna strona: schemat sektorów, status containment/civilian, aktywni agenci, confidence, budżet, czas decyzji, wybrana akcja. Layout jako schemat logiczny, jeśli brak rzeczywistego planu; nie udawać geometrii budynku. Dane zawsze z AA-15. Wyraźny badge offline/private-test/official i stale/error.

### Preconditions
AA-15; kontrakt obsługuje wiele sektorów oraz częściowe dane.

### Acceptance criteria
Mapa i statystyki aktualizują się z replay/live, bez wymyślonych liczb. Control i outbreak wizualnie odróżnialne; unknown nie jest zerem. Na laptopie mieści się najważniejszy przebieg, kolory mają także opisy; żadnych nieczynnych przycisków udających działanie.

### Test steps
1. Odtwórz outbreak, control, wiele sektorów i brak danych.
2. Zatrzymaj backend: pokaż stale/error, nie pozornie live.
3. Przejdź całość klawiaturą i sprawdź czytelność na szerokości laptopa.

### Evidence artifacts
- evidence/AA-16/dashboard-outbreak.png
- evidence/AA-16/dashboard-control.png
- docs/demo-flow.md

### Rollback / fallback
Przy presji czasu karta/tabela sektorów zamiast rozbudowanej mapy; bez animacji, edytora map i deploy. Zachować czytelne dane i źródło.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-56](https://linear.app/skymoondev/issue/SKY-56/aa-17-shared-chat-timeline-decyzji-i-prawdziwy-scoreboard)

## AA-17 · Shared chat, timeline decyzji i prawdziwy scoreboard

**Milestone:** M3
**Estymata:** 0.75 h; native 2 pkt; sprint timebox 20 min.
**Dependency:** [SKY-55 · AA-16](https://linear.app/skymoondev/issue/SKY-55/aa-16-mapa-obiektu-i-statystyki-agentow-w-nextjs).
**Priority:** 2 — High.

### Stan w repo
UI pokazuje raw scoreboard JSON; nie ma shared chat timeline ani czytelnej tabeli wyników.

### Cel
Uwidocznić współpracę agentów i oddzielić lokalną ocenę od oficjalnego wyniku.

### Implementacja
Rozszerzyć app/page.tsx, API i store; obecny raw scoreboard JSON zamienić w czytelną tabelę. Panel czatu/timeline z agentem, zakresem obserwacji, źródłami, confidence i rationale; filtr run/tick. Panel scoreboard tylko z get-scoreboard, odfiltrowany lokalnie dla handle i oznaczony czasem pobrania. Lokalne proxy metrics w oddzielnej sekcji. Prywatne message refs nie są publikowane; kopia dowodów po redakcji.

### Preconditions
AA-16; M1 scoreboard read zweryfikowany lub fixture jawnie oznaczony.

### Acceptance criteria
Da się prześledzić observation→share→grounding→decision→effect→judgment. Oficjalny wynik 0–1/totals nie jest opisany jako rubryka 100 pkt. Stan disconnected/pending/fallback/duplicate czytelny. Brak fikcyjnego czatu i losowych statystyk.

### Test steps
1. Odtwórz run i sprawdź powiązania source refs/tick.
2. Sprawdź fixture oraz prawdziwy read-only scoreboard, bez submit.
3. Wywołaj brak danych/odłączenie i duplikat zdarzenia; UI pokazuje poprawne etykiety.

### Evidence artifacts
- evidence/AA-17/chat-scoreboard.png
- evidence/AA-17/event-trace.json
- docs/ui-labels.md

### Rollback / fallback
Timeline/tabela zamiast interaktywnego czatu. Gdy feed nie działa, pokaż ostatni wynik ze znacznikiem czasu lub unavailable; nie zastępuj go wygenerowaną punktacją.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

## 4 · Hardening, demo + reproducibility
Po M3. AA-18–20: błędy/restart/dedup, jedno polecenie uruchomienia, komplet dowodów i przygotowanie oficjalnego zgłoszenia. Gate: czysty start i replay, gotowe demo, oficjalny wynik/formularz tylko w świadomie uruchomionym finalnym przebiegu; prywatne testy pozostają prywatne.

Linear: [SKY-57](https://linear.app/skymoondev/issue/SKY-57/aa-18-hardening-timeout-retry-restart-privacy-i-budzety)

## AA-18 · Hardening: timeout, retry, restart, privacy i budżety

**Milestone:** M4
**Estymata:** 1 h; native 2 pkt; sprint timebox 20 min.
**Dependency:** [SKY-56 · AA-17](https://linear.app/skymoondev/issue/SKY-56/aa-17-shared-chat-timeline-decyzji-i-prawdziwy-scoreboard).
**Priority:** 1 — Urgent.

### Stan w repo
Istnieje 8 testów API + 17 worker z mockowaną siecią, auth/binding/dedup/unknown outcome. Rozszerzyć o nowe ryzyka, zachować regresję.

### Cel
Zapobiec najdroższym awariom podczas demo i oficjalnego przebiegu.

### Implementacja
Zachować i rozszerzyć istniejące tests/api-safety.test.ts (8 cases) oraz worker/tests/test_worker.py (17 cases); nie pisać od nowa testów już pokrytych. Test matrix: provider 401/429/5xx/timeout, błędny MCP schema, missing/null observation, exhausted, utrata połączenia, restart outbox. Retry ograniczone i zgodne z idempotency; One najwyżej jeden ostrożny retry. Reconcile niejednoznacznych writes; maskowanie auth i prywatnych identyfikatorów; limity requests/tokenów/agentów.

### Preconditions
AA-17 i działająca ścieżka E2E; testy błędów wykonywane przez stuby, nie przez spamowanie usług.

### Acceptance criteria
Żaden error nie wywołuje nieograniczonej pętli, nie przekracza budget i nie przełącza się na oficjalny kanał. Restart nie duplikuje dispatch/submit. Syntetyczny secret sentinel nie trafia do logów/API/evidence. Zatrzymanie procesu zachowuje bezpieczny stan.

### Test steps
1. Wykonaj wybraną matrix fault injection.
2. Przeprowadź kill/restart w punktach przed/po efekcie oraz przed ack.
3. Skanuj przygotowane artefakty pod kątem syntetycznych sekretów i sprawdź prywatną allowlistę.

### Evidence artifacts
- evidence/AA-18/fault-matrix.md
- tests/test_recovery.py
- docs/troubleshooting.md

### Rollback / fallback
Wyłącz niedziałający adapter lub zmniejsz concurrency; wróć do ostatniego passing run. Tryb replay pozostaje dostępny; nie czyść automatycznie outbox ani dowodów.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-58](https://linear.app/skymoondev/issue/SKY-58/aa-19-jedno-polecenie-evidence-pack-i-3-minutowe-demo)

## AA-19 · Jedno polecenie, evidence pack i 3-minutowe demo

**Milestone:** M4
**Estymata:** 1 h; native 2 pkt; sprint timebox 25 min.
**Dependency:** [SKY-57 · AA-18](https://linear.app/skymoondev/issue/SKY-57/aa-18-hardening-timeout-retry-restart-privacy-i-budzety).
**Priority:** 1 — Urgent.

### Stan w repo
README, docs/VERIFICATION.md i skrypty startowe istnieją. Potrzebne odtworzenie od zera oraz finalny evidence/demo pack.

### Cel
Umożliwić obcej osobie uruchomienie projektu i ocenę realnego wkładu czterech partnerów.

### Implementacja
Uzupełnić istniejące README i docs/VERIFICATION.md oraz skrypty setup/dev/doctor; oddzielić stare zapisane wyniki od nowych evidence. README quickstart z pustym .env.example, wymaganiami wersji, pojedynczym startem i offline replay; pinned deps. Seeded demo outbreak→control→trace współpracy→prywatny efekt→scoreboard read. Manifest dowodów mapuje rubrykę i statusy. Krótki film/zrzuty tylko rzeczywistych przebiegów i scenariusz 3-min demo. Wymienić znane ograniczenia oraz One fallback bez obietnicy pełnych punktów.

### Preconditions
AA-18; przygotowany prywatny test i zredagowane artefakty; nie publikować sekretów ani prywatnych permalinków.

### Acceptance criteria
Czyste środowisko odtwarza offline jednym poleceniem bez kluczy, live przechodzi doctor i wymaga lokalnej konfiguracji. Wszystkie 4 integracje mają dowód lub jawny brak/fallback. Brak ręcznie edytowanego stanu; data/commit/seed i tryb na nagraniu. Demo zawiera zero false alarms na control.

### Test steps
1. Uruchom instrukcję od zera w czystym katalogu/venv.
2. Odtwórz demo i zmierz czas; dopasuj do 3 minut.
3. Zweryfikuj każdy link/plik w manifest i redakcję; sprawdź, że .env nie jest w paczce.

### Evidence artifacts
- README.md
- docs/demo-script.md
- evidence/manifest.json
- evidence/AA-19/reproducibility.md
- demo recording

### Rollback / fallback
Demo offline/replay oznaczone jako takie plus zapisany dowód rzeczywistych integracji. Nie nazywaj filmu bieżącym live. Jeśli brak czasu, zrezygnuj z montażu i dodatkowych efektów UI.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.

Linear: [SKY-59](https://linear.app/skymoondev/issue/SKY-59/aa-20-finalny-gate-oficjalny-run-scoreboard-i-formularz)

## AA-20 · Finalny gate: oficjalny run, scoreboard i formularz

**Milestone:** M4
**Estymata:** 0.5 h; native 1 pkt; sprint timebox 15 min.
**Dependency:** [SKY-58 · AA-19](https://linear.app/skymoondev/issue/SKY-58/aa-19-jedno-polecenie-evidence-pack-i-3-minutowe-demo).
**Priority:** 1 — Urgent.

### Stan w repo
Live provider calls, tick/submission i wynik scoreboardu niezweryfikowane. Istnieją przyciski submit/send, lecz samo live nie może oznaczać zgody na oficjalny run.

### Cel
Przygotować i następnie świadomie wykonać właściwe zgłoszenie, oddzielone od testów prywatnych.

### Implementacja
Checklist operatora: termin z organizatorami/formularzem, unikalny TEAM_HANDLE, aktualne schema/auth, działający budget i control tests, finalne linki/commit/demo. Domyślnie tylko preview i read-only scoreboard. Właściciel jawnie uruchamia finalny official mode: prawdziwy tick (kursor), jedna wybrana odpowiedź/tick, odczyt judgment/scoreboard. Oficjalny Discord tylko jeśli właściciel odrębnie zatwierdzi cel i finalną eskalację — obecna instrukcja nie zezwala publikować testów. Przygotować wymagany Google Form; wysłanie to osobny końcowy krok.

### Preconditions
AA-19; właściciel zna wpływ pierwszego submit i aktywuje finalny run. Prywatny handle testowy nie jest prywatnym scoreboardem; nie przesyłać testowej kolejki do konkursu. Brak potwierdzonego oficjalnego kanału pozostawia dispatch wyłączony.

### Acceptance criteria
Gotowość i wykonanie mają oddzielne statusy. Tylko po finalnej aktywacji: potwierdzony live judgment/scoreboard i receipt formularza, jeśli został wysłany. Nieprawidłowy tick/action/team blokuje przed requestem. Duplikat zachowuje pierwszą odpowiedź, brak resetu; oficjalne testowe posty = 0. Bez aktywacji story pozostaje gotowe do wykonania, nie Done.

### Test steps
1. Najpierw sprawdź preview payloadu oraz read-only scoreboard, bez get-tick/submit.
2. Po świadomej aktywacji wykonaj finalny przebieg i zachowaj acknowledgment; przy niejednoznacznym wyniku sprawdź stan, nie zmieniaj akcji w retry.
3. Potwierdź wymagane pola formularza i jego receipt; jeśli niedostępny, skontaktuj się osobiście z organizatorami przed faktycznym deadlinem.

### Evidence artifacts
- docs/final-checklist.md
- evidence/AA-20/final-payload-preview.json
- evidence/AA-20/judgment-redacted.json
- evidence/AA-20/submission-receipt.md

### Rollback / fallback
Jeśli feed padnie, zachowaj oryginalne tick/decision w outbox i oznacz pending; późniejszy replay tylko w tym samym zatwierdzonym trybie. Brak oficjalnego dispatch bez zatwierdzenia; ręczny fallback również wymaga właściwego celu. Formularz wymagany niezależnie od Discorda.

Źródło: [oficjalny przewodnik](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes). Evidence paths są planowanymi artefaktami; nie oznaczają wykonanego testu. Wszystkie testy Discord wyłącznie prywatne.
