---
name: emp-log-task
description: Create and immediately complete an EMP task for the current work, backdating it to the correct date. Use whenever the user says "dodaj zadanie do EMP", "zaloguj zadanie", "log task to EMP", "add EMP task", "zapisz zadanie", "log this work", or wants to record completed work in EMP. Also triggers on "dodaj do ewidencji", "wpisz do EMP", "zaloguj pracę".
---

# EMP — Dodaj i zakończ zadanie

Skill tworzy zadanie w EMP, kończy je i backdatuje na wskazaną datę.
Używa narzędzi `emp_add_my_task`, `emp_complete_task` i `emp_backdate_task` przez MCP server `emp`.

## Workflow

### 1. Ustal kontekst

Zbierz informacje potrzebne do stworzenia zadania:

**Wymagane:**
- `task_type_id` — ID typu zadania z `emp_list_task_types()`
- `subject` — opis zadania (co było robione)
- `target_date` — data pracy w formacie `YYYY-MM-DD` (domyślnie: dziś)

**Opcjonalne:**
- `tag_ids` — tagi z `emp_list_tags()` (np. ePW=7, LSI2021=3, AI/BA=5, eMP=1, AZ=87)
- `quantity` — ilość (gdy typ wymaga)
- `time` — czas HH:MM (gdy typ wymaga)

Jeśli użytkownik nie podał typu zadania, zapytaj o kontekst i dobierz typ:

| Rodzaj pracy | Typ |
|---|---|
| Nowa funkcjonalność / duży feature | `list_task_types(search="Nowa funkcjonalność")` → id≈27 (8 pkt) |
| Zmiana / ulepszenie istniejącego | `list_task_types(search="Zmiana funkcjonalności")` → id≈49 (3 pkt) |
| Nowy element / komponent | `list_task_types(search="Nowy element")` → id≈26 (3 pkt) |
| Drobna poprawka / fix | `list_task_types(search="Drobna poprawka")` → id≈28 (2 pkt) |
| Analiza / badanie problemu | `list_task_types(search="Analiza")` → id≈52 (3 pkt) |
| Spotkanie | `list_task_types(search="Spotkanie")` → id≈7 (1 pkt) |
| Konfiguracja środowiska | `list_task_types(search="Konfiguracja")` → id≈1081 (2 pkt) |
| Dokumentacja / artykuł | `list_task_types(search="Opracowanie")` → id≈1063 (2 pkt) |

### 2. Dobierz tagi

Dobierz tag na podstawie projektu/repozytorium:

| Projekt | Tag ID |
|---|---|
| ePW / ePW_web | 7 |
| LSI2021 | 3 |
| eMP / mcp-emp | 1 |
| AI / BA / nestjs | 5 |
| AZ / Asystent Zarządu | 87 |
| SharePoint | 4 |

### 3. Dry-run — pokaż podgląd

Przed stworzeniem pokaż użytkownikowi co zostanie zalogowane:

```
Typ:    Zmiana funkcjonalności (3 pkt)
Temat:  ePW - poprawka headerTitle w Finansowanie.jsx
Data:   2026-05-14
Tagi:   [ePW]
```

Zapytaj: **"Dodać? (tak / zmień opis / inny typ)"**

### 4. Stwórz i zakończ zadanie

```
emp_add_my_task(task_type_id=..., subject=..., tag_ids=[...])
→ task_id

emp_complete_task(task_id=task_id)
→ status: ZAKOŃCZONE
```

### 5. Backdatuj (jeśli data ≠ dziś)

Jeśli `target_date` jest inny niż dzisiejsza data:

```
emp_backdate_task(
  task_id=task_id,
  target_date="YYYY-MM-DD",
  set_completion_date=True
)
```

### 6. Potwierdź

Pokaż wynik:
```
✅ Zadanie #151600 dodane do EMP
   Temat:  ePW - poprawka headerTitle...
   Data:   2026-05-14
   Status: ZAKOŃCZONE
   Punkty: 3
```

## Zasady

- Zawsze rób dry-run przed stworzeniem — nigdy nie twórz bez potwierdzenia.
- Jeśli użytkownik nie podał daty — użyj dzisiejszej, ale zapytaj czy to na pewno dziś.
- Maksymalnie 1 zadanie per wywołanie tego skilla. Dla wielu zadań wywołaj skill wielokrotnie.
- Nie zmieniaj nr_cyklu — EMP przydziela go automatycznie.
