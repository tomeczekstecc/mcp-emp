# 03 — User Use Cases

Each use case: **actor**, **trigger** (what the user says), **flow**,
**tools used** (from [02-features](02-features.md)), **success criteria**.

---

## UC-1 — "Add what I just did"

- **Actor:** pracownik
- **Trigger:** *"Dodaj zadanie: odpowiedziałem na maila od p. Kowalskiego w sprawie SOD-2024/123"*
- **Flow:**
  1. LLM calls `pobierz_typy_zadania` (B12) → finds "Obsługa korespondencji".
  2. LLM drafts task with `dotyczy`, `slownik_typ_zadania_id`, `nr_sprawy_sod`.
  3. Show draft to user → user confirms.
  4. `dodaj_moje_zadanie` (B1).
  5. Optionally `zakoncz_zadanie` (B5) if already done.
- **Success:** Task visible in `lista/moje` with correct type and metadata.

---

## UC-2 — "Mark X as done"

- **Actor:** pracownik
- **Trigger:** *"Zakończ zadanie o SOD-2024/123"*
- **Flow:**
  1. `lista_moich_zadan` (B10), filter by `nr_sprawy_sod` or `dotyczy`.
  2. If ambiguous → ask user to disambiguate.
  3. `zakoncz_zadanie` (B5) with chosen id.
  4. Report new status (`ZAKOŃCZONE` vs. `DO_OCENY`).
- **Success:** Status transitions correctly; user told whether evaluation pending.

---

## UC-3 — "Clean up obsolete drafts"

- **Actor:** pracownik
- **Trigger:** *"Usuń wszystkie moje wersje robocze starsze niż 2 tygodnie"*
- **Flow:**
  1. `lista_moich_zadan_wszystkie` (B11) → filter `status=W_EDYCJI`, `data_zlecenia < now-14d`.
  2. Preview list to user.
  3. On confirm → `usun_zadanie` (B8) per id with confirmation envelope (E2).
- **Success:** Only `W_EDYCJI` deleted (EMP enforces); user gets summary.

---

## UC-4 — "How am I doing this cycle?"

- **Actor:** pracownik
- **Trigger:** *"Podsumuj mój bieżący cykl pracy"*
- **Flow:**
  1. `moje_statystyki_cyklu` (C1).
  2. `lista_moich_zadan` (B10) for active.
  3. LLM composes Polish narrative.
- **Success:** One-paragraph readable summary.

---

## UC-5 — "Compare me with my team"

- **Actor:** pracownik or kierownik
- **Trigger:** *"Porównaj moje wyniki z zespołem"*
- **Flow:**
  1. `porownanie_ja_vs_zespol` (C7) — composes C1 + C2.
  2. Returns structured deltas: points, count, overdue.
  3. LLM concludes with data-grounded statement.
- **Success:** No hallucinated numbers; honest comparison.

---

## UC-6 — "Who in my team is overloaded?"

- **Actor:** kierownik
- **Trigger:** *"Czy ktoś w zespole jest przeciążony?"*
- **Flow:**
  1. `statystyki_zespolu` (C2).
  2. `wykryj_problemy` (C8) — heuristics on load + overdue.
  3. Name specific employees with evidence.
- **Success:** Actionable list, not generic advice.

---

## UC-7 — "What should I work on next?"

- **Actor:** pracownik
- **Trigger:** *"Co powinienem teraz robić?"*
- **Flow:**
  1. `kontekst_biezacej_pracy` (D1).
  2. LLM ranks by deadline, points/effort, state.
  3. Suggests top 1–3 with reasoning.
- **Success:** Prioritised shortlist.

---

## UC-8 — "I just finished a meeting, log my work"

- **Actor:** pracownik
- **Trigger:** *"Miałem spotkanie 10:00–11:30 z zespołem o migracji bazy"*
- **Flow:**
  1. LLM picks type via B12 + D6.
  2. Computes `czas=01:30`.
  3. `dodaj_moje_zadanie` (B1) dry-run preview (E1).
  4. On confirm → create + immediate `zakoncz_zadanie` (B5).
- **Success:** Time-tracked task created and closed in one turn.

---

## UC-9 — "Bulk-log a week of forgotten work"

- **Actor:** pracownik
- **Trigger:** *"Zapomniałem logować przez tydzień, oto co robiłem: [tekst]"*
- **Flow:**
  1. LLM parses text into N drafts.
  2. `szablony_zadan` (D4) fills defaults.
  3. `bulk_create` (D3) `dry_run=true` → preview table.
  4. On confirm → batch create + optional batch zakoncz.
- **Success:** Whole batch in one confirmation; failures reported individually.

---

## UC-10 — "Spot my recurring tasks"

- **Actor:** pracownik
- **Trigger:** *"Jakie zadania robię regularnie co tydzień?"*
- **Flow:**
  1. `lista_moich_zadan_wszystkie` (B11) — last 8–12 weeks.
  2. `wykryj_powtarzajace` (D5) — group by type + normalised dotyczy.
  3. LLM lists patterns + offers next instances.
- **Success:** Routine made explicit; opt-in pre-creation.

---

## UC-11 — "Daily standup helper"

- **Actor:** pracownik
- **Trigger:** *"Przygotuj notatkę na stand-up"*
- **Flow:**
  1. `raport_dzienny` (C6) for yesterday.
  2. `lista_moich_zadan` (B10) for today.
  3. LLM produces *Wczoraj / Dziś / Blockers* note.
- **Success:** Copy-pasteable Polish standup note.

---

## UC-12 — "Audit a single task"

- **Actor:** kierownik
- **Trigger:** *"Pokaż historię zadania #1234"*
- **Flow:**
  1. `pobierz_zadanie` (B9).
  2. `historia_zadania` (B13).
  3. LLM formats timeline.
- **Success:** Clear chronology of who/what/when.
