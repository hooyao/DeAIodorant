"""Command-line interface for deterministic Chinese corpus analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import FeatureConfigError, load_feature_config
from .corpus import CorpusValidationError
from .pipeline import FeaturePipelineError, extract_feature_matrix
from .stanza_backend import (
    SyntaxBackendError,
    annotate_corpus,
    download_stanza_model,
)
from .syntax import ConlluValidationError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deaiodorant-analysis",
        description="Extract deterministic non-LLM features from prepared Chinese corpora.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download = subparsers.add_parser(
        "download-syntax-model",
        help="Explicitly download the pinned Stanza Chinese syntax model.",
    )
    download.add_argument("--model-dir", type=Path, required=True)
    download.add_argument("--language", default="zh-hans")
    download.add_argument("--package", default="gsdsimp")

    annotate = subparsers.add_parser(
        "annotate",
        help="Create immutable CoNLL-U syntax annotations for a prepared corpus.",
    )
    annotate.add_argument("--corpus", type=Path, required=True)
    annotate.add_argument("--config", type=Path, required=True)
    annotate.add_argument("--model-dir", type=Path, required=True)
    annotate.add_argument("--output", type=Path, required=True)
    annotate.add_argument("--language", default="zh-hans")
    annotate.add_argument("--package", default="gsdsimp")
    annotate.add_argument("--device", choices=("cpu", "cuda"), default="cpu")

    extract = subparsers.add_parser(
        "extract",
        help="Write a self-describing numeric document-feature matrix.",
    )
    extract.add_argument("--corpus", type=Path, required=True)
    extract.add_argument("--config", type=Path, required=True)
    extract.add_argument("--annotations", type=Path)
    extract.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a subcommand and return a process exit status."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "download-syntax-model":
            download_stanza_model(
                model_dir=args.model_dir,
                language=args.language,
                package=args.package,
            )
            return 0
        if args.command == "annotate":
            config = load_feature_config(args.config)
            result = annotate_corpus(
                corpus_root=args.corpus,
                config=config,
                model_dir=args.model_dir,
                output_dir=args.output,
                language=args.language,
                package=args.package,
                device=args.device,
            )
        else:
            result = extract_feature_matrix(
                corpus_root=args.corpus,
                config_path=args.config,
                output_dir=args.output,
                annotation_dir=args.annotations,
            )
    except (
        FeatureConfigError,
        FeaturePipelineError,
        ConlluValidationError,
        CorpusValidationError,
        SyntaxBackendError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
