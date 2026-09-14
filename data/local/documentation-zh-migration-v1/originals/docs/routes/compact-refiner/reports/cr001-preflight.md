# CR-001: Autonomous Editing Preflight

Date: 2026-09-14. Route: `compact-refiner-v1`. Status: model-assisted development
experiment; human preference and training acceptance remain unmeasured.

## Question and interpretation boundary

Can this pipeline produce reviewable, meaning-preserving editing proposals,
and what fails before any SFT investment? This run does not estimate natural
smell prevalence, establish reader preference, train a model, or validate an
NLP reward. All semantic/editorial assessments are model-assisted, including
assessments performed by separate agents.

The numerical results below belong to a small constructed development sample.
They do not establish the general capability of all models at a parameter size.
Assistant proposals and their review use related underlying model capabilities;
separate agents and hidden identities do not make their errors independent.

## Inputs and execution

Twenty-four independently constructed factual briefs cover four genres, six
each: technical explanation, practical instructions, evidence-based analysis,
and workplace/public communication. All names/events are fictional. The briefs
contain 158 fact-inventory entries and two exact locked sentences. Every group
is development-only; no legacy reserve or final test was opened.

The two draft generators were `deepseek/deepseek-v4.1-flash` and
`qwen/qwen3.8-27b`, assigned alternately within genre. Generation used the frozen
ordinary-task prompt, temperature 0.4, maximum 2048 output tokens, requested
seed 20260914, and reasoning disabled. We did not ask for bad prose or regenerate
valid outputs until they contained a desired marker.

One source request, `cr001-23`, remained unavailable after HTTP 429 responses,
including a documented single-attempt recovery after more than 120 seconds.
It received no fabricated text or semantic label. Source 24 succeeded with its
original assigned model and request. The result is 23 actual drafts from 24
planned groups; all groups remain in the accounting denominator.

Source inspection and API attrition led to a separately frozen editing-stage
manifest before compact-model outputs. This is an explicit operational amendment
after source outcomes, not a claim of untouched confirmatory preregistration.
The initial source manifest and failed attempts remain preserved.

## Source-only review before edits

A separate agent compared the source drafts with their complete fact packets
before seeing edits. Generator identities were omitted from the review inputs.
A second agent reviewed six cases selected by fixed hash without the first
agent's labels. Their source-fidelity classifications agreed on all six.

| Source disposition | Count | Clear editing opportunity | Limited opportunity | No clear opportunity |
|---|---:|---:|---:|---:|
| Model-assisted pass | 13 | 4 | 3 | 6 |
| Model-assisted fail | 7 | 6 | 1 | 0 |
| Uncertain | 3 | 2 | 1 | 0 |
| API unavailable | 1 | Not assessed | Not assessed | Not assessed |

Examples of source defects include omitted requirements, added procedural
obligations, stronger frequency/possibility claims, and advancing an operational
status from waiting for contact to active contact. These are source-generation
defects, not failures introduced by the compact editor.

Eight of the twelve source drafts with a model-diagnosed clear editing
opportunity were source-failed or uncertain. This is a consequential selection
issue: improving those drafts by repairing content would not demonstrate a
style-preserving edit. Meanwhile, six of thirteen admissible drafts had no
clear editing need. The short, fully specified tasks may be poor coverage of
real editing demand. The result does not justify manufacturing worse inputs.

## Matched-input candidate comparison

For the thirteen source-pass drafts:

- U retained the exact original;
- P used `mistralai/ministral-3b-2512` with the frozen editor prompt,
  temperature 0, maximum 2048 output tokens, and seed 20260914;
- T was one proposal by a fresh agent that had not read briefs, fact inventories,
  source assessments, P outputs, or historical examples. It received only the
  same fully rendered editor inputs as P.

P and T input-prompt hashes match for all thirteen items. T is a model-assisted
editing proposal, not a human-edited upper bound. Its internal deliberation,
latency, and cost are unavailable, so this is not a controlled compute-budget
comparison with a single hosted request.

The candidate reviewer received originals, candidate texts, legitimate context,
and locks with author/model identities hidden. Six constructed semantic controls
were intermixed and excluded from study counts. All six controls were classified
as expected. A second agent reviewed six fixed-hash-selected actual candidates,
covering five distinct original drafts.

| Arm | Actual candidates | Primary preservation pass | Primary fail | Exactly unchanged |
|---|---:|---:|---:|---:|
| P: untuned Ministral 3B prompt | 13 | 2 | 11 | 0 |
| T: fresh-agent proposal | 13 | 13 | 0 | 3 |

The secondary candidate review agreed on five of six fidelity classifications.
The remaining case was a primary failure versus secondary uncertainty, not an
accepted edit under either review. The two model-diagnosed clear T improvements
both passed secondary review. This limited cross-check does not certify the
remaining candidates or replace a human judgment.

Primary editorial diagnoses, distinct from preservation, were:

| Arm | Clear | Limited | None | Regression |
|---|---:|---:|---:|---:|
| P | 0 | 1 | 5 | 7 |
| T | 2 | 8 | 3 | 0 |

One P candidate passes preservation but is judged stylistically worse, illustrating
why fidelity and usefulness cannot be a single automatic label. None of these
editorial diagnoses is a measured reader win.

## Concrete failures and useful proposals

The 3B candidates include the following model-reviewed failures:

- replacing a known count of two pictures with an `X` placeholder and adding
  a deadline and new instructions;
- reversing the condition under which an existing link remains available;
- turning one continuous closure interval into a recurring daily interval;
- converting absence of consent into explicit refusal;
- dropping a permission-independent access guarantee or a service limitation.

Two candidates also violate an exact locked sentence. Fee wording in one of
them loses the "additional" qualification; the semantic interpretation is
ambiguous, so the definite exact-lock failure and the possible scope expansion
must not be conflated. Output-format violations, such as added editing commentary,
are recorded separately from changed factual claims.

Three primary P failures did not trigger the implemented numeric/protected-literal
warning checks (`cr001-01`, `cr001-03`, `cr001-14`). One preservation-passing P
candidate did trigger a literal warning. These are evidence of the checks'
incompleteness and need for contextual review, not estimates of a validated
semantic detector's precision or recall.

Two T proposals address independently observed local issues clearly according
to both model reviewers:

- `cr001-08`: move number-mismatch handling and carrying requirements before
  the hanging step, while retaining counts, roles, and the completion condition;
- `cr001-12`: replace the awkward invitation involving "quiet eyes and ears"
  with a concrete observation/listening instruction, preserving the exercise's
  privacy and measurement limits.

Most other changes are tightening or formatting. Three T cases return the
original exactly. These are useful proposals for human discussion, not proof
that the route has learned to remove a general smell.

## Additional capacity control: CR-001B

The initial result could reflect a poor student choice rather than a general
need for SFT. A separate exploratory follow-up therefore applies
`qwen/qwen3.5-9b` to the exact thirteen editor inputs. It is a Chinese-capable
capacity control, not a selected final student or a substitution for P.

Its manifest was frozen before calls, after the initial preflight observations.
All thirteen requests succeeded on one attempt, with no cache reuse or retries,
and returned Qwen3.5-9B through Darkbloom. Added reported cost was USD 0.00100229.
The Qwen candidates are evaluated by a fresh identity-blinded agent using the
same semantic controls. Interpretation must allow differences in architecture,
language training, provider, and review agent as well as parameter count.

The fresh review agent classified all six controls as expected. On the thirteen
actual Qwen candidates, preservation dispositions were eight pass, two fail,
and three uncertain. Editorial diagnoses were zero clear, four limited, six
none, and three regressions. The two failures narrow a no-seed attendance
permission into a condition about seed ownership and omit two distinct study
limitations. Uncertainties concern actor/scope qualifiers and an added automation
claim. These judgments remain model-assisted.

The result weakens a blanket conclusion that compact API models cannot follow
the contract: this control performs materially differently from the 3B baseline
on the reviewed items. It also does not establish that a 9B model is the right
student or that larger size caused the difference. Different model families and
review agents are confounded. No fine-tuning gain has been measured; all API
models in this run are untuned baselines.

## Cost and operational findings

Across smoke checks, source generation, P, and CR-001B: 52 successful API attempts
reported USD 0.01012750. Ten HTTP 429 attempts had unknown billing; conservatively
accounted total, including their reservations, is USD 0.05459170 under the USD 5
working cap. Agent deliberation is not included or represented as free API use.

The client preserved price ceilings, exact request identities, response metadata,
spend reservations, failure records, and cached successes. Process/artifact
checks established progress and termination independently of any watcher. No
overlapping cache writer, model download, local SFT, or cloud GPU job occurred.

The first client version did not respect/preserve Retry-After headers. The run
retains that operational limitation. Later stages used zero automatic retries;
a separately versioned client maintenance change addresses server-directed
backoff after all inference finished. Exact pre-maintenance code and inputs are
archived, so the correction does not retroactively change the experiment.

The [maintenance record](../client-maintenance-2026-09-14.md) documents the fix.
The final implementation passed 113 offline tests and the required compilation
checks. Record/hash validation, Markdown links, JSON parsing, ignore rules, and
credential exclusion also passed. These checks do not validate reader benefit.

## Decisions

Do not start SFT or request a GPU from these results alone. Prioritize three
concrete questions: choose a Chinese-capable student baseline; establish whether
humans prefer the few safe proposals with an identifiable benefit; and collect
accepted edit/no-edit pairs with reliable semantic review. The 3B failures do not
show that all compact models fail, and the T passes do not show that a small
student can learn them from a few hundred examples. Preserve scope, conditions,
and unchanged behavior as explicit training-data concerns rather than rewarding
surface marker deletion.

Retain both accepted-looking and failed proposals, unchanged cases, source
quarantine, and API attrition. No SFT or DPO record is eligible without the
human evidence required by the data contract. A three-pair qualitative reader
preview is prepared from two clear T proposals and a smaller edit. It is
post-review selection for discussion, not a held-out benchmark or a model ranking.

## Reproduction identity

| Artifact | SHA-256 |
|---|---|
| Constructed briefs | `23f7d43004c672e53e1269e12be14e7990f81e738ef29701d23d386edb713932` |
| Live model catalog | `6875124fd348cbf584154a4413b8cd8cd01122f0563e048689546a13aa740f2b` |
| CR-001 source manifest | `349e9cc728e03c66ab9756269188d8cd9dfa51cc0dc980748e6b168dd6d69295` |
| Editing-stage manifest | `357ae56874a3be36da362c7841842c6d02fbf279a5c6c8218b64fd23fe0f29f2` |
| CR-001B manifest | `ad0c780be078516d97fdd9845ca02a3295708f126d8d3845ac9d3782cfabf998` |

Private artifacts are under `data/local/compact_refiner/cr001-v1/` and
`feature_runs/compact_refiner/`. Exact old code/inputs are under
`feature_runs/compact_refiner/cr001-code-snapshot/`. Current code may have newer
operational safeguards; reproducing a frozen run requires its isolated code
snapshot rather than silently updating its hashes or reusing its final outputs.

Commands actually used included:

```powershell
python experiments/compact_refiner_run.py prepare --run-root feature_runs/compact_refiner/cr001-v1 --dataset-root data/local/compact_refiner/cr001-v1 --briefs experiments/fixtures/compact-refiner/briefs.v1.jsonl --catalog feature_runs/compact_refiner/cr001-catalog-20260914/models.json
python experiments/compact_refiner_run.py generate --run-root feature_runs/compact_refiner/cr001-v1
python feature_runs/compact_refiner/cr001-v1/recover_sources.py
python experiments/compact_refiner_edit_stage.py prepare
python feature_runs/compact_refiner/cr001-edit-v1/run_verified.py
```

The generation command terminated on the documented source-23 API failure.
Recovery and the separate edit stage are explicit deviations, not a claim that
the original command completed all twenty-four drafts. Agent assessments and
proposals retain their own input/output hashes and provenance; they are not
reproducible by replaying an invented human annotation command.
