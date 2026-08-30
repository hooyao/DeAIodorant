# Frozen Nominal-Chain Integration Probe

## Status

Protocol `nominal-chain-integration-probe-0.2` is frozen before any candidate
output is produced or inspected. Version 0.1 attempted to parse complete article
bodies. It was terminated without writing results when a 1,501-line tutorial
spent several minutes inside Stanza because code and DOM fragments were filtered
only after parsing. Version 0.2 freezes a pre-parse complete-prose gate derived
from the existing reader-passage reconstruction logic. This operational change
does not use candidate outcomes or alter the nominal-chain thresholds.

The probe is deterministic discovery, not a reader-quality score, authorship
detector, or product rule.

## Hypothesis

A reader may recognize every local term but still fail to segment a long
head-final nominal phrase on first pass. The narrow target is a pre-head chain
that supplies several modifiers without an overt boundary before the head noun
arrives. This is more specific than sentence length, abstract-word density, or
generic proposition decompression.

The reader-localized phrase `AI 原生时代全新算力服务需求` motivates the
hypothesis. It does not define a corpus label or authorize threshold tuning.

## Frozen strict candidate

For every Stanza `NOUN` or `PROPN` head, collect left-side `acl`, `amod`,
`compound`, and `nmod` dependents and their subtrees. The contiguous span from
the earliest modifier token through the head is a strict candidate only when:

1. at least five non-punctuation lexical tokens precede the head;
2. the pre-head material contains at least 10 visible characters;
3. at least three nominal-modifier dependency relations occur inside the span;
4. no verb occurs before the head inside the span;
5. no punctuation or symbol interrupts the span;
6. none of `的`, `之`, `及`, `与`, `和`, `或`, `、`, or `以及`, and no
   `CCONJ`, supplies an overt segmentation boundary;
7. the complete sentence contains a verb;
8. at least one lexical sentence token lies outside the candidate phrase;
9. the sentence is not recognized as code or a URL-bearing command fragment.

Named entities, numbers, nominal-chain depth, and CJK length are recorded as
diagnostics but do not decide admission. No abstract-word lexicon enters the
strict rule.

Before Stanza, non-overlapping source lines are rejoined into complete prose
passages. A passage must contain 120–360 CJK characters, at most 520 total
characters, at least two Chinese sentence-end marks, at least 50% CJK among
visible characters, and no URL, code cue, profile metadata, caption, dependent
opening, external figure reference, or list-heavy fragmentation. These gates
were already used for post-period reader-passage preparation; they are applied
here before parsing to avoid changing syntax through arbitrary fixed-size
chunks.

## Corpus and separation

The scan may open only:

- the 67 `development` documents in `post_reader_handoff_v2`;
- the 93 `discovery_reserve` documents in `post_reader_handoff_v3`, which are
  already feature-discovery exposed by the earlier frozen motif inventory.

The 30-document v2 validation reserve remains unopened. No pre/post effect is
estimated because the available corpora are not source-, topic-, format-,
length-, and visibility-matched.

## Decision gate

A construction can proceed to edit-operator design only if strict candidates
appear in at least six independent documents across at least three sources.
Passing frequency is not sufficient: the spans must still form one coherent
construction, exclude headings and fragments, and support one bounded edit
without deleting propositions, entities, quantities, negation, modality,
attribution, or voice.

The thresholds and boundary list must not be relaxed after outcomes. If the
reader example itself is not localized, record probe failure rather than
changing the rule.

## Reproduction

Run only on `gx10`:

~~~bash
PYTHONPATH=src .venv/bin/python experiments/nominal_chain_integration_probe.py \
  --handoff /path/to/post_reader_handoff_v2 development \
  --handoff /path/to/post_reader_handoff_v3 discovery_reserve \
  --model-dir /path/to/stanza-models \
  --output-dir /path/to/nominal-chain-integration-v1 \
  --device cuda \
  --seed 2026083001
~~~

Candidate text, parses, and model files remain in ignored local or remote
storage. Only aggregate results, frozen definitions, and artifact identities
may be committed.

## Result

Version 0.2 ran on `gx10` with Stanza 1.14.0, the `gsdsimp` package, CUDA, and
seed `2026083001`. The model fingerprint is
`5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9`.

The scan opened the requested 160 discovery/development documents and no v2
validation-reserve body. The pre-parse gate retained 1,393 non-overlapping
passages from 133 documents. The reader example was localized exactly as one
candidate: six pre-head lexical tokens, 12 visible characters, six nominal
relations, no boundary, and nominal-chain depth two.

The corpus scan found 87 strict candidates in 41 documents across all five
sources, so the frequency gate passed. Structural coherence did not:

- 47 instances in 30 documents contain a proper-name or numeric anchor;
- 67 of 87 instances have nominal-chain depth one;
- the set mixes report and program names, model and hardware specifications,
  lexicalized technical compounds, company descriptions, and genuine dense
  modifier strings;
- Stanza also treats predicate-like forms such as `修复`, `追平`, `排名`, and
  `去噪` as nominal heads in several contexts.

An audit-only diagnostic subset removed proper and numeric anchors and required
depth at least two. It retained 13 instances in seven documents and four
sources, but six came from one QbitAI document. The remaining cases still mix a
paper title, an official program name, ordinary technical compounds, a parsed
contrast, and possible integration problems. They do not support one bounded
edit operator across six independent documents.

Reject v0.2 as an intervention selector. Do not tighten its thresholds or add a
post-hoc head-noun blacklist against these results. No Project 8 is prepared.
Further work would need an independently frozen lexical-familiarity or phrase-
boundary signal, or new reader-localized examples, before another intervention
attempt.

## Artifact identity

| Artifact | SHA-256 |
|---|---|
| Probe script used remotely | `1a5814cac645ac55e24c8b4494dd7854e42c2aa4fafbae901d235bb121b2c121` |
| Summary | `2d48f84b5c954b6d6c909fb7fd394f868c34e47c01cc1bbb97ded3a8f0a0f0d4` |
| Candidate instances | `abfb5a5e9181c5b0e87d5636f649766c1c82437326ac5a0740229eec89e674c2` |
| v2 handoff manifest | `ecab7336c2ca54f59d24b79bcb841f0d3f4085a9c80a117f5a3ea0e31fec5d01` |
| v3 handoff manifest | `5462a30c6c9d8e598fd1f8f6af567bbb4d4efbcc7cc30e3bfd36d4965225ebac` |
