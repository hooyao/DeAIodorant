import datetime as dt
import hashlib
import json

from deaiodorant.corpus.integrity import validate_monthly_corpus


def write_document(root, *, doc_id="doc-1", published_at="2022-06-15", body="示例正文"):
    month = published_at[:7]
    month_dir = root / month
    month_dir.mkdir(parents=True, exist_ok=True)
    text_file = f"{doc_id}.txt"
    (month_dir / text_file).write_text(body + "\n", encoding="utf-8")
    record = {
        "doc_id": doc_id,
        "source": "example",
        "period": "pre",
        "url": f"https://example.com/{doc_id}",
        "published_at": published_at,
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "quality_pass": True,
        "is_translation": False,
        "translation_evidence": [],
        "visibility_evidence": "page_view_snapshot",
        "content_hash": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "text_file": text_file,
    }
    (month_dir / "meta.jsonl").write_text(
        json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def test_integrity_accepts_consistent_monthly_corpus(tmp_path):
    root = tmp_path / "monthly"
    write_document(root)

    report = validate_monthly_corpus(root)

    assert report["valid"] is True
    assert report["documents"] == 1
    assert report["errors"] == []


def test_integrity_rejects_transition_period_and_hash_mismatch(tmp_path):
    root = tmp_path / "monthly"
    record = write_document(root, published_at="2024-06-15")
    record["content_hash"] = "0" * 64
    meta_path = root / "2024-06" / "meta.jsonl"
    meta_path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")

    report = validate_monthly_corpus(root)
    messages = [item["message"] for item in report["errors"]]

    assert report["valid"] is False
    assert "Document falls inside the excluded transition period" in messages
    assert "content_hash does not match the body file" in messages


def test_integrity_rejects_orphan_body_file(tmp_path):
    root = tmp_path / "monthly"
    write_document(root)
    (root / "2022-06" / "orphan.txt").write_text("孤立正文\n", encoding="utf-8")

    report = validate_monthly_corpus(root)

    assert report["valid"] is False
    assert any("no metadata record" in item["message"] for item in report["errors"])


def test_integrity_can_require_the_configured_model_gate(tmp_path):
    root = tmp_path / "monthly"
    write_document(root)

    report = validate_monthly_corpus(root, required_translation_model="qwen3.5:9b")

    assert report["valid"] is False
    assert report["model_gated_documents"] == 0
    assert any("configured model gate" in item["message"] for item in report["errors"])
