# Media Contrast Source Qualification v1

Date: 2026-09-14. Review version: `media-contrast-source-qualification-1.0`.
Status: model-assisted qualification, not human gold; all six documents remain
unadmitted staging material. No target-intensity or authorship labels were made.

The six complete supplied textual articles and their six referenced
`structure.json` files were read. All six contain substantive information, but
only three have supported original-language provenance at the model-assisted
level. One domestic engineering case needs provenance clarification. Two articles
explicitly compile foreign material and must be excluded from the primary
original-Chinese comparison, one from each temporal cohort. Empty translation
metadata is insufficient to override evidence in the bodies and links.

| Packet ID | Format and topic | Provenance disposition | Textual inspection and material limits |
|---|---|---|---|
| pair-01-A | Named InfoQ interview on CNStack | Supported original, model-assisted | Eligible for scoped textual inspection. Product architecture, deployment constraints, and vendor claims are substantive. One unreviewed image; the published article explicitly excerpts a longer discussion. |
| pair-01-B | Founder opinion on enterprise AI governance | Supported original, model-assisted | Eligible for textual inspection. Named products, architecture, business-metric examples, and a declared company interest are present. No images recorded; original WeChat page and corporate facts remain unverified. |
| pair-02-A | SelectDB-attributed Xiaomi Doris case | Plausible original; provenance uncertain | Hold original-language eligibility: vendor byline and unnamed client narrator lack an explicit adaptation/original-source chain. Concrete operations and performance details are present. Fifteen images and flattened SQL prevent complete technical evidence inspection. |
| pair-02-B | Named PalFish engineers' iOS implementation article | Supported original, model-assisted | Eligible for scoped textual inspection. Source URL, named authors, thresholds, design alternatives, and operational examples are present. Seven images and five flattened code blocks require presentation repair before whole-article comparison. |
| pair-03-A | Twitter acquisition news and biography roundup | Exclude foreign compilation | Explicit foreign-report attribution throughout and links to Bloomberg, New York Times, Wired, Business Insider, and other foreign material. Substantive and textually complete, but primary-cohort ineligible. One image unreviewed. |
| pair-03-B | Cowork announcement and community-reaction roundup | Exclude foreign compilation | Attributed foreign announcement quotation, product-statement summaries, and Reddit reactions with source links. Substantive and textually complete, but primary-cohort ineligible. Four images unreviewed. |

The exclusion of pair-03 is based on explicit source dependencies, not the
foreign subject matter or the named Chinese bylines. By contrast, pair-01-B
supplies a first-person domestic business argument with a named author and source
link. Its foreign corporate facts and two attributed English quotations do not
alone justify calling the whole article foreign compilation. The Apple reference
in pair-02-B likewise does not displace its documented domestic engineering origin.

Substantive value was assessed through information content, mechanisms, examples,
and qualifications, independently of writing style. No article was required to
have polished prose, and none was rejected for the expression problem under
study. Claims remain source assertions rather than verified facts. Commercial
interests, unnamed customer evidence, and absent benchmark conditions must remain
visible when these materials are interpreted.

The technical pair cannot yet support a complete article-level reading experience.
In pair-02-A, benchmark captions reference unavailable chart details; the captured
SQL joins tokens. In pair-02-B, before/after overhead and memory claims explicitly
rely on unseen figures, and flattened code merges line comments and statements.
Both retain copy-code interface labels. These are presentation limitations even
though the packet's non-whitespace textual identity is preserved. No source text,
code, figure, or caption was corrected in this review.

All 28 image references are preserved in the supplied structures, but none was
viewed or downloaded here. Empty alt text and absent figure captions cannot prove
that the media are decorative. The structures record references, not inspected
image content; this report does not certify multimedia completeness. Pair-03-B
also retains literal emphasis markers and a reference query string; neither is
used as evidence of authorship.

The supplied InfoQ publication dates divide evenly between pre-2023 and
post-2025-06. Publication, update, original-source, and collection provenance must
remain distinct. In pair-02-B, the original URL date is 2021-08-30 while the InfoQ
publication date is 2021-09-27; both precede the cohort boundary. The transition
period is excluded. Current view counts of 3,143 to 11,189 are visibility snapshots,
not age-adjusted evidence that the historical and recent samples are comparable.
No high-quality/high-visibility corpus admission was performed. All training
licenses remain unverified, including the article with a reprint notice.

The apparent pairings are not controlled comparisons: pair-01 contrasts an
interview with a founder opinion essay and differs substantially in length;
pair-02 differs in topic, attribution, code density, and figures. No comparative
style inference follows from this qualification review.

## Reproduction identity

Input: `data/local/media-contrast-review-v1/qualification-inputs.json`.
Input SHA-256: `a809c8de44623b538cede9acb762802901bdafe2194eac2603fcc98f1fcba5c7`.
Private output: `data/local/media-contrast-review-v1/qualification-review.json`.
The output records document IDs, supplied capture hashes, verified presentation
hashes, structure hashes, source quotations, dates, evidence, and uncertainty for
each article. Every quoted evidence string was checked as an exact substring of
the supplied full article. All six presentation SHA-256 values matched the packet.

Reading used local PowerShell `Get-Content` / `ConvertFrom-Json` on the packet and
its referenced structure files. A Python standard-library assembly step wrote
only the private JSON and this report, checked the six IDs and evidence excerpts,
and computed SHA-256 with `hashlib`. No API call, image inspection, benchmark
read, source rewrite, or admission command was used. Qualitative judgments are
model-assisted and are not deterministic gold labels. The exact session model
identifier and sampling settings were not exposed in the reviewing agent context.
