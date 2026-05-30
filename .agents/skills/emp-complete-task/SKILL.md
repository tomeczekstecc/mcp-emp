---
name: emp-complete-task
description: Find an open EMP task and mark it as completed. Use whenever the user says "zakończ zadanie w EMP", "oznacz jako ukończone", "complete EMP task", "finish task", "zamknij zadanie", "skończyłem zadanie", "mark done in EMP", or wants to close/finish a specific task by ID or description. Also triggers on "zakończ #ID", "zamknij zadanie o nazwie X".
---

# EMP — Zakończ zadanie

Skill znajduje otwarte zadanie i oznacza je jako ZAKOŃCZONE.

## Workflow

### 1. Zidentyfikuj zadanie

Użytkownik może podać:
- **ID zadania** (np. `#151560`) → użyj `emp_get_task(task_id=...)`
- **Fragment opisu** → `emp_list_my_tasks(scope="active", search="...")` i pokaż listę
- **Brak informacji** → `emp_list_my_tasks(scope="active")` i wypisz otwarte zadania

Pokaż znalezione zadanie:
```
Zadanie #151560
  Temat:  ePW - anulowanie Karty Projektu
  Status: REALIZOWANE
  Typ:    Nowa funkcjonalność (8 pkt)
  can_complete: true
```

### 2. Sprawdź wymagania

Z `get_task.permissions`:
- `can_complete: false` → powiedz dlaczego (np. status W_EDYCJI) i zatrzymaj
- `task_type.requires_time: true` → zapytaj o czas HH:MM
- `task_type.requires_quantity: true` → zapytaj o ilość

### 3. Dry-run — pokaż tranzycję

```
emp_complete_task(task_id=..., dry_run=True)
```

Pokaż:
```
Tranzycja: REALIZOWANE → ZAKOŃCZONE
           (lub → DO_OCENY jeśli typ wymaga oceny)
```

Zapytaj: **"Zakończyć?"**

### 4. Zakończ

```
emp_complete_task(task_id=..., time="HH:MM", quantity=N)
```

### 5. Potwierdź

```
✅ Zadanie #151560 zakończone
   Nowy status: ZAKOŃCZONE
   Punkty: 8
```

## Zasady

- Zawsze sprawdź `can_complete` przed próbą zakończenia.
- Jeśli status to `DO_OCENY` — zakończenie możliwe, powiedz użytkownikowi że trafia do managera.
- Nie zamykaj zadań w W_EDYCJI — zaproponuj najpierw `emp_start_task`.
