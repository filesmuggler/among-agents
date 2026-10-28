# Theme 1 — macierz punktów i dowodów

Stan: **28.10.2026, America/Los_Angeles**. Źródło: §8 [przewodnika organizatora](https://youdotcom-oss.github.io/halloween-hack-2026/#8-how-you-are-scored), [wersja 424320d](https://github.com/youdotcom-oss/halloween-hack-2026/blob/424320dbc9b217849df85f54cca20e493861692a/index.html). Poniższe artefakty to wymagania do zebrania, nie deklaracja ukończenia integracji.

| Kryterium | Punkty | Stories istniejącego planu | Dowód wymagany do oceny | Wkład M0 |
| --- | ---: | --- | --- | --- |
| Szybkość containment względem baseline | 30 | AA-12, AA-14, AA-20 | Zmierzony przebieg tick → decyzja → scoreboard i porównanie z baseline | Kontrakt i lokalny smoke; brak pomiaru konkursowego |
| False-alarm rate | 20 | AA-07, AA-10, AA-12, AA-14 | Control oraz warianty wysokiego motion; brak nieuzasadnionej eskalacji | Oficjalne fixtures i negatywne testy offline |
| Cywile / poprawność eskalacji | 20 | AA-11–14, AA-20 | Właściwa akcja, cel, budżet i brak duplikatów | Zachowane pola wejścia, rozdzielone efekty i blokady |
| Rzeczywisty wkład partnerów | 20 | AA-03, AA-05, AA-06–08, AA-13–14 | Przewodnik wskazuje trace CrewAI, grounding You.com, inferencję Parasail i dispatch Discord przez webhook; projekt ma używać One zgodnie z decyzją użytkownika | Lokalna konstrukcja CrewAI; dowody live i wpływ rozbieżności transportu na ocenę pozostają otwarte |
| Jakość kodu i odtwarzalność | 10 | AA-00–02, AA-18–19 | Lockfiles, pojedyncza komenda startu, powtarzalne dane i zredagowane evidence | Bezpośredni zakres M0 |

**Decyzja użytkownika z 28.10.2026: używamy One do Discorda.** AA-06/07/13 pozostają pracą nad tą integracją; M1 ma zweryfikować One na potwierdzonym prywatnym kanale po świadomej aktywacji wysyłki. Aktualny §3.4 zabrania tego transportu dla oficjalnego Track 1 i wymaga webhooka lub dopuszczonego ręcznego postu. Zapisujemy tę rozbieżność i pozostawiamy ocenę organizatorom; nie gwarantujemy pełnych punktów ani nie zastępujemy One webhookiem bez zmiany decyzji użytkownika. Żaden wariant dispatch nie został wykonany w M0.

Wynik pojedynczej odpowiedzi feedu **0–1 nie jest wynikiem rubryki 100 pkt**. Feed przyznaje 1 za poprawną akcję, 0,5 za pomylenie contain/evacuate oraz 0 za observe przy breach; działanie na control może zostać false alarm. Tie-break uwzględnia czas czystego przebiegu tick → scoreboard. Dyskwalifikatory: jeden agent udający swarm, hardcoded odpowiedzi scenariusza, partner użyty wyłącznie pozornie.

Każdy przyszły dowód powinien podawać datę, wersję kodu, tryb fixture/live, seed lub run/tick, wynik i ograniczenia. W repo oraz Linear zapisujemy wyłącznie zredagowane artefakty: bez `.env`, tokenów, nagłówków autoryzacji, webhooków, prywatnych identyfikatorów kanałów i connection keys. Build, mock i lokalny smoke nigdy nie otrzymują etykiety PASS_LIVE.
