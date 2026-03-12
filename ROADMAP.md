# Roadmap

This is the public feature roadmap for Scholare. Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for how to get started.

Items marked with ✅ are complete. Items with a contributor's name are in progress.

---

## v1.0 — Core Pipeline ✅

- ✅ Google Scholar search via SerpAPI (with pagination)
- ✅ Semantic Scholar enrichment (abstracts, TLDRs, open-access URLs, DOIs)
- ✅ Config-driven pipeline (any research topic)
- ✅ Keyword-based paper categorization
- ✅ Open-access PDF downloading
- ✅ Visualizations (category, open-access, citation, year charts)
- ✅ Structured Markdown research notes
- ✅ Run-to-run comparison (new paper detection)
- ✅ Auto-named output folders (`<date>_<terms>/`)
- ✅ CLI entry point (`scholare --config ...`)

---

## v1.1 — Better Data Sources

> **Goal**: More APIs = better coverage, fewer missed papers, reduced SerpAPI cost.

- ✅ **Unpaywall integration** — DOI-based open-access PDF discovery (free, no key, 55M+ articles)
- ✅ **OpenAlex search** — free alternative to Google Scholar (250M+ works, no per-search cost)
- ✅ **arXiv search** — preprints in CS, ML, physics, math (free, no key)
- [ ] **Crossref enrichment** — reference lists, funder info via DOI (free, no key)
- [ ] **PubMed search** — biomedical literature (free key)
- [ ] **CORE search** — institutional repository papers (free key)
- [ ] **Multi-source search** — search multiple APIs in parallel, merge and deduplicate

---

## v1.2 — Export & Integration

> **Goal**: Fit into existing research workflows.

- [ ] **BibTeX export** — generate `.bib` files for LaTeX/Overleaf
- [ ] **RIS export** — generate `.ris` files for reference managers
- [ ] **Zotero integration** — import results directly into Zotero libraries
- [ ] **Mendeley integration** — import results directly into Mendeley
- [ ] **CSV/Excel improvements** — richer export with all metadata fields

---

## v1.3 — Smarter Analysis

> **Goal**: Go beyond keyword matching.

- [ ] **Citation network analysis** — find influential papers through reference chains
- [ ] **Paper deduplication** — fuzzy title matching across searches and runs
- [ ] **Keyword co-occurrence** — discover subtopics from abstract analysis
- [ ] **Abstract similarity clustering** — TF-IDF or embedding-based grouping
- [ ] **PRISMA flow diagram** — auto-generate the standard systematic review diagram
- [ ] **Trend analysis** — track publication volume and citation trends over time
- ✅ **Relevance scoring** — keyword-heuristic scoring AND optional semantic embedding-based ranking limit threshold
- [ ] **AI keyword generation** — auto-generate Boolean queries and category keywords from a plain-language research question
- [ ] **Performance benchmarking** — track memory usage, API call timing, and throughput per pipeline stage
- ✅ **Documentation Website** — full user and developer docs via MkDocs and GitHub Pages

---

## v1.4 — User Experience

> **Goal**: Professional, polished tool.

- [ ] **Rich CLI output** — progress bars, colored output, time estimates via `rich`
- [ ] **Interactive HTML dashboard** — Plotly/Dash-based visual exploration
- [ ] **Watch mode** — periodic re-runs with notifications for new papers
- [ ] **Multi-query configs** — run several related queries in one config
- [ ] **Verbose/quiet modes** — control output detail level
- [ ] **Resume support** — restart from last checkpoint if a run is interrupted
- [ ] **Collect Feedback & Reviews** — enable GitHub Discussions for community reviews and embed a feedback form link in docs/CLI for structured ratings.

---

## v2.0 — Browser & Platform

> **Goal**: Reach beyond the command line.

- [ ] **Chrome extension** — one-click literature search from any webpage
- [ ] **Firefox extension** — same as Chrome, for Firefox users
- [ ] **Web UI** — browser-based interface for non-technical users
- [ ] **REST API** — serve as a backend for other tools
- [ ] **Jupyter integration** — widget-based interface for notebooks

---

## v2.5 — Retrieval-Augmented Generation (RAG)

> **Goal**: Turn the static downloaded PDF folder into an interactive, conversational research assistant. The chosen architecture is a **Serverless Open Source API (e.g., Groq, Together AI)**.
> **Reasoning**: This provides the speed and quality of open-source models (like Llama-3) without the prohibitive $150+/month cost of renting idle dedicated GPUs. You only pay fractions of a cent per token generated, allowing the service to scale cheaply while feeling free to the end user.

- [ ] **PDF Parsing Engine** — robust text extraction from multi-column academic PDFs (e.g., using `PyMuPDF` or `unstructured`).
- [ ] **Local Vector Store** — lightweight embedding storage (e.g., `ChromaDB` or `FAISS`) for semantic search across downloaded papers.
- [ ] **Serverless LLM Integration** — integrate with Inference APIs (e.g., Groq, Together AI) to generate answers using open-source weights (Llama-3/Mistral) cost-effectively.
- [ ] **Interactive CLI Chat** — a new command (e.g., `scholare-chat --folder output/xyz`) to ask natural language questions across the dataset.
- [ ] **Methodology & Data Extraction** — specialized prompts to automatically pull study limitations, participant demographics, or equipment used.

---

## Ideas & Wishlist

These are longer-term ideas. Open an issue to discuss or propose an implementation:

- LLM-powered summarization (optional, for users with API keys)
- Full-text PDF analysis (extract methods, results, limitations)
- Collaborative reviews (multiple reviewers, conflict resolution)
- Integration with Notion/Obsidian for note-taking workflows
- Docker image for easy deployment
- GitHub Actions template for scheduled literature monitoring

---

## Contributing

Pick any unchecked item, open an issue to claim it, and submit a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines. We especially welcome:

- **New API integrations** (see v1.1)
- **Export formats** (see v1.2)
- **Bug fixes and tests**
- **Documentation improvements**
