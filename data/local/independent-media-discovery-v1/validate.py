"""本次发现的离线核验；不访问网络、不重写来源。"""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
REPORT=REPO/'docs/routes/compact-refiner/reports/independent-media-discovery-v1.md'

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def no_space(s): return re.sub(r'\s+','',s)
def norm(s): return re.sub(r'\s+',' ',s).strip()
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

searches=sorted((ROOT/'searches').glob('*.json'))
assert len(searches)==8
assert [read(p)['id'] for p in searches]==[f's{i:02d}' for i in range(1,9)]
errors=0;credits=0;results=[]
for p in searches:
    item=read(p)
    assert item['started_at']<=item['completed_at']
    if item['result'].get('isError'):
        errors+=1
        assert '未找到相关数据' in item['result']['content'][0]['text']
    else:
        payload=json.loads(item['result']['content'][0]['text'])
        credits+=payload.get('credits',0)
        results.extend(payload['webpages'])
assert (errors,credits,len(results))==(2,18,48)
assert len({x['link'].rstrip('/') for x in results})==47
selections=read(ROOT/'selections.json')['articles']
assert len(selections)==6
requests=list((ROOT/'documents').glob('*/article-request.json'))
robots=list((ROOT/'robots').glob('*/robots-request.json'))
assert (len(requests),len(robots))==(6,3)
for p in requests+robots:
    request=read(p)
    response=p.parent/('article.html' if p.name.startswith('article') else 'robots.html')
    assert request['status']==200
    assert len(response.read_bytes())==request['bytes']
    assert sha(response.read_bytes())==request['sha256']
coverage=read(ROOT/'reading-coverage.json')
analysis=read(ROOT/'analysis.json')
assert len(coverage['documents'])==5
assert coverage['failed_full_read_attempts']==['d05']
quotes=0;characters=0;blocks_total=0
for item in coverage['documents']:
    doc=item['doc_id'];folder=ROOT/'documents'/doc
    body=(folder/'body.txt').read_text(encoding='utf-8')
    blocks=read(folder/'blocks.json');meta=read(folder/'metadata.json')
    assert sha(body.encode())==item['body_sha256']==meta['body_sha256']
    assert len(body)==item['characters_read']==meta['characters']
    assert item['blocks_read']==[b['block_id'] for b in blocks]
    assert body=='\n'.join(b['text'] for b in blocks)
    assert len(blocks)==meta['text_blocks']
    for b in blocks:
        assert body[b['start_char']:b['end_char']]==b['text']
    soup=BeautifulSoup((folder/'article.html').read_bytes(),'html.parser')
    if doc=='d01':
        decoded=base64.b64decode(soup.select_one('input#content_json')['value'])
        assert decoded==(folder/'content-json-decoded.json').read_bytes()
        data=json.loads(decoded)
        assert len(data)==8==read(folder/'component-coverage.json')['components_parsed']
        for b in blocks:
            obj=data
            for part in b['source_path'].strip('/').split('/'):
                obj=obj[int(part)] if isinstance(obj,list) else obj[part]
            text=str(obj)+'%' if b['tag']=='percentage' else str(obj)
            assert norm(BeautifulSoup(text,'html.parser').get_text('',strip=False))==b['text']
    else:
        article=soup.select_one('#task_page .des' if doc=='d04' else 'article#articleId')
        for selector in ['h1.item-name','.recommend-tab','.the-end']:
            for node in article.select(selector):node.decompose()
        assert no_space(article.get_text('',strip=False))==no_space(body)
        assert read(folder/'dom-coverage.json')['nonwhitespace_text_coverage_equal']
    rec=next(r for r in analysis['documents'] if r['doc_id']==doc)
    ids={b['block_id'] for b in blocks}
    for f in rec['findings']:
        assert set(f['context_block_ids'])<=ids
        for q in f['quotes']:
            assert q['body_sha256']==meta['body_sha256']
            assert body[q['start_char']:q['end_char']]==q['text']
            block=next(b for b in blocks if b['block_id']==q['block_id'])
            assert block['start_char']<=q['start_char']<q['end_char']<=block['end_char']
            quotes+=1
    characters+=len(body);blocks_total+=len(blocks)
assert (quotes,characters,blocks_total)==(61,25504,286)
assert read(ROOT/'documents/d05/metadata.json')['full_text_status']=='failed_client_shell_only'
assert not (ROOT/'documents/d05/body.txt').exists()
duplicates=read(ROOT/'duplicate-check.json')
assert len(duplicates['pairs'])==15
assert not any(p['exact_text_equal'] for p in duplicates['pairs'])
assert REPORT.exists()
validation={'version':'independent-media-validation-1.0','validated_at_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'network_in_validation':False,'search_calls':8,'searches_with_results':6,'searches_without_data':2,'reported_credits':18,'unreported_error_cost':'unknown','returned_results':48,'unique_search_urls':47,'selected_documents':6,'article_get_requests':6,'robots_get_requests':3,'http_200_responses':9,'additional_web_reader_or_llm_calls':0,'complete_text_documents':5,'client_shell_failures':1,'cohorts_complete_text':{'pre_2023':2,'post_2025_07':2,'transition':1},'text_characters':characters,'text_blocks':blocks_total,'exact_quote_checks':quotes,'full_text_read_coverage':'b001至末块；动态页面只验证公开响应内8个组件的文字','nonwhitespace_dom_coverage_documents':4,'embedded_component_coverage_documents':1,'unique_document_pair_checks':15,'max_char_5gram_jaccard':max(p['char_5gram_jaccard'] for p in duplicates['pairs']),'human_labels_collected':0,'old_reserve_opened':False,'limits':['未核验图片像素与网页视觉渲染。','近重复检查仅本轮五篇及固定锚点，不保证与未读取旧集合无重叠。','语义解释仍为单个助手测量，不是人工或干预验证。']}
save(ROOT/'validation.json',validation)
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json')+[REPORT]
save(ROOT/'manifest.json',{'version':'independent-media-manifest-1.0','created_at_utc':datetime.now(timezone.utc).isoformat(),'files':[{'path':p.relative_to(REPO).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in files],'total_files_excluding_manifest':len(files),'total_bytes_excluding_manifest':sum(p.stat().st_size for p in files),'command':'python data/local/independent-media-discovery-v1/validate.py','manifest_self_excluded':True})
print(json.dumps({'passed':True,'search_calls':8,'article_gets':6,'complete_texts':5,'blocks':blocks_total,'quotes':quotes,'manifest_files':len(files)}))
