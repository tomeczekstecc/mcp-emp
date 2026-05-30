---
name: tanstack-form
description: Use when building or refactoring React forms with TanStack Form in this repository, especially in `apps/web` when form state, Zod validation, accessible field wiring, error rendering, array fields, or non-input controls like Select, Checkbox, Radio Group, and Switch need repo-aligned patterns.
---

# TanStack Form

## Overview

Use this skill to implement headless, typed forms in `apps/web` with `@tanstack/react-form` and Zod. Keep the form API usage explicit, preserve accessibility, and match the repo's existing UI primitives instead of inventing a parallel form abstraction.

## Workflow

1. Read the feature's existing route, form component, and shared UI primitives before changing structure.
2. Use `$context7-first` if TanStack Form, Zod, or input-library APIs are version-sensitive or unclear.
3. Define the form schema once with Zod and keep `defaultValues` aligned with that shape.
4. Create the form with `useForm`, attach validators intentionally, and keep `onSubmit` small.
5. Render fields with `form.Field` and wire `value`, `onBlur`, and `onChange` directly from the field object.
6. Derive invalid state from `field.state.meta.isTouched` and `field.state.meta.isValid`.
7. Add `data-invalid` on the field wrapper and `aria-invalid` on the interactive control.
8. Use focused validation and build checks in `apps/web` after changes.

## Rules

- Prefer `form.Field` close to the rendered control instead of wrapping everything in custom helpers too early.
- Keep field names stable and explicit so nested and array paths remain readable.
- Reuse shared UI primitives such as `Input`, `Textarea`, `Select`, `Checkbox`, `RadioGroup`, and `Switch`.
- Keep validation mode intentional. Use `onSubmit` by default unless the UX clearly needs `onBlur` or `onChange`.
- Render errors next to the owning control, not in a detached global list unless the feature requires both.
- Use array helpers like `pushValue` and `removeValue` for repeated fields instead of manual cloning logic.
- Avoid duplicating schema types or creating ad hoc frontend-only field contracts when Zod already defines the shape.

## Core Pattern

```tsx
const form = useForm({
  defaultValues: {
    title: "",
  },
  validators: {
    onSubmit: formSchema,
  },
  onSubmit: async ({ value }) => {
    // keep side effects here
  },
})
```

```tsx
<form.Field
  name="title"
  children={(field) => {
    const isInvalid =
      field.state.meta.isTouched && !field.state.meta.isValid

    return (
      <Field data-invalid={isInvalid}>
        <FieldLabel htmlFor={field.name}>Title</FieldLabel>
        <Input
          id={field.name}
          name={field.name}
          value={field.state.value}
          onBlur={field.handleBlur}
          onChange={(e) => field.handleChange(e.target.value)}
          aria-invalid={isInvalid}
        />
        {isInvalid && <FieldError errors={field.state.meta.errors} />}
      </Field>
    )
  }}
/>
```

## Reference

Read [field-patterns.md](references/field-patterns.md) when you need concrete wiring for:

- input and textarea fields
- select, checkbox, radio group, and switch controls
- array fields and nested field paths
- reset behavior and validation mode choices

## Validation

- Run `npm run check-types` from `apps/web`.
- Run `npm run build` from `apps/web` when form structure or client boundaries changed.
