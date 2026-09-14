from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parent
sys.path.insert(0,str(RUN))
from translate import FENCE, INLINE, TARGET, URL, HAN, NUMBER

def values(pattern,text):
    return Counter(m.group(0) for m in pattern.finditer(text))

def without_blocks(text):
    return FENCE.sub('',text)

def table_shapes(text):
    return [line.count('|') for line in text.splitlines() if re.match(r'^\s*\|.*\|\s*$',line)]

def english_lines(text):
    candidates=[]
    in_fence=False
    for n,line in enumerate(text.splitlines(),1):
        if re.match(r'^\s*(`{3,}|~{3,})',line):
            in_fence=not in_fence
            continue
        if in_fence: continue
        plain=TARGET.sub('',INLINE.sub('',line))
        if not HAN.search(plain) and len(re.findall('[A-Za-z]{2,}',plain))>=6:
            candidates.append({'line':n,'text':line})
    return candidates

manifest=json.loads((RUN/'manifest-before-extended.json').read_text(encoding='utf-8'))
records=[]
for item in manifest['files']:
    name=item['path']
    path=ROOT/name
    before=(RUN/'originals'/name).read_text(encoding='utf-8-sig')
    after=path.read_text(encoding='utf-8-sig')
    checks={}
    if path.suffix=='.md':
        for label,pattern in [('inline_code',INLINE),('link_targets',TARGET),('urls',URL),('chinese_runs',HAN)]:
            old,new=values(pattern,before),values(pattern,after)
            checks[label]={'missing':list((old-new).elements()),'added_count':sum((new-old).values())}
        checks['code_fences_equal']=values(FENCE,before)==values(FENCE,after)
        checks['heading_levels_equal']=re.findall(r'(?m)^#{1,6}\s+',before)==re.findall(r'(?m)^#{1,6}\s+',after)
        checks['table_shapes_equal']=table_shapes(before)==table_shapes(after)
        checks['english_lines']=english_lines(after)
    records.append({'path':name,'changed':before!=after,'before_sha256':item['sha256'],
        'after_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checks':checks})
(RUN/'audit.json').write_text(json.dumps({'files':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(records),'changed':sum(r['changed'] for r in records),
    'unchanged':[r['path'] for r in records if not r['changed']],
    'english_line_files':sum(bool(r['checks'].get('english_lines')) for r in records)},ensure_ascii=True))
