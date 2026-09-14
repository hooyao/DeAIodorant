"""Explicit, versioned Stanza annotation with deterministic settings."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import random
from pathlib import Path
from typing import Any

from .config import FeatureConfig
from .corpus import load_monthly_corpus


class SyntaxBackendError(RuntimeError):
    """Raised when syntax annotation cannot satisfy reproducibility requirements."""


PROCESSORS = "tokenize,pos,lemma,depparse"


def _load_stanza() -> Any:
    try:
        import stanza
    except ImportError as exc:
        raise SyntaxBackendError(
            'Stanza is not installed; install the optional dependency with "pip install -e .[syntax]"'
        ) from exc
    return stanza


def download_stanza_model(
    *,
    model_dir: Path,
    language: str = "zh-hans",
    package: str = "gsdsimp",
) -> None:
    """Perform the only network-enabled step in the syntax workflow."""

    stanza = _load_stanza()
    model_dir.mkdir(parents=True, exist_ok=True)
    stanza.download(
        language,
        model_dir=str(model_dir),
        package=package,
        processors=PROCESSORS,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_fingerprint(model_dir: Path, language: str) -> tuple[str, int]:
    candidates = []
    language_dir = model_dir / language
    if language_dir.is_dir():
        candidates.extend(path for path in language_dir.rglob("*") if path.is_file())
    resources_path = model_dir / "resources.json"
    if resources_path.is_file():
        candidates.append(resources_path)
    candidates = sorted(set(candidates))
    if not candidates:
        raise SyntaxBackendError(
            f"No downloaded model files found for {language!r} under {model_dir}"
        )
    digest = hashlib.sha256()
    for path in candidates:
        relative = path.relative_to(model_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest(), len(candidates)


def _configure_determinism(seed: int, device: str) -> Any:
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    if device == "cuda":
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    try:
        import numpy
        import torch
    except ImportError as exc:
        raise SyntaxBackendError("Stanza runtime dependencies are incomplete") from exc
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    if device == "cuda":
        if not torch.cuda.is_available():
            raise SyntaxBackendError("CUDA was requested but is not available")
        torch.cuda.manual_seed_all(seed)
    else:
        torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    return torch


def _conllu_value(value: Any) -> str:
    if value is None or value == "":
        return "_"
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def _document_to_conllu(document: Any, *, doc_id: str) -> str:
    lines: list[str] = []
    for sentence_index, sentence in enumerate(document.sentences, start=1):
        lines.append(f"# sent_id = {doc_id}-{sentence_index}")
        for word in sentence.words:
            lines.append(
                "\t".join(
                    [
                        _conllu_value(word.id),
                        _conllu_value(word.text),
                        _conllu_value(word.lemma),
                        _conllu_value(word.upos),
                        _conllu_value(word.xpos),
                        _conllu_value(word.feats),
                        _conllu_value(word.head),
                        _conllu_value(word.deprel),
                        _conllu_value(word.deps),
                        _conllu_value(word.misc),
                    ]
                )
            )
        lines.append("")
    return "\n".join(lines)


def _prepare_output_directory(path: Path) -> Path:
    path = path.resolve()
    if path.exists() and any(path.iterdir()):
        raise SyntaxBackendError(
            f"Annotation output is not empty; annotations are immutable: {path}"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _package_versions() -> dict[str, str]:
    packages = ("emoji", "networkx", "numpy", "protobuf", "stanza", "torch")
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def annotate_corpus(
    *,
    corpus_root: Path,
    config: FeatureConfig,
    model_dir: Path,
    output_dir: Path,
    language: str = "zh-hans",
    package: str = "gsdsimp",
    device: str = "cpu",
) -> dict[str, Any]:
    """Create one immutable CoNLL-U file per corpus document and a model manifest."""

    if device not in {"cpu", "cuda"}:
        raise SyntaxBackendError("device must be 'cpu' or 'cuda'")
    stanza = _load_stanza()
    torch = _configure_determinism(config.annotation_seed, device)
    corpus = load_monthly_corpus(
        corpus_root,
        pre_end_exclusive=config.pre_end_exclusive,
        post_start_inclusive=config.post_start_inclusive,
    )
    model_dir = model_dir.resolve()
    model_fingerprint, model_file_count = _model_fingerprint(model_dir, language)
    output_dir = _prepare_output_directory(output_dir)

    pipeline_options: dict[str, Any] = {
        "dir": str(model_dir),
        "lang": language,
        "package": package,
        "processors": PROCESSORS,
        "use_gpu": device == "cuda",
        "verbose": False,
    }
    if hasattr(stanza, "DownloadMethod"):
        pipeline_options["download_method"] = stanza.DownloadMethod.NONE
    nlp = stanza.Pipeline(**pipeline_options)

    file_hashes: dict[str, str] = {}
    context = torch.inference_mode()
    with context:
        for index, document in enumerate(corpus.documents, start=1):
            print(
                f"[annotate] {index}/{len(corpus.documents)} {document.doc_id}",
                flush=True,
            )
            parsed = nlp(document.text)
            if not parsed.sentences:
                raise SyntaxBackendError(f"No sentences produced for {document.doc_id}")
            output_path = output_dir / f"{document.doc_id}.conllu"
            output_path.write_text(
                _document_to_conllu(parsed, doc_id=document.doc_id),
                encoding="utf-8",
                newline="\n",
            )
            file_hashes[output_path.name] = _sha256_file(output_path)

    manifest = {
        "annotation_files": dict(sorted(file_hashes.items())),
        "corpus_fingerprint": corpus.corpus_fingerprint,
        "document_count": len(corpus.documents),
        "parser": {
            "device": device,
            "language": language,
            "model_file_count": model_file_count,
            "model_fingerprint": model_fingerprint,
            "name": "stanza-universal-dependencies",
            "package": package,
            "package_versions": _package_versions(),
            "processors": PROCESSORS.split(","),
            "seed": config.annotation_seed,
            "version": importlib.metadata.version("stanza"),
        },
        "python_version": platform.python_version(),
        "schema_version": "deaiodorant-annotations-1.0",
    }
    (output_dir / "annotation_manifest.json").write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest
