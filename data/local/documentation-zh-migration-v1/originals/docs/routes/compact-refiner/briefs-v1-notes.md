# CR-001 Constructed Briefs: Version 1

Fixture version: `compact-refiner-briefs-1.0`  
Date: 2026-09-14  
Role: development only  
Author: assistant subagent `development_briefs`  
Fixture: `experiments/fixtures/compact-refiner/briefs.v1.jsonl`

## Status and interpretation

The file contains 24 purpose-written fictional briefs, with six briefs in each
of the four genres specified in [CR-001](first-batch.md). Each brief has a
distinct task-group ID, topic, and fact packet. These are constructed fixtures,
not sampled publications or evidence of natural writing-pattern prevalence.
Every entity, measurement, event, and situation is fictional. No historical
corpus, legacy reserve, sealed test, real personal information, or external
source text was used to construct the file.

The fact packets, required-fact statements, and risk notes are agent-authored.
They are **not independent human gold labels**, reader judgments, or proof of
semantic preservation. A source draft must still be checked for consistency;
a later edit must preserve its actual source rather than use the packet as
permission to add information missing from that source. Human acceptance and
preference gates remain separate.

All tasks request ordinary Chinese prose of 300-600 Chinese characters. No task
asks for a bad draft, a target smell marker, a particular NLP score, or a
recognizable model style. The requested audiences and voices are legitimate
writing requirements. Retain valid already-good drafts and no-edit outcomes.

The fixture is an authoring input to dataset materialization. It is not yet a
complete `briefs.jsonl` dataset artifact: dataset version, creation timestamp,
rights evidence, and canonical per-record hashes are added by the materializer
under the [data contract](data-contract.md). All 24 groups must be assigned to
development before any variant is generated. Derived texts do not create new
independent groups.

## Construction choices and boundaries

Each packet supplies a complete, compact set of fictional facts. Its
`required_facts` array gives an English audit description of those same facts;
it does not introduce additional factual requirements. These statements and
their IDs are audit metadata, excluded from ordinary generation and editor
inputs. `protected_literals` provide a bounded literal screen, mainly for
names, quantities, and status labels. A retained number with a changed subject
or denominator can still be a semantic failure. A changed surface spelling of
the same quantity requires interpretation rather than automatic certification.

The two exact locked sentences belong to briefs 19 and 20. Both also occur in
their fact packets, and both generation instructions request the exact
sentence. Other source phrasing is editable subject to semantic preservation;
an empty literal list does not mean a fact is optional. All packet facts are
explicitly in scope through the shared read-only context.

The packets contain 208-268 Unicode code points, including 176-225 CJK
characters. These are compact fact packets, not completed requested passages.
The prose target is not a demand to pad a draft with new facts or generic
framing. Downstream length handling must be reported independently of source
fact consistency; do not silently regenerate a valid draft because it is
already clear or lacks a proposed pattern.

The sample deliberately covers conditions, exceptions, measurement limits,
attribution, and unresolved decisions. It therefore overrepresents explicit
preservation challenges relative to an unknown deployment distribution.
Community, cultural, and workplace settings are prominent. There is no claim
of topic representativeness, and the batch does not test long-form narrative,
personal literary voice, high-stakes advice, or open-ended factual generation.
The generic context sentence and prose-only format are shared instructions;
the underlying events, factual relationships, and workflows are independently
constructed. Surface distinctness does not itself establish statistical
independence or future generalization.

## Coverage and prospective semantic risks

The failures below are prospective review prompts. They are not findings about
any generated output, preferences, or validated smell categories.

| Brief | Genre | Main distinction or dependency | Concrete possible semantic failure |
|---|---|---|---|
| 01 | Technical explanation | Offline availability, opt-in updates, and fresh closure information | Turn absent location permission into an unusable map; infer reopening from stale closure data; promise automatic updates. |
| 02 | Technical explanation | Interval sum, missing observations, and late uploads | Treat missing intervals as zero; replace the sum with an average; describe a delayed upload as rain at upload time. |
| 03 | Technical explanation | Published page versus search index; ranking versus review | Say the linked page is unpublished; equate high rank with approval; describe an old snippet as current document content. |
| 04 | Technical explanation | A single controlled demonstration and limited mechanism | Exchange the two measured temperatures; promise a universal temperature gap; extend the test to lidded or drop-resistant behavior. |
| 05 | Technical explanation | Capture interval versus playback rate | Claim slower playback recovers unsampled actions; reverse the resulting duration; invent a universal ideal capture interval or on-site sound. |
| 06 | Technical explanation | Color proof versus final content approval | Treat a paper proof as approval of unproofread names; equate color adjustment with increased resolution; carry approval to a different paper. |
| 07 | Practical instructions | Household and per-kind caps, optional contribution, uncertain labels | Turn maximums into required amounts; exclude people bringing no seeds; replace an unknown month with a guess or volunteer certification. |
| 08 | Practical instructions | Full precheck before staff hanging; role-specific review | Let volunteers install hooks; hang each photo before the complete check; collapse separate sequence and label responsibilities; open unchecked work. |
| 09 | Practical instructions | Backup, attribution of conflict, explicit confirmation | Overwrite originals; choose a conflicting account by plausibility; interpret silence as approval or substitute the planned date. |
| 10 | Practical instructions | Optional second color and a condition beyond elapsed time | Require yellow; allow overlay solely because ten minutes elapsed; replace next-day collection with immediate collection; promise wash durability. |
| 11 | Practical instructions | Registration versus acceptance and distinct pending dispositions | Accept all registered books; alter a written telephone number; confuse return and pending boxes; count a title once regardless of copies. |
| 12 | Practical instructions | Observation examples versus expected data; early-exit choice | Demand recordings or conversations; require all example sounds; omit actual shorter duration; extrapolate the walk to all-day noise levels. |
| 13 | Analysis/commentary | Median, voluntary observations, time-of-day imbalance | Call the statistic a mean; attribute the whole difference to the new schedule; treat people abandoning the queue as recorded; claim satisfaction. |
| 14 | Analysis/commentary | Completer, outline user, and survey-response denominators | Apply the 42 positive replies to all visitors; claim random assignment or a proven completion-rate improvement; equate feedback with comprehension. |
| 15 | Analysis/commentary | Repeated occupied-seat snapshots versus unique people | Sum repeated observations into unique users; infer unobserved weekend demand; present the proposed trial as approved or its benefit as certain. |
| 16 | Analysis/commentary | Total leftovers versus plate effect under unequal menus | Ignore bones, meal counts, or menus; claim the small plate caused the reduction; infer equal satiety from absent feedback. |
| 17 | Analysis/commentary | Actual use count versus conditional projection; board mass versus emissions | Describe 18 outings as observed; omit repairs after the first outing; present the mass ratio as a measured carbon reduction. |
| 18 | Analysis/commentary | Recorded categories, uncertain identification, and changed observation conditions | Count uncertain records as species; attribute observations only to water trays; equate sightings with resident birds or breeding. |
| 19 | Workplace/public communication | Slot cap after cancellations, confirmation, and a time-limited pilot | Count canceled slots against the cap; admit waitlisted applicants; promise permanence; change the locked entry sentence or cancellation lead time. |
| 20 | Workplace/public communication | Partial closure, step-free alternate room, and conditional reopening | Close the whole building; reverse directions; extend every loan rather than only due dates in the closure window; promise unconditional reopening. |
| 21 | Workplace/public communication | Confirmed dimensions gate an orderable print list | Make the Friday deadline unconditional; permit estimated dimensions; treat the current draft as final cutting approval; demand repeated completed work. |
| 22 | Workplace/public communication | Conditional venue change and retained registration | Announce cancellation; invent a weather forecast; require re-registration; treat nonresponse as withdrawal or invite walk-in places. |
| 23 | Workplace/public communication | Corrected counting label versus unchanged occasion total | Replace 96 check-ins with 71 check-ins; call 71 all attendees; invent recovered paper copies, excuses, or new feedback collection. |
| 24 | Workplace/public communication | Preferences versus confirmed roles; voluntary extra coverage | Report all 16 assignments as complete; make a morning extension mandatory; treat a request as confirmation; publish contact details. |

The six analysis packets use different substantive settings and measurement
problems, but share deliberate caution about evidence. Their caveats are source
meaning to preserve, not a target style to penalize. Similarly, repeated
negative or conditional structures across practical notices are often necessary
instructions, not predetermined editing opportunities.

## Validation and freeze identity

The frozen UTF-8 file has LF line endings, no byte-order mark, and a terminal
newline. Each JSON object occupies one line.

| Check | Result |
|---|---|
| Records, distinct brief IDs, distinct task groups, distinct topics | 24 each |
| Technical explanation | 6 |
| Practical instructions | 6 |
| Evidence-based analysis/commentary | 6 |
| Workplace/public-facing communication | 6 |
| Required-fact objects and unique fact IDs | 158 |
| Nonempty locked-content fields | 2 |
| Protected literals present in their corresponding fact packets | All |
| Explicit constructed origin, rights status, and no personal data | All 24 |
| Exact duplicate fact packets | 0 |
| Largest pairwise CJK character 5-gram Jaccard similarity | 0.005025125628140704, briefs 08 and 11 |
| File size | 68,991 bytes |
| SHA-256 | `23f7d43004c672e53e1269e12be14e7990f81e738ef29701d23d386edb713932` |

The Jaccard screen strips non-CJK characters and compares sets of contiguous
five-character strings within each packet. It excludes shared instruction and
context boilerplate. It is only a cheap surface-duplication screen. The
conceptual coverage inspection above is agent review, not an independent audit.

Before freezing, construction review clarified three ambiguous statements:
the two post-installation reviewers have separate duties (08), repairs are
counted after every outing including the first (17), and canceled reservations
do not consume the weekly cap (19). These changes preceded source generation.
After freezing, corrections require a new fixture version and a recorded
departure rather than silently changing this file.

The file was authored through local Python JSON serialization with
`ensure_ascii=False`, compact separators, UTF-8 encoding, and `newline="\n"`.
No external inference request was used for fixture construction. The essential
identity and count checks can be reproduced from the repository root:

```powershell
@'
import collections
import hashlib
import json
from pathlib import Path

path = Path("experiments/fixtures/compact-refiner/briefs.v1.jsonl")
raw = path.read_bytes()
rows = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
assert len(rows) == 24
assert len({row["brief_id"] for row in rows}) == 24
assert len({row["task_group_id"] for row in rows}) == 24
assert len({row["fact_packet"] for row in rows}) == 24
counts = collections.Counter(row["genre"] for row in rows)
assert sorted(counts.values()) == [6, 6, 6, 6]
assert not raw.startswith(b"\xef\xbb\xbf")
assert b"\r" not in raw and raw.endswith(b"\n")
for row in rows:
    assert row["rights_status"] == "project_constructed"
    assert row["content_origin"] == "project_constructed_fixture"
    assert row["contains_personal_data"] is False
    assert row["locked_content"] in row["fact_packet"]
    for fact in row["required_facts"]:
        for literal in fact["protected_literals"]:
            assert literal and literal in row["fact_packet"]
print(dict(counts))
print(hashlib.sha256(raw).hexdigest())
'@ | python -
```

Downstream manifests must record their own prompt, model, provider, decoding,
cost, generation, exclusion, and review identities. This note establishes the
fixture provenance and limits, not an experiment outcome or training readiness.
