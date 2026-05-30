## Contributing

### Branch Naming

Use short, descriptive branch names prefixed by type:

```
feat/short-description
fix/short-description
chore/short-description
```

### Commit Messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must have a type prefix:

```
feat: add user profile page
fix: correct token expiry handling
chore: update dependencies
docs: clarify environment variable setup
```

Common types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`.

### Pull Requests

- Open a PR against `master` when your branch is ready for review.
- At least **one approving review** is required before merging.
- Keep PRs focused — one logical change per PR makes review faster.
- If your change affects setup steps, scripts, or environment variables, update the README in the same PR.
