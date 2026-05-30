---
name: emp-commit-and-log
description: Commit and push code changes AND automatically create a matching EMP task for the work. Use whenever the user says "commit i zaloguj do EMP", "zapisz i dodaj zadanie", "commit with EMP task", "wyślij i zaloguj", "push and log", "commit + EMP", "zatwierdź i wpisz do ewidencji", or any request combining git commit with EMP task logging. This is the main automation skill for daily developer workflow.
---

# Git Commit + EMP Task — automatyczny workflow

Skill commituje zmiany w git ORAZ tworzy odpowiadające zadanie w EMP.
Łączy `git-add-push` z `emp-log-task` w jeden spójny przepływ.

## Workflow

### 1. Przeanalizuj zmiany w repo

Wykonaj równolegle:

```bash
git status
git diff --stat
git log --oneline -5
```

Z analizy wyciągnij:
- **Co zostało zmienione** (pliki, moduły, funkcje)
- **Jaki typ pracy** (feature / fix / refactor / docs / config)
- **Jakiego projektu dotyczy** (ePW, LSI2021, mcp-emp, BA, itp.)

### 2. Zaproponuj commit message i zadanie EMP

Pokaż użytkownikowi **obie** propozycje jednocześnie:

```
📝 GIT COMMIT
   feat(ePW): add project card section K - attachments management

📋 EMP ZADANIE
   Typ:   Nowy element funkcjonalności (3 pkt)  [id=26]
   Temat: ePW - karta projektu: sekcja K zarządzanie załącznikami
   Data:  2026-05-30 (dziś)
   Tagi:  [ePW]
```

Zapytaj: **"Zatwierdź? Możesz edytować opis lub zmienić typ zadania."**

### 3. Dopasuj typ EMP do rodzaju pracy git

| Typ commita | Sugerowany typ EMP |
|---|---|
| `feat:` duży moduł / nowa strona | Nowa funkcjonalność (27, 8 pkt) |
| `feat:` nowy komponent / endpoint | Nowy element funkcjonalności (26, 3 pkt) |
| `feat:` / `refactor:` zmiana zachowania | Zmiana funkcjonalności (49, 3 pkt) |
| `fix:` / poprawka | Drobna poprawka/zmiana (28, 2 pkt) |
| `test:` / `refactor:` | Zmiana funkcjonalności (49, 3 pkt) |
| `docs:` / `chore:` | Opracowanie artykułu/dokumentacji (1063, 2 pkt) |
| `chore:` konfiguracja / deploy | Konfiguracja środowiska (1081, 2 pkt) |
| Spotkanie / planowanie | Spotkanie (7, 1 pkt) |

### 4. Dopasuj tagi do repozytorium

Wykryj projekt z `git remote get-url origin` lub aktualnego katalogu:

| Repo / katalog | Tag EMP |
|---|---|
| `ePW_web`, `ePW` | ePW (id=7) |
| `Lsi2021web_win`, `lsi2021` | LSI2021 (id=3) |
| `eMP_web`, `mcp_emp`, `mcp-emp` | eMP (id=1) |
| `nestjs-nextjs`, `ba-trpc` | AI (id=5) |
| `mcp_az_sharepoint`, `sharepoint` | Sharepoint (id=4) |
| `eDrogi_web` | eDrogi (id=8) |

### 5. Wykonaj git commit i push

Po potwierdzeniu:

```bash
git add -A        # lub wskazane pliki
git commit -m "..."
git push
```

Jeśli push się nie uda (non-fast-forward) — zatrzymaj i zgłoś błąd. Nie force-push.

### 6. Stwórz i zakończ zadanie EMP

```
emp_add_my_task(
  task_type_id=...,
  subject="...",
  tag_ids=[...],
)
→ task_id

emp_complete_task(task_id=task_id)
→ ZAKOŃCZONE
```

### 7. Backdatuj jeśli data ≠ dziś

Jeśli użytkownik wskazał inną datę lub commit był wcześniej:

```
emp_backdate_task(
  task_id=task_id,
  target_date="YYYY-MM-DD",
  set_completion_date=True
)
```

### 8. Podsumuj wynik

```
✅ GIT   Commit abc1234 wypchnięty na origin/master
✅ EMP   Zadanie #151700 dodane i zakończone
         Temat: ePW - karta projektu sekcja K...
         Data:  2026-05-30 | Punkty: 3
```

## Warianty wywołania

| Co mówi użytkownik | Zachowanie |
|---|---|
| "commit i zaloguj" | Standardowy flow: commit + 1 zadanie EMP |
| "commit i zaloguj jako nowa funkcja" | Wymusza typ 27 (Nowa funkcjonalność) |
| "commit bez EMP" | Tylko git, pomiń EMP |
| "zaloguj bez commita" | Tylko EMP, pomiń git |
| "commit i zaloguj na 15 maja" | Git dziś, EMP backdated na 15-05 |
| "commit i zaloguj 3 zadania" | 1 commit, 3 osobne zadania EMP (wywołaj emp-log-task 3×) |

## Zasady

- **Zawsze dry-run przed akcją** — pokaż obie propozycje (git + EMP) razem.
- Jeśli working tree jest czysty — pomiń git, zaloguj tylko EMP.
- Jeden commit = jedno zadanie EMP (chyba że użytkownik prosi o więcej).
- Nie twórz zadania EMP jeśli commit nie powiedzie się.
- Zachowaj oryginalny język opisu: PL dla zadań EMP, EN dla commit messages.
- Nigdy nie force-push i nie bypass hooks.
