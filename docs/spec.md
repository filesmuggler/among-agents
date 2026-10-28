# M0 — kontrakt wymagań Theme 1

Stan źródeł: **28.10.2026, America/Los_Angeles**. Owner: Kris. Zakres M0: bezpieczny lokalny Next.js ↔ FastAPI/CrewAI, konfiguracja, kontrakt i testy offline. Pełny swarm oraz dowody integracji live należą do kolejnych etapów; M0 nie potwierdza wyniku konkursowego.

## Źródło i pierwszeństwo

Sprawdzono [przewodnik organizatora](https://youdotcom-oss.github.io/halloween-hack-2026/#11-verification-notes) oraz [wersję `index.html` z commitu 424320d](https://github.com/youdotcom-oss/halloween-hack-2026/blob/424320dbc9b217849df85f54cca20e493861692a/index.html), opublikowaną 28.10 o 15:02:57 PDT. [Surowe źródło tej wersji](https://raw.githubusercontent.com/youdotcom-oss/halloween-hack-2026/424320dbc9b217849df85f54cca20e493861692a/index.html) pozwala odtworzyć odczyt. Wskazywany przez stronę `PARTNER-FACTS.md` zwracał 404; nie traktujemy go jako przeczytanego audytu.

Aktualny §3.4 **wyklucza One/WithOne jako transport eskalacji Track 1** i wskazuje webhook jako wymaganą ścieżkę automatyczną; dopuszcza też ręczny post. Jest to rozbieżność ze starszym `via: one-mcp` w przykładowym ticku. **Użytkownik 28.10.2026 potwierdził, że projekt ma używać One do Discorda.** Zachowujemy One jako docelową integrację projektu, z blokadą wysyłki do czasu świadomej aktywacji i potwierdzenia prywatnego celu. M1 ma sprawdzić rzeczywisty dispatch One na prywatnym kanale. Rozbieżność z aktualnym przewodnikiem pozostaje otwarta dla oficjalnego zgłoszenia i nie pozwala zagwarantować punktacji. Webhook nie jest wybraną architekturą ani implementacją M0; jego adresu nie kopiujemy do repo. W M0 nie wysyłamy żadnej wiadomości.

## Stały kontrakt scenariusza

| Element | Reguła |
| --- | --- |
| Tick | `tick_id`, `facility_id`, `sector_reports[]`, `swarm_budget`, `escalation_channel` |
| Sektor | Zachować `sensors`, `sighting`, `civilian_status`, `containment_state`; obsługiwać więcej niż jeden sektor |
| Budżet | Nie przekraczać `swarm_budget.max_active_agents`; uwzględniać dostępne kredyty |
| Decyzja | `contain`, `evacuate` albo `observe`, powiązane z konkretnym tickiem i zespołem |
| Eskalacja | `app=discord`; pole celu z ticka nie nadaje uprawnienia do wysyłki |
| Team | Własny, konsekwentnie używany handle; 2–32 małych liter, cyfr i myślników, pierwszy znak alfanumeryczny |

Zachowujemy oficjalne fixtures outbreak/control jako dane offline. Wymaganie konkursowe to kilka współpracujących ról z częściową wiedzą i rzeczywistym wkładem partnerów. Lokalny deterministyczny demo/replay musi być oznaczony jako fixture; nie jest dowodem działania live. Macierz punktów i dowodów: [scoring-matrix.md](scoring-matrix.md).

## Korekty techniczne §11

- CrewAI: Python 3.10–3.13; M0 przypina 3.12. Przewodnik opisuje CrewAI 1.13.0, a zastany starter 1.15.2 — zgodność nowszej wersji potwierdzają lokalne testy, nie samo wskazanie przewodnika.
- Parasail Responses API wymaga `store: false`. Dotyczy to ewentualnego użycia tego API; nie uzasadnia zmiany działającego klienta Chat Completions w M0.
- Model embeddings wskazany przez organizatora: `parasail-ai/GritLM-7B-vllm`, bez opublikowanej tam ceny. Embeddings, indeks lore i pamięć semantyczna pozostają poza M0.
- Cena Kimi K3 w odczytanej wersji przewodnika: $3/$15 za milion tokenów wejścia/wyjścia. To datowana informacja źródłowa, nie potwierdzenie rachunku ani dostępności modelu użytkownika.
- You.com Search/Contents używają `X-API-Key`; Parasail ma własny klucz i bazę `https://api.parasail.io/v1`. Sukces odczytu listy modeli nie potwierdza inferencji. Limity i billing sprawdzić przed live.
- Przy użyciu wrappera MCP CrewAI stosować jawny `MCPServerHTTP` z `streamable=True`; przewodnik ostrzega przed skrótem URL w działającej pętli zdarzeń. Istniejący jawny klient MCP nie wymaga zastąpienia tylko dla zgodności ze snippetem.

## Kryteria zamknięcia M0

1. `.env` i prywatne dane są ignorowane; template zawiera puste sekrety i bezpieczne defaults. Raport pokazuje wyłącznie nazwy oraz status konfiguracji, bez wartości.
2. Zachowano zastany starter i pracę użytkownika; instalacja korzysta z lockfiles, a README podaje jedną ścieżkę uruchomienia.
3. Next.js komunikuje się z lokalnym workerem według udokumentowanego kontraktu; sekrety dostawców pozostają po stronie serwera.
4. Smoke test obejmuje health, fixture run i odczyt wyniku oraz negatywne przypadki konfiguracji/uwierzytelnienia. Offline nie wykonuje requestów do partnerów.
5. Wysyłka Discord i submission są oddzielnymi, domyślnie zablokowanymi efektami. W tym zadaniu nie są wykonywane nawet przy obecnych kluczach.
6. Wyniki testów, ograniczenia i niewykonane próby są zapisane w [VERIFICATION.md](VERIFICATION.md); otwarte bramki mają właściciela w [decisions.md](decisions.md).
