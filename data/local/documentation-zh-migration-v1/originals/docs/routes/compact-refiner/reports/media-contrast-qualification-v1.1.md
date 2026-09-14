# Media Contrast Source Qualification v1.1: Evidence Correction

Date: 2026-09-14. Review version:
`media-contrast-source-qualification-1.1-policy-correction`.
Status: model-assisted provenance review, not human gold. This addendum preserves
[v1](media-contrast-qualification-v1.md) as an audit record and supersedes its
pair-03-A and pair-03-B deterministic-exclusion judgments. Those two v1 judgments
must not be used as active findings.

The earlier review overclaimed what foreign-source attributions established.
Both pair-03 articles visibly depend on foreign information sources, but neither
supplied body proves that the article as a whole translates or closely compiles a
specific foreign work. Both are now **uncertain/pending review**, with formal
corpus admission still withheld. This corrects evidence strength; it does not
relax admission or change the translation policy.

## Policy basis

`pilot_collect.py`, method `prompt_verifier`, explicitly permits Chinese
summaries, commentary, and reporting based on
foreign papers, product announcements, and news. It rejects using foreign links,
names, or terminology alone as translation evidence and allows original
multi-source analysis. The correction concerns that method's text at lines
226-247, not a new prompt or rule.

[Translation gate benchmark v2](../../../translation-benchmark-v2.md), under
"Candidate and label tiers," likewise includes independently synthesized Chinese
work in reviewed originals. Under "Model-assisted triage," it requires evidence
of a specific non-Chinese source work before confirming an exclusion. A Chinese
byline alone also cannot establish independent original composition. No prompt,
threshold, benchmark input, or gold label was changed.

## Corrected article findings

| ID | Direct observation | What remains inferred or unresolved | Active disposition |
|---|---|---|---|
| pair-03-A | Recurring Bloomberg/New York Times attributions; references to several foreign reports, tweets, and biographical material; attributed quotations. | Whether the Chinese author independently organized and wrote the multi-topic report or followed specific foreign works closely. Citations and source dependence do not resolve this. | Uncertain/pending; no deterministic translation exclusion; no formal admission. |
| pair-03-B | A bounded quotation attributed to Boris Cherny; reported official product statements; Reddit reaction summaries and foreign-source links. | Whether the surrounding Chinese explanation independently synthesizes these sources. A translated quotation inside an article is not proof that the whole article is a translation. | Uncertain/pending; no deterministic translation exclusion; no formal admission. |

No explicit document-level translation evidence was located in the supplied six
articles: no translator field, translation/compilation publication label, paired
foreign-original-author biography and original-work link, or identifiable foreign
interview transcript adaptation. Pair-03-B's quoted announcement is an observed
foreign-source dependency, not a whole-document translation label. Pair-01-B's
English quotations with Chinese renderings likewise do not classify its
surrounding first-person essay. None of the linked foreign works was fetched or
compared for textual correspondence.

The Chinese bylines do not settle pair-03 originality. Their Chinese explanatory
organization is compatible with independent synthesis, but the degree of original
composition is unresolved from the reviewed evidence. The private v1.1 JSON
separates observed dependencies, independent-synthesis indicators, inferred
whole-article compilation, and remaining uncertainty instead of compressing them
into an unsupported exclusion verdict.

The other four dispositions remain unchanged: pair-01-A, pair-01-B, and pair-02-B
have provisional model-assisted original-language support using their recorded
interview or domestic first-party context and source linkage together; pair-02-A
remains plausible original with unresolved attribution. The six records now have
three supported originals, one plausible original with attribution uncertainty,
two pending originality judgments, and **zero deterministic translation or
compilation exclusions**. All remain unadmitted staging material.

Substantive-content findings and presentation limits remain in force. Pair-03-A
and pair-03-B may be retained for provisional textual inspection with provenance
clearly pending. They cannot be presented as verified original-language corpus
members. The technical articles' unreviewed figures and flattened code still
limit whole-article presentation. No human validation, writing-style ranking,
target-intensity label, authorship label, verified training license, or source
rewrite was added.

## Audit and verification

The input packet and six presentation hashes are unchanged. The separate private
output is `data/local/media-contrast-review-v1/qualification-review-v1.1.json`.
It records the v1 JSON/report hashes, policy-file hashes, corrected fields, and
reason for correction. The v1 files were checked unchanged after the new outputs
were written. Evidence quotations and presentation hashes were rechecked against
the original six-article packet. Policy documents were read; no external article,
image, benchmark-data artifact, API, or gold-label artifact was consulted.
