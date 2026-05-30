# TanStack Form Field Patterns

Use this file when the task needs concrete control wiring beyond the overview in `SKILL.md`.

## Schema And Form Setup

Define the schema with Zod and keep `defaultValues` in the same shape.

```tsx
const formSchema = z.object({
  title: z.string().min(5).max(32),
  description: z.string().min(20).max(100),
})

const form = useForm({
  defaultValues: {
    title: "",
    description: "",
  },
  validators: {
    onSubmit: formSchema,
  },
  onSubmit: async ({ value }) => {
    // submit side effects
  },
})
```

Validation modes:

- `onSubmit`: safest default for new forms
- `onBlur`: use when users need earlier feedback without validating every keystroke
- `onChange`: use only when frequent validation feedback is clearly helpful

## Invalid State Pattern

Use the same invalid calculation across controls.

```tsx
const isInvalid =
  field.state.meta.isTouched && !field.state.meta.isValid
```

Apply:

- `data-invalid={isInvalid}` on the field wrapper
- `aria-invalid={isInvalid}` on the interactive element
- `<FieldError errors={field.state.meta.errors} />` near the control

## Input

```tsx
<form.Field
  name="username"
  children={(field) => {
    const isInvalid =
      field.state.meta.isTouched && !field.state.meta.isValid

    return (
      <Field data-invalid={isInvalid}>
        <FieldLabel htmlFor={field.name}>Username</FieldLabel>
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

## Textarea

Use the same pattern as `Input`, but wire `Textarea` instead.

## Select

Use `value={field.state.value}` and `onValueChange={field.handleChange}` on `Select`. Put `aria-invalid` on `SelectTrigger`.

## Checkbox

For a single checkbox, wire `checked={field.state.value}` and `onCheckedChange={field.handleChange}`.

For checkbox arrays:

- set `mode="array"` on the parent field
- use `field.pushValue(item)` to add checked values
- use `field.removeValue(index)` to remove unchecked values
- add `data-slot="checkbox-group"` on the checkbox `FieldGroup` when local styling expects it

## Radio Group

Use `value={field.state.value}` and `onValueChange={field.handleChange}` on `RadioGroup`. Put `aria-invalid` on `RadioGroupItem`.

## Switch

Use `checked={field.state.value}` and `onCheckedChange={field.handleChange}` on `Switch`.

## Array Fields

Use `mode="array"` on the parent field and bracket notation for nested items such as `emails[${index}].address`.

Common operations:

- `field.pushValue({ address: "" })`
- `field.removeValue(index)`

Use nested `form.Field` calls for each array item so validation and touched state stay local to the subfield.

## Reset

Use `form.reset()` to restore `defaultValues`.
