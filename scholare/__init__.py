"""
Scholare — A general-purpose literature review pipeline.

Search Google Scholar, enrich results with Semantic Scholar metadata,
download open-access PDFs, and generate structured research notes.
"""

__version__ = "1.0.0"

from .config import load_config
from .pipeline import run_pipeline

__all__ = ["load_config", "run_pipeline", "__version__"]
