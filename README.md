# 📚 Scholare — Automated Literature Review Pipeline

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

An end-to-end, config-driven Python tool that **searches academic literature**, **downloads papers**, and **generates structured research notes** — ready to plug into any research topic.

> **🚀 Try it instantly — no installation required!**
> 
> [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zikt/scholare/blob/main/examples/cloud_notebook_template.ipynb)
>
> Click the badge above to run Scholare directly in your browser via Google Colab.

---

## ✨ What It Does

1. **Searches Free APIs** via [OpenAlex](https://openalex.org) natively, along with preprint servers like arXiv and bioRxiv/medRxiv.
2. **Enriches every result** through [Semantic Scholar](https://www.semanticscholar.org/product/api) — abstracts, TLDRs, DOIs, code/data hints. (Falls back to DOI lookups for highest accuracy).
3. **Discovers Open-Access Links** dynamically using the [Unpaywall API](https://unpaywall.org/).
4. **Categorizes papers** using configurable keyword rules.
5. **Downloads open-access PDFs** into a local folder (with a `--no-download` CLI override).
6. **Generates visualizations** — category distribution, open-access status, citation histogram, year timeline.
7. **Produces structured Markdown research notes** — executive summary, taxonomy, top-cited, per-category breakdown with TLDRs, embedded charts, full paper index.
8. **Compares runs** — pass a previous CSV to isolate newly discovered papers.

---

## 🛠️ Setup

### 1. Prerequisites

- **Python 3.10+**
- *(Optional)* A **Semantic Scholar API key** — [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api) (Highly recommended to avoid rate limits).

### 2. Install

**From source (recommended for now):**

```bash
git clone https://github.com/OWNER/scholare.git
cd scholare
python -m venv venv

# Activate
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

pip install -e .
```

**Eventually via PyPI:**

```bash
pip install scholare
```

### 3. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env`:

```
S2_API_KEY=your_actual_semantic_scholar_key
UNPAYWALL_EMAIL=your_email@example.com
```

### 4. Create Your Config

```bash
cp config_example.json my_config.json
```

Edit `my_config.json`:

```json
{
  "query": "your search query here",
  "limit": 30,
  "output_dir": "./my_output",
  "categories": {
    "Category A": ["keyword1", "keyword2"],
    "Other": []
  },
  "default_category": "Other",
  "download_pdfs": true,
  "sources": ["openalex", "arxiv", "biorxiv"]
}
```

| Field | Description |
|-------|-------------|
| `query` | Search string (mapped appropriately across OpenAlex and preprints) |
| `limit` | Max number of papers to retrieve *per API source* |
| `output_dir` | Base output directory (subfolders auto-named by date + terms) |
| `categories` | Category name → keyword list for paper classification |
| `default_category` | Fallback when no keywords match |
| `download_pdfs` | Set `false` to skip PDF downloading by default |
| `sources` | (Optional) List of sources to query. Available: `openalex`, `arxiv`, `biorxiv` |

---

## 🚀 Usage

### CLI

```bash
# Run the pipeline
scholare --config my_config.json

# Skip downloading PDFs (overrides config)
scholare --config my_config.json --no-download

# Compare with a previous run
scholare --config my_config.json --previous-csv ./old_output/results.csv
```

### Programmatic & Cloud Notebooks (Colab / Kaggle)

> **⚡ Zero-install quick start** — Run Scholare directly in your browser!
>
> [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/zikt/scholare/blob/main/examples/cloud_notebook_template.ipynb)
>
> No Python setup, no terminal, no installation. Just click and run.

You can also install the package manually in any cloud notebook:
Install the package directly from GitHub:
```bash
!pip install git+https://github.com/zikt/scholare.git
```

Then, you can define your configuration natively in Python and pass it to the pipeline:

```python
import os
from scholare.config import load_config
from scholare.pipeline import run_pipeline

# Setting API Keys:
# Method A: Direct Injection
# os.environ["S2_API_KEY"] = "your_key_here"
# os.environ["UNPAYWALL_EMAIL"] = "your_email@example.com"

# Method B: Secure Colab Secrets (Recommended)
# from google.colab import userdata
# os.environ["S2_API_KEY"] = userdata.get('S2_API_KEY')

# Define config as a dictionary mapping
my_config = {
    "query": "federated learning",
    "limit": 10,
    "output_dir": "./output",
    "categories": {"Privacy": ["dp"]},
    "default_category": "Other",
    "download_pdfs": False
}

config_obj = load_config(my_config)
df = run_pipeline(config_obj)

print(f"Found {len(df)} papers")
```

> [!TIP]
> See the full interactive [Cloud Notebook Template (`examples/cloud_notebook_template.ipynb`)](examples/cloud_notebook_template.ipynb) to get started immediately!

---

## 📁 Output Structure

Each run creates a descriptive subfolder:

```
output/
└── 2026-02-25_EEG_BCI_melanin_bias/
    ├── papers/                        # Downloaded open-access PDFs
    ├── visualizations/                # PNG charts
    │   ├── category_distribution.png
    │   ├── open_access_status.png
    │   ├── citation_distribution.png
    │   └── year_distribution.png
    ├── research_notes.md              # Structured Markdown summary
    ├── results.csv                    # Raw data
    └── new_discoveries.csv            # (if --previous-csv was used)
```

---

## 📝 Example Configs

See the [`examples/`](examples/) directory for ready-to-use configs:

- [`eeg_bias_config.json`](examples/eeg_bias_config.json) — EEG/BCI bias research
- [`federated_learning_config.json`](examples/federated_learning_config.json) — Federated learning in healthcare

---

## 🗺️ Roadmap

Scholare is actively growing. See [ROADMAP.md](ROADMAP.md) for planned features including:

- 📡 **More APIs** — OpenAlex, Unpaywall, arXiv, Crossref, PubMed, CORE
- 📤 **Export** — BibTeX/RIS for Zotero & Mendeley
- 🔗 **Integration** — Zotero/Mendeley library sync
- 🌐 **Chrome extension** — one-click literature searches
- 📊 **Analysis** — citation networks, clustering, PRISMA diagrams
- 🎨 **UX** — rich CLI, interactive HTML dashboards

Contributions welcome! Pick any item from the roadmap.

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

---

## ⚠️ Limitations

- Only **open-access PDFs** can be downloaded. Paywalled papers are noted with links.
- **Semantic Scholar** without a key is limited, which might slow down enrichment on large searches. Adding an `S2_API_KEY` solves this.
- **Categorization** is keyword-based (heuristic, not an AI classifier).
- **bioRxiv searching** uses the Crossref endpoint simulating a search, leading to slightly different handling.

---

## 📦 Package Structure

```
scholare/
├── __init__.py          # Public API 
├── __main__.py          # CLI entry point
├── config.py            # Config loader
├── api.py               # OpenAlex, preprint, Unpaywall, Semantic Scholar clients
├── pipeline.py          # Main orchestration
├── downloader.py        # PDF downloading
├── notes.py             # Markdown research notes generator
├── visualizations.py    # Chart generation
└── utils.py             # Categorization & comparison helpers
```

---

## 📄 License

[MIT](LICENSE) — use it, fork it, build on it.
