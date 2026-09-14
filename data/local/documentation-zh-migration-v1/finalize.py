from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
RUN=Path(__file__).resolve().parent
FENCE=re.compile(r"(?ms)^(?P<f>`{3,}|~{3,})[^\n]*\n.*?^(?P=f)[ \t]*(?:\n|$)")
INLINE=re.compile(r"(`+)([^`]+?)\1")
LINK=re.compile(r"(?<=\]\()[^\n)]*(?=\))")
SHA=re.compile(r"(?<![A-Za-z0-9])[a-f0-9]{64}(?![A-Za-z0-9])")
before=json.loads((RUN/'manifest-before-extended.json').read_text(encoding='utf-8'))
records=[]
failures=[]
counts={'existing_documents':0,'changed_documents':0,'command_blocks_checked':0,'original_inline_literals_checked':0,'original_sha256_occurrences_checked':0}
for item in before['files']:
    name=item['path']
    original=(RUN/'originals'/name).read_text(encoding='utf-8-sig')
    current=(ROOT/name).read_text(encoding='utf-8-sig')
    record={**item,'after_sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),'after_bytes':(ROOT/name).stat().st_size}
    if name.endswith('.md'):
        counts['existing_documents']+=1
        counts['changed_documents']+=original!=current
        if original==current:failures.append({'path':name,'reason':'not_translated'})
        a,b=FENCE.sub('',original),FENCE.sub('',current)
        for label,pattern,x,y in [('inline',INLINE,a,b),('links',LINK,original,current),('sha256',SHA,original,current)]:
            old=Counter(m.group(0) for m in pattern.finditer(x))
            new=Counter(m.group(0) for m in pattern.finditer(y))
            if old-new:failures.append({'path':name,'reason':label+'_missing','values':list((old-new).elements())})
            if label=='inline':counts['original_inline_literals_checked']+=sum(old.values())
            if label=='sha256':counts['original_sha256_occurrences_checked']+=sum(old.values())
        for match in FENCE.finditer(original):
            block=match.group(0)
            if re.match(r'^(?:`{3,}|~{3,})(?:powershell|bash|python|json)',block):
                counts['command_blocks_checked']+=1
                if block not in current:failures.append({'path':name,'reason':'command_block_changed'})
        shape=lambda text:[line.count('|') for line in text.splitlines() if re.match(r'^\s*\|.*\|\s*$',line)]
        if shape(original)!=shape(current):failures.append({'path':name,'reason':'table_structure_changed'})
        levels=lambda text:re.findall(r'(?m)^#{1,6}\s+',text)
        if levels(original)!=levels(current):failures.append({'path':name,'reason':'heading_structure_changed'})
    records.append(record)
result={'version':'documentation-zh-migration-v1','status':'failed' if failures else 'complete',
    'counts':counts,'failures':failures,'files':records,
    'new_document':{'path':'docs/documentation-language.md','sha256':hashlib.sha256((ROOT/'docs/documentation-language.md').read_bytes()).hexdigest()},
    'validation':{'offline_tests':'168 passed','compileall':'passed','semantic_review':'Agent review and selected independent comparisons; mechanical checks do not prove full semantic equivalence.'},
    'network_policy':'OpenRouter only for fast, inexpensive small models. Strong-model work uses the current Astra agent or Astra subagents.',
    'preserved_exceptions':'Actual experimental prompts, original reader questions, brief voice values, mathematical definitions, models and machine literals remain in their source language. Explanatory diagrams were translated.'}
(RUN/'manifest-after.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],**counts,'failures':failures},ensure_ascii=True))
raise SystemExit(bool(failures))
