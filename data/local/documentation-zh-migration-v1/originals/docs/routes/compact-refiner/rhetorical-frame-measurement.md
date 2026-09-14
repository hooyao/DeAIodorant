# Contrast Constructions and Reader-Agenda Frames

Protocol: `rhetorical-frame-measurement-1.0`. Date: 2026-09-14.
Status: exploratory measurement specification informed by the maintainer's
explicit localized observations, before this version's new measurements.

## Maintainer clarification

The maintainer identifies the literal `而是` as a strong signal and explains
that the SMZDM example `机载的不是 Jetson，是一块国产瑞芯微 RK3566 核心板`
uses a bare positive copula to express the same negative-positive construction.
The surface omission of `而` does not change that example's correction.
Preserve the reader-nominated construction as a high-priority hypothesis.
Do not treat the article's zero literal count as evidence against the broader
signal or silently change historical literal counts.

The maintainer also localizes `先把买、搓、等三条路算明白` in the title as
a strongly aversive cue. Titles and section headings must be inspected as part
of the whole article; body-only counts do not cover that observation.

## Two separate candidate families

### Negative-positive replacement/correction

Keep the existing literal `而是` count unchanged and expose the explicit form
in the new analysis. Add a separately reported realization in which a catalog
negative prefix precedes a comma/semicolon followed immediately by `是` or
`就是`. Whitespace may occur at that boundary. Reuse the frozen negative-prefix
catalog from `reading_burden.py`; do not expand it silently.

The nearest permitted negative prefix must occur in the same input block after
the last `。！？!?` or previously consumed contrast connector, whichever is
later. A prefix embedded in `而不是` is not a new negative-side anchor. Do not
reuse one prefix for multiple positive clauses. Newlines within a supplied DOM
block do not create sentence boundaries. Inputs for this run are true saved
DOM blocks, not collector lines treated as paragraphs.

Every explicit literal remains observable even if its prefix is unresolved.
Unresolved literals are not silently called confirmed paired constructions.
Report paired explicit and bare-copula candidates separately and together;
their syntactic similarity does not certify semantic equivalence in every
possible sentence. No source sentence is rewritten.

Reverse-order classifications, implicit negation outside the fixed catalog,
intervening subjects/adverbs before the positive copula, and broader parallel
contrasts remain outside this narrow first extractor. An omitted case is a
coverage limitation, not evidence of good writing. A matched construction may
convey a necessary distinction and is not automatically redundant.

### Reader-agenda framing

Locate `先把` followed by a nonempty topic and one of this fixed result-predicate
inventory: `算明白`, `说清楚`, `说明白`, `讲清楚`, `讲明白`, `捋清楚`, `捋清`,
`理清楚`, `理清`, `弄清楚`, `弄明白`, or `搞清楚`.
Do not match across a comma, colon, semicolon, terminal mark, or newline.
Chinese enumeration separator `、` is allowed inside the topic.

Record the exact topic span and enumeration-separator count, along with title,
heading, or body role. This operationalizes a limited cognitive-organization
template; it does not catch every directive or validate whether it is unwanted.
Practical actions such as removing a battery are outside this inventory.

The title's three abbreviated activities and the noun phrase packaging them as
three routes are retained for semantic interpretation. Do not hard-code that
exact title as the only positive pattern or assume every enumeration is bad.

## Scope, artifacts, and safeguards

First run on the two source-linked reader anchors: complete titles and DOM
blocks for SMZDM and Baidu. Keep all matched and unmatched observations; no
corpus-wide effect, accuracy, severity ranking, p-value, or RL reward is inferred.
The corpus, genre, and length confounding of the pair remains unchanged.

Save zero-based end-exclusive Unicode offsets within each input record, exact
evidence, prefix/marker/topic spans, realization, and role. Report title and body
separately as well as total candidate coverage. Preserve all earlier source,
feedback, analysis, and count versions. Input, code, protocol, and output hashes
are recorded in a new private run under `feature_runs/reader-anchor-frames-v1/`.

Tests must distinguish the actual bare-copula construction from ordinary uses
of `是`, prevent cross-sentence/block and repeated-prefix matches, retain
unresolved explicit literals, verify exact Unicode spans, and keep ordinary
directive examples from becoming error labels. Candidate extraction is separate
from semantic necessity, reader harm, and editing efficacy.
