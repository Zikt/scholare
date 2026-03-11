# Contributing to Scholare

Thank you for your interest in contributing! Scholare is an open-source project and we welcome contributions of all kinds.

First off, thank you for considering contributing to Scholare! Dedicated open-source contributors like you make this tool better for researchers everywhere.

Please review the [ARCHITECTURE.md](ARCHITECTURE.md) document first. It comprehensively outlines the data flow, module responsibilities, and how to add new API sources to the search pipeline.

---

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/scholare.git
cd scholare
```

### 2. Set Up Development Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -e ".[dev]"
```

### 3. Set Up API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

---

## Development Workflow

### Running Tests

```bash
pytest
```

### Code Style

- Use **type hints** on all function signatures.
- Write **docstrings** for all public functions (NumPy style).
- Keep functions focused — one function, one job.
- Use `pathlib.Path` instead of `os.path` where possible.

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add Unpaywall API integration for better OA discovery
fix: handle missing DOI in Semantic Scholar response
docs: add arXiv search example to README
test: add unit tests for deduplication logic
```

---

## How to Contribute

### 🐛 Bug Reports

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your Python version and OS

### 💡 Feature Requests

Check the [ROADMAP.md](ROADMAP.md) first — your idea might already be listed. If not, open an issue describing the feature and why it would be useful.

### 🔧 Pull Requests

1. Create a branch from `main`: `git checkout -b feat/my-feature`
2. Make your changes
3. Add tests if applicable
4. Run `pytest` to make sure everything passes
5. **Update Documentation**: Modify `CHANGELOG.md`, `ROADMAP.md` (if taking a planned item), and `README.md` or `docs/` if appropriate.
6. Open a PR with a clear description of what you changed and why, checking off the PR template boxes.

### 📡 Adding New API Integrations

We're especially interested in contributions that add new data sources. See [ROADMAP.md](ROADMAP.md) for the list. When adding an API:

1. Add the client function(s) to `scholare/api.py` (or a new module if it's large)
2. Make it **optional** — the tool should work without the new API key
3. Add the API key to `.env.example` with a comment explaining where to get it
4. Update `config.py` to load the new key
5. Add tests that don't require a live API key (mock the responses)
6. Update README with setup instructions

---

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
