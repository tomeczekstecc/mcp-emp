---
name: missspell-checker
description: Scans UI-visible text in React/Next.js components for Polish spelling errors, including words missing Polish diacritics (ą, ę, ó, ś, ź, ż, ć, ń, ł). Use when the user wants to audit Polish copy in the app, says "check spelling", "check Polish text", "find typos", or "check diacritics".
argument-hint: run|check
---

# Polish Spell Checker

Scan all UI-visible text in `src/` for Polish spelling mistakes, including words where Polish diacritical characters are missing or incorrect.

## Scope

Only check **user-visible strings** — what appears in the UI:
- JSX text nodes and string literals in `.tsx` / `.jsx` files
- String props that render as labels, placeholders, titles, descriptions, errors, tooltips, breadcrumbs, buttons, headings (`label`, `placeholder`, `title`, `description`, `alt`, `aria-label`, `aria-description`, `content`, `emptyState`, `noResultsState`, `children` when a plain string)
- String arrays used as options or messages

**Skip:**
- Code identifiers, variable names, import paths, class names, CSS values
- Comments and `console.*` calls
- English words and technical terms
- `data-*` attributes and non-display props

## What to check

### 1. Missing Polish diacritics

Flag words where a Latin base letter is used instead of the correct Polish character. Common patterns:

| Wrong | Correct Polish |
|-------|---------------|
| a → ą | np. "zadanie" → OK, but "mam" vs "mąm" — check context |
| e → ę | "nie" → OK, "wiecej" → "więcej" |
| o → ó | "rog" → "róg", "moc" → OK |
| s → ś | "srodek" → "środek", "wies" → "wieś" |
| z → ź/ż | "zrodlo" → "źródło", "juz" → "już" |
| c → ć | "wiec" → "więc" (check context), "noc" → OK |
| n → ń | "kon" → "koń", "dzien" → "dzień" |
| l → ł | "ladny" → "ładny", "byl" → "był" |

Focus on high-confidence cases where the base-Latin version does not form a valid Polish word.

### 2. Common Polish misspellings

Check for frequent errors:
- Incorrect soft/hard consonant pairs: `rz` vs `ż`, `ch` vs `h`, `u` vs `ó`
- Wrong verb endings: `-ię` vs `-ie`, `-ią` vs `-ia`
- Common word-level typos in the codebase strings

### 3. Mixed-language inconsistency

Flag strings that mix Polish and English in a way that looks unintentional (e.g. one button says "Anuluj", another says "Cancel" in the same flow).

## Mode: $ARGUMENTS

**check (default)** — report only, no edits:
1. List each file with findings
2. For each finding show: file path, line number, the string found, and the suggested correction
3. Group by file
4. Show a summary count at the end

**run** — interactive fix mode:
1. First run the full check and display all findings numbered
2. Ask: "Which items would you like me to fix? (enter numbers like 1,3,5 or 'all' or 'none')"
3. Wait for user confirmation before editing anything
4. Apply only the selected fixes
5. Report what was changed

## Output format

```
## Polish Spell Check — <mode>

### src/components/foo/bar.tsx
- Line 12: "wiecej opcji" → "więcej opcji"
- Line 34: "Ladowanie..." → "Ładowanie..."

### src/app/(app)/wizard-demo/page.tsx
- Line 8: "Zadania (brak)" → OK  ← only list issues, not OKs

---
Summary: X issues found across Y files.
```

## Rules

- Be conservative — only flag high-confidence misspellings. Do not flag ambiguous cases.
- Do not alter English words, variable names, or technical strings.
- Preserve surrounding JSX structure exactly when fixing; only change the string content.
- If unsure whether a word is intentional (e.g. a proper noun or brand name), list it as a warning, not an error.
