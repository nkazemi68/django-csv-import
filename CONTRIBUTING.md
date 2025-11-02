# Contributing

This project follows **Conventional Commits** (semantic commit messages).

Example commit messages:
- `feat(imports): add CSV import service`
- `fix(api): validate missing isbn`
- `chore(ci): add GH Actions workflow`

**For users:** you do not need to install/use Commitizen. The above is for contributors only.

## Hooks
- Developers are encouraged to enable `.githooks` via:

```bash
git config core.hooksPath .githooks
```

## Running tests
- From repo root:
```bash
cd src
venv\Scripts\activate #windows
pip install -r requirements.txt
pytest
```
