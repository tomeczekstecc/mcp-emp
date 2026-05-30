## Contributing

### Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must have a structured prefix:

```
<type>(<scope>): <short summary>
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`.

Examples:

```
feat(auth): add sign-in page with TanStack Form
fix(api): handle empty response from applications endpoint
chore(deps): upgrade shadcn/ui to latest
```

Keep the summary short (under 72 characters), written in the imperative mood, and lowercase after the colon.

### Pull requests

- Open a PR for every change — do not push directly to `master`.
- At least one review approval is required before merging.
- Keep PRs focused. One logical change per PR makes review faster and reverts cleaner.
- Make sure `pnpm lint` passes before requesting review. Run `pnpm build` when your change touches route structure, types, or API integration.
- Address all review comments before merging. Resolve threads you have acted on; leave threads open if you need a follow-up from the reviewer.

### Branch naming

Use a short, descriptive name prefixed with the work type:

```
feat/sign-in-page
fix/api-error-fallback
chore/upgrade-deps
```
