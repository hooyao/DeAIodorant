"""Parse three exact review bodies with an installed CPU-only Stanza model."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deaiodorant.analysis.stanza_backend import (
    PROCESSORS,
    _configure_determinism,
    _document_to_conllu,
    _load_stanza,
    _model_fingerprint,
    _package_versions,
    _sha256_file,
)
from deaiodorant.refine.records import write_json

VERSION = "contrast-syntax-feasibility-1.0"
SEED = 20260914
ALIASES = ("doc-03", "doc-05", "doc-11")
PROTOCOL = ROOT / "docs/routes/compact-refiner/contrast-syntax-feasibility.md"
PACKETS = ROOT / "data/local/contrast-context-v1"


def deny_network(event: str, arguments: tuple) -> None:
    """Fail closed on Python socket operations during local model inspection."""
    if event in {"socket.connect", "socket.getaddrinfo", "socket.sendto"}:
        raise RuntimeError("Network operations are disabled for this experiment")


def serialize_document(parsed, text: str, alias: str) -> dict:
    """Retain complete parser fields and exact source alignment evidence."""
    sentences = []
    gaps = []
    issues = []
    cursor = 0
    for index, sentence in enumerate(parsed.sentences, 1):
        tokens = []
        for token in sentence.tokens:
            start, end = token.start_char, token.end_char
            valid = isinstance(start, int) and isinstance(end, int) and 0 <= start <= end <= len(text)
            source_text = text[start:end] if valid else None
            if not valid or source_text != token.text:
                issues.append({"sentence_id": index, "token_ids": list(token.id),
                               "kind": "token_source_alignment"})
            tokens.append({"ids": list(token.id), "text": token.text,
                           "start_char": start, "end_char": end,
                           "source_text": source_text, "fields": token.to_dict()})
        start = tokens[0]["start_char"] if tokens else None
        end = tokens[-1]["end_char"] if tokens else None
        valid = isinstance(start, int) and isinstance(end, int) and cursor <= start <= end <= len(text)
        source_text = text[start:end] if valid else None
        if valid:
            gaps.append({"start_char": cursor, "end_char": start, "text": text[cursor:start]})
            cursor = end
        else:
            issues.append({"sentence_id": index, "kind": "sentence_source_alignment"})
        words = []
        for word in sentence.words:
            fields = word.to_dict()
            word_start, word_end = word.start_char, word.end_char
            fields["start_char"] = word_start
            fields["end_char"] = word_end
            word_valid = (isinstance(word_start, int) and isinstance(word_end, int)
                          and 0 <= word_start <= word_end <= len(text))
            fields["source_text"] = text[word_start:word_end] if word_valid else None
            if not word_valid:
                issues.append({"sentence_id": index, "word_id": word.id,
                               "kind": "word_offset_unavailable"})
            elif fields["source_text"] != word.text:
                issues.append({"sentence_id": index, "word_id": word.id,
                               "kind": "word_source_alignment"})
            words.append(fields)
        sentences.append({"sentence_id": f"{alias}-s{index:03d}", "index": index,
                          "start_char": start, "end_char": end,
                          "source_text": source_text, "parser_text": sentence.text,
                          "parser_text_matches_source_slice": sentence.text == source_text,
                          "tokens": tokens, "words": words})
    gaps.append({"start_char": cursor, "end_char": len(text), "text": text[cursor:]})
    reconstructed = "".join(gap["text"] + (sentence["source_text"] or "")
                            for gap, sentence in zip(gaps, sentences)) + gaps[-1]["text"]
    return {"protocol": VERSION, "alias": alias, "human_gold": False,
            "source_characters": len(text), "source_linebreaks": text.count("\n"),
            "sentence_count": len(sentences),
            "token_count": sum(len(sentence["tokens"]) for sentence in sentences),
            "word_count": sum(len(sentence["words"]) for sentence in sentences),
            "source_reconstruction_exact": reconstructed == text,
            "offset_issues": issues, "source_gaps": gaps, "sentences": sentences}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models/stanza")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "data/local").resolve())
    if output.exists():
        raise ValueError("Use a new output directory")
    if os.environ.get("PYTHONHASHSEED") != str(SEED):
        environment = dict(os.environ, PYTHONHASHSEED=str(SEED), CUDA_VISIBLE_DEVICES="")
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
            env=environment, check=False,
        ).returncode
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    sys.addaudithook(deny_network)
    started = time.perf_counter()
    source_manifest = PACKETS / "manifest.json"
    expected_outputs = json.loads(source_manifest.read_text(encoding="utf-8"))["output_hashes"]
    inputs = {source_manifest.relative_to(ROOT).as_posix(): _sha256_file(source_manifest)}
    sources = {}
    for alias in ALIASES:
        for name in ("body.txt", "occurrences.json"):
            path = PACKETS / "packets" / alias / name
            actual = _sha256_file(path)
            if actual != expected_outputs[path.relative_to(PACKETS).as_posix()]:
                raise ValueError("Source packet hash mismatch")
            inputs[path.relative_to(ROOT).as_posix()] = actual
        body = PACKETS / "packets" / alias / "body.txt"
        sources[alias] = body.read_bytes().decode("utf-8")
    implementation_paths = [Path(__file__).resolve(), PROTOCOL,
                            ROOT / "src/deaiodorant/analysis/stanza_backend.py",
                            ROOT / "src/deaiodorant/refine/records.py"]
    implementation_hashes = {path.relative_to(ROOT).as_posix(): _sha256_file(path)
                             for path in implementation_paths}
    model_dir = args.model_dir.resolve()
    model_fingerprint, model_file_count = _model_fingerprint(model_dir, "zh-hans")
    model_paths = sorted([path for path in (model_dir / "zh-hans").rglob("*") if path.is_file()]
                         + [model_dir / "resources.json"])
    model_hashes = {path.relative_to(model_dir).as_posix(): _sha256_file(path) for path in model_paths}
    output.mkdir(parents=True)
    snapshot = output / "implementation-snapshot"
    snapshot.mkdir()
    for path in implementation_paths:
        (snapshot / path.name).write_bytes(path.read_bytes())
    progress_path = output / "run-state.json"
    state = {"protocol": VERSION, "pid": os.getpid(), "completed_documents": 0,
             "total_documents": len(ALIASES), "status": "loading_model", "counts": []}
    write_json(progress_path, state)
    print(json.dumps({"pid": os.getpid(), "completed_documents": 0, "total_documents": len(ALIASES)}), flush=True)
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        stanza = _load_stanza()
        torch = _configure_determinism(SEED, "cpu")
        torch.set_num_interop_threads(1)
        nlp = stanza.Pipeline(dir=str(model_dir), lang="zh-hans", package="gsdsimp",
                              processors=PROCESSORS, use_gpu=False, verbose=False,
                              download_method=stanza.DownloadMethod.NONE)
    counts = []
    with torch.inference_mode():
        for ordinal, alias in enumerate(ALIASES, 1):
            state.update(status="parsing", current_alias=alias)
            write_json(progress_path, state)
            print(json.dumps({"alias": alias, "document_index": ordinal, "total_documents": len(ALIASES)}), flush=True)
            document_started = time.perf_counter()
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                parsed = nlp(sources[alias])
            if not parsed.sentences:
                raise ValueError("Parser produced no sentences")
            data = serialize_document(parsed, sources[alias], alias)
            directory = output / alias
            directory.mkdir()
            (directory / "body.txt").write_bytes(sources[alias].encode("utf-8"))
            write_json(directory / "annotations.json", data)
            (directory / "annotations.conllu").write_text(
                _document_to_conllu(parsed, doc_id=alias), encoding="utf-8", newline="\n")
            count = {key: data[key] for key in ("alias", "source_characters", "source_linebreaks",
                                               "sentence_count", "token_count", "word_count",
                                               "source_reconstruction_exact")}
            count["offset_issue_count"] = len(data["offset_issues"])
            count["elapsed_seconds"] = round(time.perf_counter() - document_started, 3)
            counts.append(count)
            state.update(completed_documents=ordinal, counts=list(counts))
            write_json(progress_path, state)
            print(json.dumps({key: count[key] for key in ("alias", "sentence_count", "token_count", "word_count")}), flush=True)
    for name, expected in inputs.items():
        if _sha256_file(ROOT / name) != expected:
            raise ValueError("Source input changed during parsing")
    for name, expected in implementation_hashes.items():
        if _sha256_file(ROOT / name) != expected:
            raise ValueError("Implementation changed during parsing")
    for name, expected in model_hashes.items():
        if _sha256_file(model_dir / name) != expected:
            raise ValueError("Model changed during parsing")
    state.update(status="complete")
    write_json(progress_path, state)
    write_json(output / "manifest.json", {
        "protocol": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
        "command": "python experiments/contrast_syntax_feasibility.py --model-dir models/stanza --output-dir " + output.relative_to(ROOT).as_posix(),
        "input_hashes": inputs, "implementation_hashes": implementation_hashes,
        "model_hashes": model_hashes, "model_fingerprint": model_fingerprint,
        "model_file_count": model_file_count, "model_directory": str(model_dir),
        "parser": {"name": "stanza", "language": "zh-hans", "package": "gsdsimp",
                   "processors": PROCESSORS.split(","), "download_method": "NONE",
                   "device": "cpu", "seed": SEED, "pythonhashseed": os.environ["PYTHONHASHSEED"],
                   "torch_threads": torch.get_num_threads(),
                   "torch_interop_threads": torch.get_num_interop_threads(),
                   "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()},
        "package_versions": _package_versions(), "python_version": platform.python_version(),
        "platform": platform.platform(), "logical_cpu_count": os.cpu_count(),
        "documents": counts, "elapsed_seconds": round(time.perf_counter() - started, 3),
        "output_hashes": {path.relative_to(output).as_posix(): _sha256_file(path)
                          for path in output.rglob("*") if path.is_file()},
        "external_api_calls": 0, "network_operations_allowed": False,
        "gpu_used": False, "human_gold": False,
        "interpretation": "Parser feasibility and traceable case inspection only; no automatic prose-quality score.",
    })
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        if "--output-dir" in sys.argv:
            failure_directory = Path(sys.argv[sys.argv.index("--output-dir") + 1]).resolve()
            if failure_directory.is_dir() and failure_directory.is_relative_to((ROOT / "data/local").resolve()):
                write_json(failure_directory / "failure.json", {
                    "failure_type": type(error).__name__, "detail": str(error),
                    "traceback": traceback.format_exc(),
                })
        print(json.dumps({"failure_type": type(error).__name__}), file=sys.stderr, flush=True)
        raise SystemExit(1)
