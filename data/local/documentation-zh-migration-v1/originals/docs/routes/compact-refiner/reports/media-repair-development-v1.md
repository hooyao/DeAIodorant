# Complete-Article Repair Development

Date: 2026-09-14. Protocol: `media-repair-development-1.0`.
Status: candidate development and assistant preservation review complete;
human reading outcome unmeasured. No training export or smell-efficacy claim.

## Result

One assistant edited three complete real Chinese articles using Chinese input
alone. It did not see the earlier defect labels, cue counts, English originals,
or expected reader answers. Two separate assistants reviewed complete original
and candidate text, then audited all operations without editor rationales.

The first proposals passed numeric, term, URL, source-hash, and operation-replay
checks, but only one of three passed the independent semantic review. This
reinforces why a strong teacher's output cannot automatically become an SFT
target or why literal preservation cannot replace semantic review.

| Source | Initial operations | Initial assistant preservation | Final operations | Final assistant preservation |
|---|---:|---|---:|---|
| Tencent routing report, doc-03 | 14 | Uncertain: 1 scope substitution | 13 | Pass after exact source reversion |
| Translated long interview, doc-04 | 40 | Fail: 1 qualifier change, 3 uncertain interpretations | 36 | Pass after 4 exact source reversions |
| Cowork report, doc-05 | 13 | Pass | 13 | Pass; candidate unchanged |

V1 candidates and reviews remain frozen. The doc-03/doc-04 v2 candidates remove
only the non-passing operations. Follow-up reviews verify exact source
restoration, unchanged remaining operation objects, whole-source replay, and
inverse reversion from the reviewed v1 output. The original full-text judgments
carry forward through this verified identity chain; these are not additional
independent full-text reviews or human certifications.

## Preservation failures worth learning from

- `一样的问题` became `同类问题`: same-problem capability may be weakened into
  same-class capability even though names and numbers are unchanged.
- `大部分目标` became `主要目标`: extent/majority becomes importance/priority.
- An ill-formed causal question was assigned a specific intended interpretation.
- A potentially limited task domain became an explicit universal scope.
- A startup addressed figuratively as `你` became an individual in a startup.

The final candidates revert these five operations. This preserves ambiguity
where the Chinese source does not license a unique repair. It also leaves some
bad source expressions unresolved. The experiment does not pretend that every
problem can be repaired without additional evidence.

## Concrete repair opportunity

The Cowork candidate separates the late paragraph's dissatisfaction statement
from its qualified relevance claim:

> 此外，还有一些用户表达了对 Anthropic 近期产品策略与沟通的不满。这些评论虽然并非专门针对 Cowork，但与它的发布背景和用户关系间接相关。

The corresponding original mixes comments, users, a nominal dissatisfaction
phrase, and an unclear final relation. The candidate retains both criticism
targets, the non-Cowork-specific qualification, and indirect relevance. This
is an assistant-preservation-passing proposal, not a measured reader win.

Other repairs fix duplicated predicates, inconsistent coordination, recoverable
references, and local punctuation. Meaningful contrasts remain. Across these
three sources, the literal count changes only from 32 to 31: reduced marker
count is not the objective or an efficacy measure.

## Source defects remain visible

The editor records 2, 9, and 5 unresolved content issues respectively. These
counts describe the editor's notes, not verified error prevalence. Examples
include unsupported performance generalizations, unclear scheduling semantics,
an unlabeled interview turn, inconsistent-looking milestone/platform wording,
and stronger summaries than their quoted evidence.

No content gap is silently filled. The translated interview remains explicitly
in scope, while its English source and translation method remain unverified.
Input author identity is not inferred from style. Public research access also
does not establish training rights; training eligibility remains false.

## Shared presentation prevents an extraction artifact from becoming a win

The original collector inserts newlines inside emphasized text. Five Cowork
operations, five interview operations, and one routing-report operation change
only whitespace. Showing those raw lines as broken paragraphs would make the
unchanged source artificially difficult.

The comparison renderer therefore uses the saved source DOM paragraph mapping
for both columns. It projects non-whitespace edits onto the same paragraph
structure and gives whitespace-only operations no visible advantage. All
non-whitespace source and candidate characters are verified exhaustively. No
operation crosses an original DOM paragraph boundary in these cases.

There are 36/165/45 source paragraphs and 12/31/8 visibly changed paragraphs for
doc-03/doc-04/doc-05. The renderer exposes the entire article, with links to
changed paragraphs, identical typography, and marked original/candidate columns.
It is an identified qualitative review, not a blinded preference instrument.
Referenced images are not rendered, and that limitation is explicit.

## Ready private artifacts

- `data/local/media-repair-development-v1/candidates/`: frozen first proposals.
- `candidates-v2/doc-03/` and `candidates-v2/doc-04/`: exact-reversion revisions.
- `preservation/`: independent v1 reviews and focused v2 verification.
- `validation-v1/`: full replay, literal diagnostics, hashes, and diffs.
- `presentation-v1/<alias>/review.html`: whole-article shared-layout comparison.
- `presentation-v1/<alias>/paragraphs.json`: source-linked displayed paragraphs.
- Preparation, revision, and presentation manifests preserve reproducible
  identities; two private builder scripts reproduce the v2 reversion logic.

The serving checkpoint identity was unavailable to the agents and is recorded
as unknown. Candidate generation is not claimed deterministic. No OpenRouter
requests, new model downloads, GPU, SFT, DPO, or human labels were used.

`ready-selection.json` seals the three final candidate/review/presentation
identities: 62 retained operations, including 11 whitespace-only operations
neutralized in the comparison. Required verification passed 168 offline tests
and compilation of the package, required entry points, and new experiment
scripts. No source corpus file or prior feedback was changed.

## Next boundary

The useful next human input is actual reading experience on a concrete
preservation-reviewed article, with uncertainty and possible no-improvement
responses retained. Do not ask for a strong-smell label for the already
weak-smell Cowork case, and do not interpret its readability response as proof
that the complete product removes smell. Independent source/feature discovery
continues through the translation-inclusive acquisition extension.
