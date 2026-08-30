# Frozen Post Development Motif Inventory

## Status

Protocol `post-development-motif-inventory-0.1` is frozen before its rules are
applied to the 67-document development partition. The 30-document validation
reserve is not opened.

## Purpose

The inventory asks whether narrow, deterministic surface motifs recur often
enough to justify manual candidate auditing. It does not detect AI authorship,
assign reader dislike, or promote any motif to a refinement rule.

Five candidate families are recorded:

1. the existing complete negative contrast frame;
2. an existing emphatic marker followed by a short, anchor-free payload with
   at least two existing abstract-shell terms;
3. three existing abstract-shell terms whose span contains at most 24 visible
   characters and no number, quoted phrase, or non-generic ASCII term;
4. a sentence-level dense-clause proxy requiring at least 55 CJK characters,
   four clause separators, two abstract-shell terms, and two explicit
   connectives;
5. the already frozen strict delayed-head, low-anchor abstract-stack rule.

The lexicons come from the existing discourse-graph and delayed-head probes.
Thresholds are constants in the script and must not be relaxed after results
are viewed.

## Frequency gate

A motif can proceed to manual coherence review only when it appears in at least
six independent documents across at least three sources. Passing this gate is
necessary, not sufficient. A reader intervention additionally requires a
single coherent construction, a bounded edit operator, a structured operation
log, and the existing meaning-preservation checks.

## Reproduction

~~~powershell
python experiments/inventory_post_development_motifs.py `
  --handoff-root F:\MyProjects\DeAIodorant\data\local\post_reader_handoff_v2 `
  --output-dir feature_runs/post-development-motif-inventory-v1
~~~

Generated candidate text remains under ignored `feature_runs/`. The repository
records only the frozen rules, aggregate interpretation, and artifact identity.

## Result

The scan opened all 67 development documents and no reserve document. It found
146 instances in total.

| Motif | Instances | Documents | Sources | Frequency gate |
|---|---:|---:|---:|---|
| Complete contrast frame | 124 | 37 | 5 | Pass |
| Abstract-shell cluster | 14 | 12 | 4 | Pass |
| Dense-clause surface proxy | 4 | 4 | 3 | Fail |
| Emphatic abstract payload | 4 | 3 | 2 | Fail |
| Strict delayed-head low-anchor stack | 0 | 0 | 0 | Fail |

Frequency did not produce an intervention candidate. All 14 abstract-shell
clusters were inspected. They mix repeated literal senses such as boundary
analysis, normal technical terms, list fragments, and unrelated shell-noun
uses; they do not describe one editable construction.

For the much larger contrast set, a deterministic source-stratified audit took
the first six instances from each source, or every instance when a source had
fewer than six. The sample contains genuine alternatives, mechanism
distinctions, quoted definitions, benchmark criteria, and source fragments in
addition to possible rhetorical framing. Exact marker presence therefore does
not isolate ornamental contrast. This reproduces the selection-precision limit
seen in the third intervention rather than supplying a new intervention set.

No Project 8 is prepared from this inventory. The frequency gate remains fixed,
and neither the shell rule nor the contrast rule may be relaxed or semantically
relabeled against these results.

## Artifact identity

| Input | SHA-256 |
|---|---|
| Handoff manifest | `ecab7336c2ca54f59d24b79bcb841f0d3f4085a9c80a117f5a3ea0e31fec5d01` |
| Document index | `096a4e42a947c1cc7e60c17b0b91251fd83579e682bdf8ea7bb0e15aed3fbd80` |

## Independent discovery replication

The same frozen rules were later applied to all 93 documents in
`post_reader_handoff_v3`. Those documents were assigned to a discovery reserve
before the scan. The scan therefore makes them feature-discovery exposed; they
cannot now be used as validation or final-test material.

| Motif | Instances | Documents | Sources | Frequency gate |
|---|---:|---:|---:|---|
| Complete contrast frame | 131 | 44 | 3 | Pass |
| Abstract-shell cluster | 20 | 13 | 3 | Pass |
| Dense-clause surface proxy | 2 | 2 | 1 | Fail |
| Emphatic abstract payload | 2 | 2 | 2 | Fail |
| Strict delayed-head low-anchor stack | 0 | 0 | 0 | Fail |

The strict delayed-head motif fails to replicate again. The shell-cluster
instances again mix repeated category labels, literal technical senses,
coordinate lists, and ordinary uses of polysemous shell terms. Their increased
frequency does not repair the rejected selector. Complete contrast remains
frequent but semantically heterogeneous. No Project 8 is prepared.

| Input | SHA-256 |
|---|---|
| v3 handoff manifest | `5462a30c6c9d8e598fd1f8f6af567bbb4d4efbcc7cc30e3bfd36d4965225ebac` |
| v3 document index | `dd2d3b3f99d17c2fe7179e8fcdeb7f31e5036a7d7b117ed819e12825eacd4a4d` |
