# Existing InfoQ source integrity audit v1

Date: 2026-09-14. Protocol: `media-source-completeness-v1`.
Presentation mapping: `media-source-presentation-v1`.

Both existing InfoQ anchors exactly match the complete collector-normalized
textual bodies in their current public page responses. This establishes source
text identity and supplies a traceable paragraph mapping. It does **not**
establish strong AI smell, target coverage, editing readiness, translation
admission, reader benefit, or model authorship. The maintainer explicitly
corrected the interpretation of previous human annotations: those samples did
not have strong or obvious AI smell. Historical local comments cannot turn
these assets into confirmed positive examples. No editing or model inference
was performed in this audit. The later foundational clarification retains
repeatable features of subjective AI smell as the front-half research question;
this audit is infrastructure for a real-media strong/weak contrast, not evidence
for the presence or absence of such features in the earlier weak samples.

## Sources and capture policy

Exactly two existing anchors were inspected:

| Document ID | Existing source | Published date | Stored byline |
| --- | --- | --- | --- |
| `3c60dc0a981b686870095450` | [Alibaba Cloud / Agent article](https://www.infoq.cn/article/s6TAS5JMIW1miPSqIsk0) | 2026-06-26 | 李文朋 |
| `44aa81958a6c585ee8c06847` | [Tencent Cloud / TCAR article](https://www.infoq.cn/article/cYlRMETcNGxhDvBqCDII) | 2026-01-16 | 腾讯云 |

Existing artifacts checked were `data/pilot/infoq_post.jsonl`, the matching
monthly body files, and the matching `meta.jsonl` records. A filename search
including ignored files found no earlier `.html` or `.htm` capture under
`data/`, excluding the new capture directory. No historical raw page response
was therefore available for a rendering comparison with the original crawl.

The audit made three unauthenticated ordinary GET requests: robots.txt and one
request per anchor. All returned HTTP 200. The captured robots policy allows
these article paths for the declared `DeAIodorantSourceAudit/1.0` user agent;
the policy and its hash are retained. A minimum two-second interval was used.
Requests began at 06:13:11, 06:13:14, and 06:13:17 UTC on 2026-09-14.

No redirects, retries, login, paywall/notice bypass, alternate content endpoint,
linked destination, or referenced media request was used. The capture client
disables ambient authentication and uses no API credentials. A non-success
robots response other than 404 prevents article requests; disallowed paths are
skipped; 429 or `Retry-After` stops further requests. Captures cannot be
overwritten by a repeated `--fetch` invocation.

## Text identity and boundaries

| Check | Alibaba Cloud | TCAR |
| --- | ---: | ---: |
| JSONL normalized body characters | 5,834 | 2,350 |
| Collector lines | 97 | 40 |
| Fresh text equals stored JSONL text | Yes | Yes |
| JSONL SHA-256 equals metadata content hash | Yes | Yes |
| Monthly file equals JSONL after explicit CRLF-to-LF normalization and removal of one final LF | Yes | Yes |
| CRLF line endings in the unchanged monthly file | 97 | 40 |
| Opening and ending 300 characters match | Yes | Yes |
| Title, byline, translator list, publication date match | Yes | Yes |
| Semantic text blocks in presentation mapping | 95 | 36 |
| Nonempty paragraph elements | 90 | 33 |
| Heading elements | 5 | 3 |

The immutable normalized body hashes are:

- Alibaba Cloud: `1d86ea8e2000bc104a266155800018df52aa53a34532a5fd998ebfb5226c61af`
- TCAR: `9168a023f239bb95e2df6a22a4d03b7e2f518d9bb23159ca34be9430524d3b04`

The monthly byte hashes differ from these content hashes because this Windows
checkout uses CRLF line endings and includes one terminal CRLF. The comparison
explicitly normalizes CRLF to LF and accounts for that terminal newline; raw
byte equality is not claimed. Original raw bytes remain unchanged. The fresh extracted text
was stored separately and never substituted into the pilot. Current page-view
snapshots increased from 12,821 to 13,188 and from 12,450 to 12,602 respectively;
the original visibility records were preserved. These are current exposure
counts, not comparable fixed-age popularity measurements.

The Alibaba body includes its introduction, four numbered section headings,
and its closing paragraph. The TCAR body includes three section headings,
its closing resource links, and a final paragraph consisting only of U+200B
(zero-width space). That final character is preserved and flagged; it is not
silently removed. Equality covers all extracted text, not merely these
boundary checks.

## Paragraph extraction and presentation

The historical `normalize_text` function calls `get_text("\n")`, then trims
and normalizes each resulting line. This introduces paragraph-like boundaries
at inline markup. Three observed paragraphs are affected:

| Source | Immutable collector lines | Cause | Presentation block |
| --- | --- | --- | --- |
| Alibaba Cloud | 8-10 | An inline hyperlink | `b008` |
| TCAR | 4-6 | Inline bold text | `b004` |
| TCAR | 15-17 | Inline bold text | `b013` |

Thus 97/40 collector lines must not be described as 97/40 original paragraphs.
The paragraph mappings contain 95/36 text blocks, including headings and the
TCAR U+200B-only paragraph. They preserve the original text-node strings,
normalized source-line ranges, block types, and list membership. Concatenating
their `collector_text` fields with newlines reproduces each immutable body
exactly. Separately labeled `presentation_text` joins the original inline nodes
and normalizes source whitespace; it is a presentation proposal, not a rewrite
candidate or a replacement corpus artifact.

The installed `html.parser` tree nests subsequent nodes under some self-closing
image elements in these responses. A naive top-level-child walk would therefore
misidentify much of the article as one image block. The mapping assigns each
text node to its nearest paragraph, heading, or list-item ancestor and checks
complete text coverage. It does not claim a browser-pixel rendering audit.
Actual reader displays should use sanitized source block structure or this
explicitly versioned mapping, with identical formatting in compared variants.
Restoring source layout must not count as a successful style intervention.

## Non-text material and provenance limits

| Captured element | Alibaba Cloud | TCAR |
| --- | ---: | ---: |
| Image references | 3 | 7 |
| HTML hyperlinks | 1 | 0 |
| Unordered lists / list items | 0 / 0 | 3 / 8 |
| Bold elements | 0 | 7 |
| HTML tables / code blocks | 0 / 0 | 0 / 0 |

The Alibaba images occur after collector lines 10, 13, and 78. The TCAR images
occur after lines 9, 10, 11, 12, 19, 21, and 23. Their URLs, alt attributes,
order, and source-line positions are recorded locally. None was downloaded or
visually inspected. Their contents could contain facts, diagrams, or tables
absent from the text extraction. Absence of HTML table elements does not prove
absence of tabular information inside images.

The Alibaba link anchor survives in the body, but its target
`http://skills.aliyun.com` does not. TCAR retains literal Hugging Face, GitHub,
and arXiv URLs as body text; these were not visited. List boundaries and bold
formatting are available in the new HTML but absent from the old plain text.

The current public structured author and translator fields match the old
records. Both translator lists are empty, and the existing deterministic
translation rules return no direct marker. This is an inventory observation,
not a new high-confidence originality judgment. The embedded `content` value
is structured data rather than a plain HTML string, so the audit does not
assert equality with that separate representation. It uses the publicly
returned `.ProseMirror` body used by the original collector.

The warranted description is **complete captured textual body**, with explicit
uninspected image references and missing original visual presentation. Complete
multimedia coverage is not established. Existing `data/pilot/` limitations and
historical exposure remain in force; these are development assets, not a clean
corpus, held-out evaluation set, or confirmed strong-smell set.

## Reproduction and artifacts

The bounded online capture was created with:

```powershell
python experiments/audit_media_source_capture.py --fetch --output-dir data/local/compact_refiner/media-source-captures-v1
```

Subsequent audit iterations used only the stored response bytes:

```powershell
python experiments/audit_media_source_capture.py --output-dir data/local/compact_refiner/media-source-captures-v1
```

The private, Git-ignored directory contains the robots response, both raw page
responses, `capture-manifest.json`, `audit-summary.json`, per-document audit
records, exact fresh collector output, and `*.blocks.json` presentation maps.
Raw pages may contain transient public embedded links; keep the captures
private and do not promote page payloads into tracked reports. The new files
total approximately 0.85 MiB. Underlying source rights remain with the source
publishers; public availability is not a redistribution license.

Runtime: Python 3.13.5, Beautiful Soup 4.14.3, requests 2.32.4, built-in
`html.parser`. No dependency, model, service, or binary was added. No GPU or
model inference was used. API inference cost is zero. The manifest records
request timestamps and response hashes; the audit records collector and audit
script hashes, package versions, and original byte/content hashes. Offline
replay and byte/hash/paragraph-coverage checks passed. Pilot bodies and metadata
were not changed.
