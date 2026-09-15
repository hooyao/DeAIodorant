"""回放已选操作，生成完整文字稿与阅读对照；不修改原文。"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re

RUN=Path(__file__).resolve().parent
ROOT=RUN.parents[2]
plan=json.loads((RUN/'reviewed-edit-plan.json').read_text(encoding='utf-8'))
source=(ROOT/plan['source_body_path']).read_bytes()
assert hashlib.sha256(source).hexdigest()==plan['source_body_sha256']
body=source.decode('utf-8')
blocks=json.loads((ROOT/plan['source_blocks_path']).read_text(encoding='utf-8'))
meta=json.loads((ROOT/plan['source_metadata_path']).read_text(encoding='utf-8'))
assert '\n'.join(b['text'] for b in blocks)==body
out=RUN/'draft-v1'
if out.exists():raise ValueError('output_already_exists')
lookup={b['block_id']:b for b in blocks}
selected=plan['style_edits']+plan['grouping_edits']
assert len({e['block_id'] for e in selected})==len(selected)
for edit in selected:
    assert edit['view']=='body' and lookup[edit['block_id']]['text'].count(edit['old'])==1
for edit in plan['grouping_edits']:
    assert edit['new'].replace('\n','')==edit['old']

def apply(edits):
    result=deepcopy(blocks)
    by_id={b['block_id']:b for b in result}
    for edit in edits:
        b=by_id[edit['block_id']]
        b['text']=b['text'].replace(edit['old'],edit['new'],1)
    cursor=0
    for b in result:
        b['start_char']=cursor;b['end_char']=cursor+len(b['text']);cursor=b['end_char']+1
    return result

variants={'original':apply([]),'style':apply(plan['style_edits']),
          'grouping':apply(plan['grouping_edits']),'combined':apply(selected)}
number=re.compile(r'\d+(?:[.~–-]\d+)*(?:[xX])?')
quoted=re.compile(r'“[^”]*”')
checks={}
for name,rows in variants.items():
    text='\n'.join(b['text'] for b in rows)
    assert number.findall(text)==number.findall(body)
    assert quoted.findall(text)==quoted.findall(body)
    checks[name]={'characters':len(text),'numbers_in_order_unchanged':True,
                  'quoted_text_in_order_unchanged':True,'body_sha256':hashlib.sha256(text.encode()).hexdigest(),
                  'semantic_preservation':'requires_independent_review','reader_preference':None}
assert re.sub(r'\s+','','\n'.join(b['text'] for b in variants['grouping']))==re.sub(r'\s+','',body)

def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
out.mkdir()
for name,rows in variants.items():
    text='\n'.join(b['text'] for b in rows)
    (out/f'{name}.txt').write_text(text,encoding='utf-8',newline='\n')
    (out/f'{name}.md').write_text('# '+meta['title']+'\n\n'+text.replace('\n','\n\n')+'\n',encoding='utf-8',newline='\n')
    save(out/f'{name}.blocks.json',rows)

def article(rows):
    parts=[]
    for b in rows:
        tag='h2' if b.get('tag') in ('h1','h2','h3','h4','h5','h6') else 'p'
        for paragraph in b['text'].split('\n\n'):
            parts.append(f'<{tag}>{html.escape(paragraph)}</{tag}>')
    return ''.join(parts)

change_parts=[]
for index,e in enumerate(selected,1):
    change_parts.append(f'<section class="change"><h2>{index}. {html.escape(e["target_family"])}</h2><p>{html.escape(e["why"])}</p><div class="comparison"><div><h3>原文</h3><pre>{html.escape(e["old"])}</pre></div><div><h3>改写</h3><pre>{html.escape(e["new"])}</pre></div></div></section>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>文字改写试稿</title>
<style>
:root{color-scheme:light}*{box-sizing:border-box}body{margin:0;background:#f8f7f3;color:#25302e;font-family:"Microsoft YaHei","PingFang SC",sans-serif}header{max-width:920px;margin:42px auto 0;padding:0 28px}h1{font-size:27px;line-height:1.6;font-weight:650;margin:12px 0 18px}.meta{font-size:13px;color:#626d67}a{color:#356650}nav{display:flex;gap:8px;margin:24px 0 18px}button{font:inherit;border:1px solid #d3dbd5;background:#fff;color:#43524a;padding:10px 20px;border-radius:6px;cursor:pointer}button[aria-selected=true]{background:#345c49;color:#fff;border-color:#345c49}main{max-width:920px;margin:auto;padding:8px 28px 64px}.pane{background:#fff;padding:34px 44px;border:1px solid #e3e7e2;border-radius:8px;font-size:17px;line-height:1.95}.pane[hidden]{display:none}.pane h2{font-size:21px;line-height:1.6;margin:36px 0 18px}.pane h2:first-child{margin-top:0}.pane p{margin:0 0 22px}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:20px}.comparison>div{min-width:0;background:#f5f7f4;padding:16px}.comparison h3{font-size:14px;color:#626d67;margin:0 0 8px}pre{font:inherit;font-size:15px;line-height:1.8;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}.change{border-bottom:1px solid #e3e7e2;padding-bottom:24px}.change>p{font-size:14px;color:#626d67}footer{font-size:13px;color:#747e78;margin-top:24px}@media(max-width:650px){header{margin-top:20px;padding:0 16px}h1{font-size:22px}main{padding:0 12px 36px}.pane{padding:20px;font-size:16px}.comparison{grid-template-columns:1fr}button{padding:9px 13px}}
</style><header><div class="meta">文字改写试稿 · <a href="__URL__" target="_blank" rel="noopener noreferrer">查看来源网页</a></div><h1>__TITLE__</h1><div class="meta">本页对照文字内容；未加载原网页图片。</div><nav role="tablist"><button role="tab" aria-selected="true" data-pane="combined">改写稿</button><button role="tab" aria-selected="false" data-pane="original">原文</button><button role="tab" aria-selected="false" data-pane="changes">修改对照</button></nav></header><main><article class="pane" id="combined">__COMBINED__</article><article class="pane" id="original" hidden>__ORIGINAL__</article><article class="pane" id="changes" hidden>__CHANGES__</article><footer>这是待审阅的文字稿，来源中的事实和技术建议未作外部核验。</footer></main><script>document.querySelectorAll('[data-pane]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-pane]').forEach(x=>x.setAttribute('aria-selected',String(x===button)));document.querySelectorAll('.pane').forEach(x=>x.hidden=x.id!==button.dataset.pane);window.scrollTo({top:0,behavior:'instant'});}));</script></html>'''
page=page.replace('__URL__',html.escape(meta['url'],quote=True)).replace('__TITLE__',html.escape(meta['title'])).replace('__COMBINED__',article(variants['combined'])).replace('__ORIGINAL__',article(variants['original'])).replace('__CHANGES__',''.join(change_parts))
(out/'review.html').write_text(page,encoding='utf-8',newline='\n')
save(out/'edit-log.json',{'style_edits':plan['style_edits'],'grouping_edits':plan['grouping_edits'],'excluded':plan['excluded_proposals']})
manifest={'version':'information-refinement-draft-1.0','created_at_utc':datetime.now(timezone.utc).isoformat(),
          'source_body_sha256':plan['source_body_sha256'],'plan_sha256':hashlib.sha256((RUN/'reviewed-edit-plan.json').read_bytes()).hexdigest(),
          'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':checks,
          'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()},
          'scope':'公众信息文章的有限改写；无艺术文体、作者分类或读者效果结论。'}
save(out/'manifest.json',manifest)
assert hashlib.sha256((ROOT/plan['source_body_path']).read_bytes()).hexdigest()==plan['source_body_sha256']
print(json.dumps({'variants':checks,'output':str(out),'selected_edits':len(selected)},ensure_ascii=False))
