"""Deterministic corpus analysis for DeAIodorant."""

from .corpus import CorpusDocument, CorpusLoadResult, load_monthly_corpus
from .surface import discourse_features, surface_features, title_features
from .syntax import dependency_features, read_conllu

__all__ = [
    "CorpusDocument",
    "CorpusLoadResult",
    "dependency_features",
    "discourse_features",
    "load_monthly_corpus",
    "read_conllu",
    "surface_features",
    "title_features",
]
