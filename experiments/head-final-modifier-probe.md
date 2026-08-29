# Head-Final Modifier Delay Probe

## Status

This is a deterministic post-outcome development probe. It was defined after a
reader localized a specific residual problem in the first proposition-
decompression intervention. It is not validation, a semantic judge, or an
authorship detector.

## Reader-localized construction

The source contained:

~~~text
AI 算力池面向 AI 原生时代全新算力服务需求
~~~

The reader had to delay attachment until the final head noun `需求`, while
segmenting the preceding material approximately as `AI 原生时代 / 全新 / 算力
服务`. The reader then noted that the modifier string remained long and gave no
concrete account of what made the requirements new.

The preferred revision improved the surrounding sentence structure but retained
the residual phrase:

~~~text
以满足 AI 原生时代全新的算力服务需求
~~~

This separates two hypotheses:

1. **Head delay**: a cue such as `面向` or `满足` opens a constituent whose head
   noun arrives only after a long pre-head modifier span.
2. **Low-anchor abstract stacking**: that span contains generic era, novelty, or
   emphasis modifiers without a number, quoted term, or non-generic technical
   identifier that could anchor interpretation.

The second label is only a high-precision candidate description. It does not
establish that a phrase is meaningless.

## Deterministic instance rule

The probe splits text at visible clause punctuation and searches a frozen cue
lexicon including `面向`, `针对`, `围绕`, `满足`, `支撑`, `支持`, and `聚焦`.
Within the clause it locates the last candidate head noun, such as `需求`,
`能力`, `体系`, `架构`, `机制`, `场景`, `路径`, or `流程`.

A candidate has long head delay when the intervening modifier contains at least
eight CJK characters or 12 visible characters. It becomes a low-anchor abstract
stack candidate when it also contains at least two frozen generic modifiers and
no narrow concrete anchor.

The generic list includes era frames and terms such as `全新`, `新一代`,
`核心`, `关键`, `深度`, `全面`, `系统性`, `一体化`, `智能化`, `高效`, and
`原生`. The concrete-anchor rule recognizes numbers, quoted terms, and ASCII
identifiers other than bare `AI` or `Agent`.

## Existing-corpus result

The 50-document fresh post handoff produced 48 cue-to-head instances. Twenty-one
met the broad delay threshold across 10 documents. Manual inspection shows that
the broad set contains false positives because a lexical rule cannot always
identify the true phrase boundary.

Only one instance met the stricter low-anchor abstract-stack rule: the exact
`AI 原生时代全新算力服务需求` passage localized by the reader. Both its
original and its preferred first revision remain strict candidates. This is
useful localization evidence but not replication.

The same frozen rule was then applied without modification to the existing
119-document analysis handoff: 23 pre-period and 96 transition-period
documents. It produced 107 cue-to-head instances and 38 broad delayed-head
candidates across 23 documents, again with phrase-boundary false positives.
It produced zero strict low-anchor abstract-stack candidates. The exact motif
therefore did not replicate in this discovery corpus. This result must not be
used to claim a post-period increase because the strict rule was defined after
the post example and the sources, formats, topics, visibility, and periods are
not matched.

After excluding every document already selected for projects 5, 6, and 7, only
five documents contain broad delayed-head candidates. They all come from the
Meituan source, mostly as technical-practice or section-heading fragments. A
new reader round from that remainder would repeat the source-homogeneity and
passage-quality problems already diagnosed in earlier screens, so no additional
Label Studio project is prepared from it.

A later corpus expansion produced a 97-document, five-source handoff with a
frozen role split. The same rule was applied only to its 67-document development
partition. It produced 45 cue-to-head instances and 23 broad delayed-head
candidates across 14 documents, but again produced zero strict low-anchor
abstract-stack candidates. The 30-document validation reserve was not read.
This additional non-replication preserves the single case as a useful reader
observation but does not justify relaxing the rule or creating another reader
batch.

## Intervention implication

The next bounded operator should unpack rather than merely move the phrase. For
the observed source claim, a proposition-preserving form is:

~~~text
AI 原生时代出现了新的算力服务需求。为满足这些需求，AI 算力池采用……
~~~

This preserves the source's novelty and era claims while exposing their lack of
specific payload as a separate proposition. A stronger deletion or replacement
would change the claim and is not allowed without author approval.

Future admission requires new, complete passages from multiple sources. Each
candidate must contain a frozen cue-to-head delay plus a low-anchor modifier
stack, and each edit must preserve the complete proposition set. Reader input
remains a simple blinded preference; the reader does not label the construction.

## Reproduction

~~~powershell
python experiments/head_final_modifier_probe.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v1 `
  --discovery-pool F:\MyProjects\DeAIodorant\data\local\translation_v2_review\analysis_handoff_v1\analysis_pool.jsonl `
  --integration-answer-key feature_runs/integration-pairs-v1/answer_key.json `
  --integration-results data/annotations/integration-pairwise-v1.json `
  --output-dir feature_runs/head-final-modifier-v1
~~~

The probe uses no model inference. Two runs produced byte-identical outputs:

| Artifact | SHA-256 |
|---|---|
| Corpus instances | `29d68ea788954da61c553b83ee8d8e576d1558c6676a0e87269c43a676b20852` |
| Integration-variant instances | `1676f31f2fc4381547bea1bae23ae2692981e0e0d0b6b94d892955b7a4b6151e` |
| Discovery instances | `5cf9768cf4efc96ed9f27c4eaf9a1bacb6d155e6ecf24eebfa05ebc297f73e96` |
| Summary | `18cc91e02cbff409fbb19e9b0e842bd5f8039f660542ccc5fdf85410f5072f5b` |

Generated instances remain under ignored `feature_runs/` and are not committed.
