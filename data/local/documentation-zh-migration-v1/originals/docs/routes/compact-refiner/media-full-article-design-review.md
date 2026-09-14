# Real-Media Full-Article Development Design Review

Date: 2026-09-14. Status: independent design recommendation; no candidate
generation, new human outcome, or training run is reported here.

Suggested protocol identity: `compact-refiner-real-media-full-article-1.0`.
The executing run must freeze its concrete source manifest, intervention,
requests, and analysis before candidate generation. This document alone is not
an executed or confirmatory protocol.

## Corrected task and evidence boundary

The maintainer confirmed that the target is actual Chinese media writing of the
kind already acquired from InfoQ: improve willingness to continue reading a
complete article while preserving its informational value and authorial intent.
The target includes empty expansion, repetitive emphasis, ornamental framing,
and poorly supported relations between otherwise fluent sentences. Whether a
particular expression is a problem depends on its function in that article.

Publication date, known generator identity, an NLP feature, and model agreement
do not establish that a document has the reader's target problem. The route does
not identify authorship. It also does not require a universal smell score before
testing a specific edit on a reader-reported problem.

The maintainer's real-media clarification supersedes the generated-source scope
of the earlier [full-article source probe](full-article-source-probe.md). Preserve
that proposal and the short constructed CR-001 materials as historical records.
They remain useful engineering cases, but they do not supply the target media
distribution. Do not run another synthetic source generator to replace the real
articles already available.

Reuse the prior acquisition provenance, human comments, operation logs,
preservation checks, feature definitions, and failed selectors. Reuse does not
resume the paused pre/post discovery program. Do not inspect sealed reserves,
exposed translation final-test inputs, or new validation texts for this run.

The historical [smell catalog](../../smell-catalog.md) already records reader
objections to relation framing such as `相反`, `这样一来`, and `它真正解决的`,
and to the unresolved expression `AI 原生时代全新的算力服务需求`. These are
development leads with context-dependent counterexamples. They do not authorize
deleting those strings wherever they occur. Generic decompression and automatic
marker removal have already produced mixed or failed evidence.

## Smallest useful development batch

Start with two distinct, previously exposed source articles containing explicit
reader-reported problems. Use existing feedback to identify the affected spans.
If an already exposed article has clear no-obvious-problem feedback and a usable
complete source, add it as one overediting control. Do not generate a substitute
or ask the maintainer to screen a new batch merely to fill this optional slot.

Freeze selection before candidate outputs. Prefer an exact recoverable source
and unambiguous feedback-to-span mapping over an apparently dramatic example.
If more than two problem articles qualify, order them by the hash of the stable
document ID and a frozen seed. Record every considered article and exclusion.
Keep all variants, extracts, historical interventions, and future derivatives
of an article in the same development group.

An old human comment establishes the particular historical complaint; it is not
a fresh whole-article baseline rating. A new full-article comparison on that
source can establish a personal development preference for the new edit, but
cannot establish independent replication, population benefit, natural problem
prevalence, or improvement from SFT.

An unavailable historical handoff is a reproducibility limitation, not a reason
to recreate its text from a report. Recover an accessible source through the
normal acquisition path when permitted, retain the new timestamp and hash, and
compare it to any preserved original. Changed source text is a new version. If
the reader's complained-about passage cannot be aligned to that version, do not
claim that its target coverage is already reader confirmed.

## Source gates before editing

For each article retain the canonical URL, source and title, publication and
collection times, body hash, extraction version, original artifact references,
historical task IDs, feedback references, and exposure status. Preserve the
original body unchanged. Store any repaired extraction as a separately hashed
version with a transformation record.

Audit completeness against the source page or an already preserved complete
capture. Check the beginning and ending, section order, paragraphs, quotations,
lists, tables, code blocks, links, footnotes, figure anchors, captions, and any
text carried by images. Remove navigation or advertising only as documented
extraction, before freezing the editable article. A plausibly long body is not
proof of completeness.

Keep figures and other assets in the same position for both reader versions.
Do not recreate missing figures from imagination or silently drop their
captions. Record missing or inaccessible assets. If an essential claim depends
on unavailable visual content, that article cannot yet support a resolved
full-context comparison; continue with other eligible articles. A text-only
capture must be labeled as such and cannot silently become a complete source.

Translation status remains explicit. Known translated or compiled foreign
articles stay excluded from the primary corpus and primary media anchor pool.
Preserve their historical annotations as development challenge evidence; do
not erase them or reclassify them as original. Uncertain originality cannot be
silently admitted to the primary corpus. A separately labeled diagnostic use
does not repair corpus eligibility or permit a pre/post conclusion. Never use
the exposed translation final test to improve the gate.

Record rights separately for private research use, provider processing, training,
and redistribution. Public availability alone does not establish training
permission. Unknown training rights set `training_eligible=false`; this need
not stop source inspection, local preparation, or otherwise authorized private
diagnostic work. An explicit source restriction still applies. Do not publish
full third-party bodies, invent a license, or assume API authorization changes
the article's rights. Resolve the actual use and applicable evidence before a
training export, without turning that later prerequisite into a blanket
approval request for the current development work.

## Three principles to freeze before candidate outputs

1. **Freeze the target and allowed operation from the original.** For each
   problem article, save a source-only plan with the historical complaint,
   exact original offsets, one primary operation family, one to three target
   spans, the expected reading benefit, a plausible counterexample, and the
   meaning that must survive. Use the smallest complete span needed to test the
   complaint. Preserve necessary contrasts and informative repetition. A claim
   that seems vague or unsupported is still a claim; do not delete or strengthen
   it merely to make the article sound more concrete.
2. **Give every editor the same complete article and bounded authority.** Freeze
   low intensity, target spans, audience, existing author voice, legitimate
   protected content, output schema, model/agent provenance, attempts, and
   budget. The complete article is context; only the planned spans are editable.
   Editor inputs exclude preference answers, private review conclusions, and
   claim-inventory verdicts. Do not change prompts or request another valid
   candidate because the first candidate is disappointing. A repair is a new
   candidate version and a separate development result.
3. **Freeze failure, selection, and reporting rules.** An unchanged output is
   legitimate. Invalid replay, edits outside scope, truncation, critical meaning
   changes, or unresolved preservation prevent that candidate entering the
   reader contrast. Preserve and count the failure. Freeze how eligible
   contrasts enter the reader packet and how every planned article/arm remains
   in the denominator. No style-score threshold or preferred model output is
   chosen after seeing outcomes.

For this first batch, title, headings, quotations, citations, figures, tables,
code, and section order should be locked. A scoped exception must be justified
from the source and frozen before generation. If the apparent problem requires
new facts, resolving a genuine source ambiguity, or changing an asserted
conclusion, classify it as outside this style intervention. Do not invent the
missing semantic relation.

## Candidate arms and operation contract

Retain U, the exact original, for every article. Use the existing untuned
`qwen/qwen3.5-9b` prompt baseline as P if the verified current endpoint supports
the full request within the frozen cost and context limits. Record requested
and returned model/provider identities and revision uncertainty. This reuses a
more informative established compact baseline; it is not a final student choice
or evidence that the endpoint matches a future training checkpoint.

Use T, an independently authored strong assistant proposal, only where the
source-only plan identifies a useful in-scope intervention. Record T as model
assistance, never human editing or training gold. If T uses iterative reasoning
or manual inspection, disclose the difference from a one-call P response;
performance differences cannot be attributed purely to model size.

P and T receive the same original, legitimate context, and frozen target
authority. A no-clear-problem control has permission to return no operations.
Do not force a token number of edits. If full context exceeds a model's actual
request limit, record the operational exclusion rather than silently cutting
the article into an apparently equivalent task.

The editor returns structured local replacements with half-open Unicode
code-point offsets into the exact original, `before`, `after`, operation type,
and a short rationale. Apply nonoverlapping operations from right to left;
verify `before` exactly; reconstruct the full article deterministically. Save
the operation list, complete output, hashes, and both local and complete diffs.
No-operation output must reproduce U byte for byte under the declared UTF-8
serialization. Missing, malformed, or truncated output is not a keep decision.

This run tests whether specific bounded repairs are feasible in full context.
It does not yet test an autonomous whole-article locator. The source-only plans
are development guidance; successful guided edits do not demonstrate that a
compact model can find the same problems unaided. Test localization separately
after worthwhile repairs exist, using new versioned experiments.

## Preservation and diagnostic review

Build an independent source-only inventory of propositions, quantities, units,
entities, citations, conditions, scope, uncertainty, negation, attribution,
referents, and author stance. Include relevant context outside the target
spans. Record factual claims as the author's claims rather than silently
certifying their truth. A separate factual defect is not permission to repair
content during style evaluation.

Run deterministic integrity checks and compare protected content, then obtain
candidate-identity-blinded semantic review using the complete original and
complete candidate. Review both losses and additions, including new
implications caused by a connective change. Exact numbers and names surviving
does not establish preserved conditions or scope; CR-001 already supplied
counterexamples. Record `pass`, `fail`, or `uncertain`, evidence spans, reviewer
identity, and disagreement. Do not allow the candidate's author to supply its
sole acceptance judgment.

For a review-ready candidate, separately ask whether the targeted issue was
addressed, unchanged, or replaced by another problem, and whether the edit
disrupts later references or the article's argument. These are attributed
model-assisted diagnoses. They cannot establish human preference or export
eligibility. No-op outputs, rejected outputs, and fallback-to-U outputs remain
separate categories.

Retain the old NLP features as diagnostics around the targeted spans and in the
complete article. They can measure what changed and expose checks that missed
a failure. Do not rank success by a composite smell score, distance to a
pre-period corpus, classifier confidence, or the largest observed feature
change. With two problem articles, descriptive case analysis is appropriate;
sentences, operations, and multiple reviewers are not independent article
replications.

## Full-article reader packet

Prepare a local packet only after the candidate, full-context review, and
selection rule have been frozen. Each task displays two complete article
versions with identical typography, section structure, visual assets, links,
and available publication context. A and B placement uses a saved seeded
allocation, with editor/model identity hidden. Do not include diff highlighting,
target markers, model verdicts, NLP scores, expected answers, or a summary in
place of either article. Keep a separate inspection view with complete diffs
and the identity key for use after the reader response.

Use one candidate-versus-U contrast per article in the first small session.
Prespecify the choice: prefer P when it is nonidentical, preservation resolved,
and independently judged to address the frozen target; otherwise use an
eligible T as a feasibility contrast. If both satisfy these conditions, keep
the unshown arm in the diagnostic report. If neither does, record no eligible
contrast and continue development; do not request a meaningless comparison.
Disclose this eligible-candidate selection when reporting. It cannot estimate
the unconditional success rate of P, T, or the deployment policy.

The primary prompt asks which complete version makes the reader more willing
to continue. Preserve A, B, no meaningful difference/both acceptable, both
unacceptable, and unable to judge. Optional feedback can identify meaning or
voice concerns and remaining irritating passages. Do not require another
original-only smell judgment for an already reader-flagged example, or ask the
reader to annotate every sentence. Retain the exact historical complaint as
provenance rather than showing it as an answer cue.

This is a qualitative development packet with acknowledged prior exposure,
not a blinded independent validation study. Hiding version identity does not
erase familiarity with the original. It does not need to burden the maintainer
with duplicate full-article controls solely to claim statistical rigor. A
later formal reader study must freeze its controls, allocation, multiple-reader
sampling, and precision design on new independent groups.

## Stage gates and autonomous next actions

| Gate | Required evidence | Action without further user input |
|---|---|---|
| Source usable | Exact provenance, historical feedback alignment, explicit translation/rights disposition, sufficient full context | Freeze eligible development inputs; recover or exclude incomplete versions and continue other articles |
| Intervention ready | Source-only targets, locks, operation authority, request/budget identities, selection and analysis rules frozen | Generate the bounded P/T proposals and retain U |
| Candidate review ready | Exact operation replay, scope checks, complete output/diff, independent full-context review | Diagnose failed or uncertain edits; keep versioned repairs distinct |
| Concrete reader contrast | At least one nonidentical proposal with resolved model-assisted preservation and a plausible target repair | Freeze the actual full-article reader packet, mapping, and complete diagnostic report |
| Human preference known | Direct reader response tied to exact packet and hashes | Record direction, strength if supplied, missingness, preservation concerns, and narrow personal-development interpretation |
| Training preparation justified | Useful accepted edits, rights and semantic acceptance, defined workload and evaluation plan | Size cloud GPU requirements; do not start local SFT or provision a host |

If no article has a useful in-scope target or all candidates fail, that is a
concrete diagnosis. Continue authorized source recovery, measurement repair,
or a separately versioned narrow intervention where the evidence supports it.
Do not produce endless candidates without an explicit hypothesis, silently
expand to a new product task, or substitute synthetic notices again.

The work that can be completed autonomously includes source/provenance
reconciliation, completeness checks, source-only plans, bounded authorized
inference, independent model review, operation tooling, diagnostics, and the
final reviewable packet. The maintainer need not approve each routine step.

Fresh personal reading preference is external evidence only an actual reader
can supply; no agent can fabricate it. Ask for it when a concrete, worthwhile
full-article contrast exists and the independent preparation is complete. A
request to change product scope, train on material without established rights,
or obtain the promised cloud GPU is a separate decision when it becomes
necessary. No GPU is required to execute this development experiment.

## Required report

Report considered and eligible original articles, completeness/translation/
rights exclusions, historical exposure, attempted P/T calls, raw failures,
unchanged outputs, reviewed changes, preservation failures/uncertainties,
issue-resolution assessments, fallback counts, reader-ready contrasts, and
actual human outcomes separately. Include all planned denominators, exact
input/configuration/output identities, API usage/cost and missingness, and the
full-article artifact paths. Summarize source bodies in tracked reports by IDs
and evidence references rather than redistributing them.

The strongest possible result from this batch is a traceable, meaning-preserving
repair that the maintainer prefers in the original media context, together with
a concrete account of the compact baseline's limitations. It still supplies no
measured SFT gain, validated universal smell rule, or justification for online
reinforcement learning.
