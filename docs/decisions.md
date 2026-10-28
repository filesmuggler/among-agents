# M0 — decyzje i otwarte bramki

Stan: **28.10.2026, America/Los_Angeles**. Owner projektu i poniższych bramek: **Kris**. Bieżące wymagania organizatora oraz datowane źródła: [spec.md](spec.md).

## Przyjęte decyzje

- Rozwijamy zastany Next.js i lokalny FastAPI/CrewAI. Nie tworzymy drugiego scaffolda, nie resetujemy working tree i zachowujemy istniejące klucze `.env`; token i prywatny cel uzupełniono na wyraźne polecenie właściciela.
- Domyślna weryfikacja M0 działa na fixtures, bez sieci partnerów. Klucze API nie trafiają do klienta Next.js, `NEXT_PUBLIC_*`, logów ani Linear.
- Analiza, wysyłka Discord i zgłoszenie containment to oddzielne operacje. Sam `RUN_MODE=live`, treść ticka albo odpowiedź modelu nie oznaczają zgody na publikację.
- W tym zadaniu nie wysyłamy żadnych wiadomości Discord, nie wykonujemy official submit i nie zgłaszamy formularza. Przyszłe testy dispatch wymagają osobnej, świadomej aktywacji oraz potwierdzonego prywatnego celu. Oficjalny kanał wydarzenia nie jest prywatnym kanałem testowym użytkownika.
- **Użytkownik 28.10.2026 wybrał One jako integrację Discorda projektu.** Zachowujemy i rozwijamy ten adapter; M1 sprawdzi go na potwierdzonym prywatnym kanale po świadomej aktywacji wysyłki. Aktualny §3.4 przewodnika wymaga innego transportu dla oficjalnego Track 1, co zapisujemy jako otwartą rozbieżność wpływającą na pewność punktacji. Nie zmieniamy wybranej architektury na webhook. M0 nie wykonuje dispatch, nie wdraża webhooka i nie kopiuje jego adresu.
- Zostają przypięte, testowane wersje zależności. Opis CrewAI 1.13.0 w przewodniku nie wymusza downgrade zastanego 1.15.2. Embeddings, pamięć semantyczna, autonomiczny loop, pełna mapa i deployment są poza M0.

## Otwarte bramki

| Bramka | Status | Owner / działanie | Co blokuje |
| --- | --- | --- | --- |
| Tożsamość prywatnego celu Discord | KONFIGURACJA GOTOWA; metadata API PENDING | Kris potwierdził prywatny serwer/kanał i podał ID; One potwierdził serwer. Odczyt kanału zwraca HTTP 401; wartości pozostają lokalnie | Weryfikację integracji w M1; użytkownik potwierdził cel, ale API nie potwierdziło metadata ani prawa wysyłki |
| Parasail model, dostęp i billing | PENDING | Kris potwierdza budżet i dostęp; M1 wykonuje małą inferencję po aktywacji live | PASS_LIVE Parasail; `/models` i mock nie są inferencją |
| You.com scopes i kredyty | PENDING | Kris potwierdza konto; M1 wykonuje ograniczony search/grounding | PASS_LIVE You.com |
| Scenario auth i tożsamość zespołu | PENDING | Kris potwierdza, czy organizator wymaga tokenu, oraz unikalny handle; nie zakładamy wymagania nieudokumentowanego tokenu | Kontrolowany get-tick i submit; osobny handle nie oznacza prywatnego sandboxa |
| One → prywatny Discord | PENDING — M1; HTTP 401 dla kanału | Najpierw wyjaśnić błąd odczytu metadata kanału; późniejszy test wysyłki wymaga świadomej aktywacji. Odczyt serwerów działa, wiadomości nie wysyłano | PASS_LIVE One; sama obecność klucza lub discovery nie potwierdza wysyłki |
| Rozbieżność oficjalnego transportu | PENDING — poza M0 | Kris potwierdza z organizatorami wpływ użycia One na oficjalny Track 1; projekt zachowuje wybraną integrację | Gwarancję zgodności oficjalnego dispatch i pełnej punktacji; nie blokuje prywatnych testów One |
| Deadline formularza | **NIEPOTWIERDZONY** | Kris ustala cutoff z organizatorami lub formularza; nie wyciągamy go z godzin wydarzenia | Planowanie finalnego zgłoszenia; 20:30 nie jest potwierdzonym terminem |
| Finalna publikacja | PENDING — poza M0 | Kris świadomie aktywuje oddzielnie official dispatch, containment submission i formularz | Wszelkie oficjalne efekty zewnętrzne |

Otwarte bramki live nie blokują lokalnej walidacji M0. Nie mogą jednak zostać przedstawione jako zaliczone na podstawie testów offline. Wyniki wykonanych sprawdzeń trafiają do [VERIFICATION.md](VERIFICATION.md), a istniejące zadania Linear aktualizujemy bez tworzenia duplikatów.
