# Contributing

Thanks for helping improve M5 Resolver Substrate.

## Development workflow

1. Fork and create a feature branch.
2. Keep firmware changes minimal and protocol-safe.
3. Add/extend tests for host runtime changes.
4. Update documentation for user-visible behavior.
5. Open a pull request with test evidence.

## Local setup

### Host runtime

```bash
cd host
python -m venv .venv
. .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
pip install pytest
```

### Run tests

```bash
cd ..
pytest
```

### Optional pre-commit setup

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Commit quality checklist

- [ ] Intent protocol changes are documented.
- [ ] No breaking API changes without migration notes.
- [ ] New registry entries validated.
- [ ] Readability and naming are clear.
