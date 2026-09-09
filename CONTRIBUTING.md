# Contributing

Open an issue before changing the canonical schema, label mapping, or paper manifests. Parser updates should include an offline fixture test and a one-page live smoke-test report without copyrighted page archives. Never commit credentials, downloaded benchmark media, checkpoints, or third-party dataset copies.

For development:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python -m ruff check src tests
```
