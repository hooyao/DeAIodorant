"""One documented post-cooldown recovery; no automatic retries."""
from pathlib import Path
import datetime as dt
import json

from deaiodorant.refine.openrouter import OpenRouterClient
from deaiodorant.refine.records import append_jsonl, load_jsonl, render_prompt, text_hash, make_candidate, literal_diagnostics, validate_saved_records

run = Path('feature_runs/compact_refiner/cr001-v1')
data = Path('data/local/compact_refiner/cr001-v1')
manifest = json.loads((run / 'manifest.initial.json').read_text(encoding='utf-8'))
decision = json.loads((run / 'recovery-decision.json').read_text(encoding='utf-8'))
elapsed = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(decision['last_failure_at_utc'])).total_seconds()
if elapsed < decision['minimum_cooldown_seconds']:
    raise SystemExit('Required cooldown has not elapsed.')
briefs = load_jsonl(data / 'briefs.jsonl')
drafts = load_jsonl(data / 'drafts.jsonl')
validate_saved_records(drafts, load_jsonl(data/'candidates.jsonl'), briefs)
seen = {row['brief_id'] for row in drafts}
client = OpenRouterClient(Path('.env'), run/'api-cache', '4', timeout_seconds=120, max_retries=0)
template = Path('docs/routes/compact-refiner/prompts/draft-v1.txt').read_text(encoding='utf-8')
for brief in briefs:
    if brief['brief_id'] == 'cr001-23' and (run/'source-disposition-23.json').exists():
        continue
    if brief['brief_id'] in seen or brief['brief_id'] not in decision['remaining_source_ids']:
        continue
    model = manifest['generator_assignments'][brief['brief_id']]
    prices = manifest['models'][model]['pricing']
    prompt = render_prompt(template, brief)
    result = client.complete(model, [{'role':'user','content':prompt}], prices['prompt'], prices['completion'], max_tokens=2048, temperature=0.4, reasoning={'enabled':False}, seed=20260914, purpose='recovery:'+brief['brief_id'])
    draft = {'schema_version':manifest['schema_version'],'draft_id':brief['brief_id']+'-draft','brief_id':brief['brief_id'],'task_group_id':brief['task_group_id'],'genre':brief['genre'],'split':'development','draft_text':result['text'],'draft_sha256':text_hash(result['text']),'prompt_sha256':text_hash(prompt),'generator':model,'inference':result['metadata'],'generated_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'fact_packet_consistency':'awaiting_model_assisted_review','human_gold':False,'operational_recovery':'CR001-RECOVERY-01'}
    append_jsonl(data/'drafts.jsonl',draft)
    candidate = make_candidate(draft, draft['draft_text'], 'unchanged')
    protected = [literal for fact in brief['required_facts'] for literal in fact['protected_literals']]
    candidate['deterministic_checks']=literal_diagnostics(draft['draft_text'],draft['draft_text'],protected)
    append_jsonl(data/'candidates.jsonl',candidate)
    print(json.dumps({'event':'recovered','draft_id':draft['draft_id'],'metadata_cost':result['metadata']['cost']}),flush=True)
print(json.dumps(client.budget_status()),flush=True)
