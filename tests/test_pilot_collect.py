import datetime as dt
import json

from pilot_collect import (
    extract_infoq,
    extract_jiqizhixin,
    LocalTranslationClassifier,
    is_translation_from_evidence,
    quality_metrics,
    strong_original_evidence,
    translation_evidence,
    write_monthly_corpus,
)


def test_quality_gate_accepts_substantive_chinese_text():
    text = "这是一个包含具体信息和完整论述的段落。" * 70
    metrics = quality_metrics(text)
    assert metrics["cjk_chars"] >= 500
    assert metrics["quality_pass"] is True


def test_infoq_extraction_from_server_state():
    state = [None] * 20
    state[2] = {
        "article_title": 3,
        "publish_time": 4,
        "content": 5,
        "views": 6,
        "comment_count": 7,
        "love": 8,
        "collect": 9,
        "author": 10,
    }
    state[3] = "A useful article"
    state[4] = 1654041600000
    state[5] = "unused"
    state[6] = 1200
    state[7] = 8
    state[8] = 20
    state[9] = 15
    state[10] = [11]
    state[11] = {"nickname": 12}
    state[12] = "Author"
    state[13] = []
    state[2]["translator"] = 13
    body = "这是经过编辑的高质量中文内容。" * 80
    html = (
        '<html><body><article><div class="ProseMirror">'
        f"<p>{body}</p></div></article>"
        f'<script id="__NUXT_DATA__" type="application/json">{json.dumps(state)}</script>'
        "</body></html>"
    )
    record = extract_infoq(html, "https://www.infoq.cn/article/example?x=1", "now")
    assert record is not None
    assert record["published_at"] == dt.date(2022, 6, 1).isoformat()
    assert record["views"] == 1200
    assert record["authors"] == ["Author"]
    assert record["translators"] == []
    assert record["is_translation"] is False
    assert record["quality_pass"] is True


def test_jiqizhixin_extraction():
    body = "这是机器之心历史归档中的完整中文文章内容。" * 70
    html = f"""
    <html><body>
      <div class="article-author__name">Editor</div>
      <div class="article__type">原创</div>
      <div class="article__published">2022/06/15 10:30</div>
      <h1 class="article__title">Archived article</h1>
      <div class="article__content"><p>{body}</p></div>
    </body></html>
    """
    warc = {"filename": "a.warc.gz", "offset": "10", "length": "20"}
    record = extract_jiqizhixin(
        html,
        "https://www.jiqizhixin.com/articles/2022-06-15-1",
        "2022-06-16T00:00:00+00:00",
        warc,
    )
    assert record is not None
    assert record["published_at"] == "2022-06-15"
    assert record["authors"] == ["Editor"]
    assert record["article_type"] == "原创"
    assert record["is_translation"] is False
    assert record["quality_pass"] is True


def test_infoq_translation_is_explicitly_flagged():
    state = [None] * 20
    state[2] = {
        "article_title": 3,
        "publish_time": 4,
        "content": 5,
        "translator": 10,
    }
    state[3] = "Translated article"
    state[4] = 1654041600000
    state[5] = "unused"
    state[10] = [11]
    state[11] = {"nickname": 12}
    state[12] = "Translator"
    body = "这是一篇页面明确标注译者的中文翻译文章。" * 70
    html = (
        '<article><div class="ProseMirror">'
        f"<p>{body}</p></div></article>"
        f'<script id="__NUXT_DATA__" type="application/json">{json.dumps(state)}</script>'
    )
    record = extract_infoq(html, "https://www.infoq.cn/article/translated", "now")
    assert record is not None
    assert record["translators"] == ["Translator"]
    assert record["is_translation"] is True
    assert "explicit_translator_field" in record["translation_evidence"]


def test_low_cost_translation_heuristic_requires_original_link_and_english_bio():
    text = (
        "正文内容。\n作者简介：\nTracy Miranda 是持续交付领域的专家。\n"
        "原文链接：https://example.com/original"
    )
    evidence = translation_evidence(text)
    assert "original_link_marker" in evidence
    assert "english_name_in_author_bio" in evidence
    assert is_translation_from_evidence(evidence) is True


def test_original_link_alone_is_not_enough_to_flag_translation():
    evidence = translation_evidence("本文参考了很多资料。原文链接：https://example.com")
    assert is_translation_from_evidence(evidence) is False


def test_compiler_byline_is_direct_translation_evidence():
    evidence = translation_evidence(
        "作者 / Rodney Brooks\n编译 / 赵阳 曹锦\n正文……\n原文链接：https://example.com"
    )
    assert "direct_translation_phrase" in evidence
    assert is_translation_from_evidence(evidence) is True


def test_foreign_podcast_transcript_is_translation():
    text = """下文基于播客视频整理，经 InfoQ 编辑。
Ashlee：
你小时候就开始编程吗？
Pedro：
是的。
访谈视频原链接：https://www.youtube.com/watch?v=example
"""
    evidence = translation_evidence(text)
    assert "foreign_media_transcript" in evidence
    assert is_translation_from_evidence(evidence) is True


def test_local_chinese_interview_is_strong_original_evidence():
    record = {
        "is_translation": False,
        "article_type": None,
        "authors": ["Tina"],
        "text": "采访嘉宾 | 于佳（宗心）\n本文是 InfoQ 对闲鱼技术负责人的中文采访。",
    }
    assert "local_interview_or_talk" in strong_original_evidence(record)


def test_chinese_wechat_reprint_is_strong_original_evidence():
    record = {
        "is_translation": False,
        "article_type": None,
        "authors": ["PingCAP技术团队"],
        "text": "原文：https://mp.weixin.qq.com/s/example\n来源：PingCAP - 微信公众号",
    }
    assert "chinese_source_reprint" in strong_original_evidence(record)


def test_local_model_excerpt_is_bounded():
    record = {
        "title": "标题",
        "authors": ["作者"],
        "text": "甲" * 3000,
    }
    excerpt = LocalTranslationClassifier.excerpt(record)
    assert len(excerpt) < 2600
    assert "标题：标题" in excerpt


def test_monthly_layout_has_one_metadata_file_per_month(tmp_path):
    records = [
        {
            "doc_id": "a1",
            "published_at": "2022-06-01",
            "source": "example",
            "text": "第一篇正文",
        },
        {
            "doc_id": "a2",
            "published_at": "2022-06-20",
            "source": "example",
            "text": "第二篇正文",
        },
        {
            "doc_id": "b1",
            "published_at": "2025-07-01",
            "source": "example",
            "text": "第三篇正文",
        },
    ]
    root = tmp_path / "monthly"
    write_monthly_corpus(root, records)

    june_meta = (root / "2022-06" / "meta.jsonl").read_text(encoding="utf-8").splitlines()
    july_meta = (root / "2025-07" / "meta.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(june_meta) == 2
    assert len(july_meta) == 1
    assert (root / "2022-06" / "a1.txt").read_text(encoding="utf-8") == "第一篇正文\n"
