# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **OpenAlex integration** — Replaced SerpAPI with OpenAlex for primary literature searches, eliminating paywalled rate limits.
- **Preprint server integration** — Added concurrent querying of arXiv and bioRxiv/medRxiv APIs.
- **Unpaywall API** — Added lookup capability to dynamically find open-access PDFs via DOI when native sources fail.
- **Smart deduplication** — Added pipeline layer to merge and deduplicate results across all new search engines.
- **CLI Flags** — Added `--no-download` flag to disable PDF saving without modifying the config file.

### Changed

- **Semantic Scholar search** — Now prioritizes searching by DOI directly to ensure maximum accuracy during metadata enrichment.
- **Config requirements** — `serp_api_key` is no longer required. `unpaywall_email`, `use_arxiv`, and `use_biorxiv` options added.

## [1.0.0] — 2026-02-25

- **Google Scholar search** via SerpAPI with automatic pagination
- **Semantic Scholar enrichment** — abstracts, TLDRs, open-access URLs, DOIs, code/data hints
- **Config-driven pipeline** — JSON config for any research topic
- **Keyword-based categorization** with configurable category → keyword mapping
- **Open-access PDF downloading** with filename sanitization
- **Visualizations** — category pie chart, open-access bar chart, citation histogram, year timeline
- **Structured Markdown research notes** — executive summary, taxonomy, top-cited, per-category breakdown, full index
- **Run comparison** — detect new papers vs. a previous CSV
- **Auto-named output folders** — `<date>_<search_terms>/` for easy organization
- **CLI entry point** — `scholare --config <path>`
- **API key management** via `.env` file
