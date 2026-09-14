# CPU Stanza Feasibility Result

Date: 2026-09-14. Protocol: `contrast-syntax-feasibility-1.0`.
Status: assistant-assisted parser feasibility and case inspection;
`human_gold: false`. No semantic reviewer outputs were read.

Local parsing is usable for traceable inspection, but these cases do not
establish automatic discrimination between reading defects and ordinary
Chinese constructions. No syntax-error prevalence, writing-quality score,
smell score, authorship classification, or refinement efficacy was measured.

## Execution and artifact identity

The ready run is `reproduction-02/manifest.json`. It used the already installed
Stanza 1.14.0 `zh-hans` / `gsdsimp` models, Torch 2.13.0, CPU only, one PyTorch
computation thread, one interoperation thread, deterministic algorithms, and
seed/PYTHONHASHSEED `20260914`. `DownloadMethod.NONE` and a Python socket audit
guard prevented network use. Model fingerprint:
`5fa23dfff06b543c63ef547b32006bb0a9acdd6bc1a3a1df23d768a171352af9`.
Eight model/resource files are individually hashed. No dependency, weights,
download, GPU, external API call, training, or generated text variant was added.

The purposive full-document selection was frozen before parsing: dense
technical announcement `doc-03`, difficult Cowork example `doc-05`, and
low-marker technical-practice control `doc-11`. These are not representative
samples or a temporal comparison. Cowork retains its existing weak-smell and
difficult-reading interpretation; parser observations do not promote it.

| Packet | Source Unicode characters | Preserved line breaks | Parser sentences | Tokens / words |
| --- | ---: | ---: | ---: | ---: |
| doc-03 | 2,350 | 39 | 32 | 1,125 |
| doc-05 | 4,048 | 57 | 77 | 2,078 |
| doc-11 | 4,900 | 125 | 55 | 2,399 |

These are execution counts, not error denominators. All 164 parser sentences
and 5,602 word records passed source-slice and graph-storage checks: unique word
IDs, valid heads, one root, and no dependency cycles. Passing these checks
establishes well-formed saved output, not a correct linguistic analysis. All
three exact bodies reconstruct from saved sentence slices and source gaps.

The two successful runs took 65.328 and 69.421 seconds including model setup,
hashing, and output. Their body copies, annotation JSON, and CoNLL-U files are
byte-identical in all nine file comparisons. The final run's seven input,
four implementation, eight model, and fourteen output hashes all match.
`reproduction-verification.json` records these checks. This is reproducibility
on this local environment, not a cross-platform guarantee.

The initial attempt stopped before producing document annotations. Its Windows
`os.execve` relaunch detached from tool capture, so the exact failure exception
was unavailable. The driver now waits for its seeded subprocess and stores
private failure details only in an output directory created by that attempt.
The initial state and implementation snapshot remain preserved; no failure
cause is inferred beyond the observed process/capture behavior. Direct process,
CPU, progress-artifact, and final-exit checks are recorded in `monitoring.json`.

## Six source-anchored cases

`inspection.json` preserves exact quotes, Unicode offsets, complete source
sentence references, relevant UD word records, contextual support, and the
assistant's reasoning for each case. Full originals and all annotations remain
under `reproduction-02/<alias>/`.

| Packet / parser sentence | Concrete source observation | Parser behavior and limit |
| --- | --- | --- |
| doc-03 / s012, awkward | `无法确定不确定` stacks two uncertainty predicates in a locally difficult construction. | Both occurrences of `确定` receive nested `xcomp` edges beneath `无法`. A complete tree does not decide whether the repetition is intended or accidental. |
| doc-03 / s026, control | The second item in an announced two-part explanation shares its actor with the preceding introduction. | The parser splits technical `路由` into `路` and `由`, assigning the latter a verb relation, and tags `设计` as a noun. An ordinary construction can therefore contain misleading parser structure. |
| doc-05 / s074, awkward | The sentence moves between comments, users, a nominal expression of dissatisfaction, and an unclear final relevance relation. | `用户` becomes a nominal modifier of `不满`, while `具有` receives a separate complement attachment. The tree accommodates the wording without resolving its reference or discourse relation. |
| doc-05 / s060, control | `其次是新增的一系列技能` is an ordinary nominal item in a list of extensions. | `技能` is root, `是` is copula, and `其次` is represented as a subject. This does not establish a missing-subject error. The source newline before the full stop is retained without splitting this sentence. |
| doc-11 / s029, awkward | The captured string `资源隔离通过将` runs an operation into a following means clause with an unclear boundary. | The heading is fused with the paragraph; heading `优势` becomes a subject of root `模式`, and `解耦` is attached under `进行`. This supplies one parse without diagnosing the boundary or its source/capture origin. |
| doc-11 / s022, control | `最终采用后者作为临时方案` has a recoverable actor and an explicit preceding pair of alternatives. | Main root `解决` and action `采用` have no overt `nsubj` dependents. Their absence is compatible with ordinary discourse ellipsis. |

These examples support inspection of proposed attachments, not a classifier or
an operational defect rule. The parser does not recover the missing discourse
premises or intended references needed to resolve the awkward Cowork case.
No facts or premises were invented to make a repair possible, and no repair
was generated.

## Segmentation and token-surface limits

In `doc-11-s045`, one parser sentence spans source offsets `[3425, 3861)`: the
SQL introduction, the full code block, the copy-code label, the next heading,
and the next prose sentence. The subsequent prose is attached to the
code-introduction root. This materially limits any clause- or sentence-based
interpretation on unchanged collector text.

There are fourteen token surface/source-slice discrepancies: one in each of
`doc-03` and `doc-05`, and twelve in `doc-11`. Each also appears in the aligned
word record, producing the stored issue counts 2, 2, and 24. These are not
fourteen syntax errors or invalid numeric offsets. Thirteen discrepancies
involve joined whitespace or line breaks, including a URL section and SQL.
One `doc-11` token even merges caption-ending `倍` with the next heading number
`02` into `倍02`. The remaining discrepancy is more severe: the entire
207-character final URL block in `doc-05`, source offsets `[3841, 4048)`, becomes
a single literal `<UNK>` token. Parser token text therefore cannot substitute
for source evidence. Exact source spans are retained alongside all transformed
token forms, so every discrepancy stays inspectable. All parser sentence text
slices themselves match the original spans.

The bounded next use is an inspection aid: first verify the relevant source
span, segmentation, and technical-token treatment, then assess the construction
in its full article. Automatic quality scores, missing-subject rules, training,
and edits remain unsupported by this feasibility result.

## Reproduction

The final successful command was:

```powershell
python experiments/contrast_syntax_feasibility.py --model-dir models/stanza --output-dir data/local/contrast-syntax-v1/reproduction-02
```

That directory is immutable. A future repetition requires a new output
directory. `build_inspection.py` records the separately authored case selection
and evidence extraction; it performs no new inference. `inspection-manifest.json`
binds the report and inspection artifacts to the final parser manifest and
annotation inputs.
