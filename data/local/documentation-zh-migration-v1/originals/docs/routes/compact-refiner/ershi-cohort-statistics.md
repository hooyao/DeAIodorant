# Contrastive Reframing Family: Cohort Statistics

Protocol: `ershi-cohort-statistics-1.0`.
Status: retrospective/descriptive analysis of available real-media material,
not a confirmatory study, authorship classifier, or validated quality reward.

## Request and counting boundary

The maintainer identifies repeated forms such as `不是……而是……`,
`并非……而是……`, and other `而是` constructions as a particularly salient
style cue and requests pre-2023 versus post-June-2025 statistics.

The primary measurement is the literal occurrence count of `而是` in the full
captured article body. Each occurrence counts once. `而不是` and `而非` are
separate expressions and do not enter that literal count. Title counts are
reported separately. Quoted source material is retained; a counted occurrence
does not establish that a contrast is unnecessary or that the author used AI.

A secondary lexical classifier assigns one left-prefix category to each
occurrence using a fixed prefix catalog. The search window starts after the
latest terminal punctuation (`。！？!?`) or previous contrast connector;
text-node newlines alone do not break the window because the collector can
insert them inside a sentence. The last matched longest-first negative prefix
determines the category. Unpaired occurrences remain in the primary count.
This is a lexical classification, not a semantic proof of contrast.

## Corpus and comparisons

Use the existing 20 InfoQ pilot articles and 20 nonempty newly captured InfoQ
bodies in `media-contrast-staging-v1`. Validate source hashes and deduplicate
IDs, URLs, and normalized body content before counting. The ten Machine Heart
pilot articles remain a separately reported pre-period source; they cannot
stand in for a matched InfoQ time comparison.

- Pre: publication before 2023-01-01.
- Post: publication on or after 2025-07-01.
- Transition: report separately and exclude from the primary contrast.

Do not treat this combination of an earlier visibility-selected pilot and a
small seeded sitemap sample as a representative or fully matched corpus.
Report the pilot and new sample separately as well as the combined diagnostic.
Originality, quality, and visibility reviews remain incomplete for some sources.

Prespecified sensitivity views:

1. All nonempty captured InfoQ bodies, retaining an explicit contamination flag.
2. Exclude known deterministic translations and the historically documented
   translated pilot document `b186cdd4f9004e0413395bf3`.
3. Within each view, additionally restrict to at least 1000 CJK characters to
   show sensitivity to short FAQ/news/announcement formats. Length is a format
   sensitivity, not a quality or originality gate.

The named exclusion is existing repository evidence, not a threshold or label
learned from final-test outcomes. No benchmark body/label is used to select
feature definitions or as an additional analysis document.

## Outputs

For each source/run/cohort/view report article count, total CJK characters,
literal occurrences, occurrences per 10,000 CJK characters, number/share of
articles with at least one occurrence, mean/median per-article frequency,
left-prefix categories, and high-count contributors. Keep every document's
raw count and normalized rate so a long outlier cannot hide behind an aggregate.

Report corpus composition, exclusions, and missingness. Do not attach a causal
AI-attribution claim or a confirmatory p-value. This measures whether the reader's
specific observable cue differs in the available sample; whether an edit should
remove an instance still depends on its discourse function and preservation.

The current Cowork article already has eight literal occurrences. Its reader
assessment remains low/weak AI smell with strong translationese and difficulty;
this single case therefore does not validate a frequency-to-smell threshold.

No frozen prior feature configuration is modified. New code, versioned output
manifests, and tests remain separate from the older unsuccessful probes.
