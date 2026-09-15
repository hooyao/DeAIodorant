"""只提取已保存公开响应，保留原始页面、块位置和未读取的媒体边界。"""
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup, Comment, NavigableString

RUN=Path(__file__).resolve().parent
def normalized(value):return re.sub(r"\s+"," ",value).strip()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

for row in json.loads((RUN/'selections.json').read_text(encoding='utf-8'))['articles']:
    folder=RUN/'documents'/row['id']
    if (folder/'metadata.json').exists():raise ValueError('existing_extraction')
    request=json.loads((folder/'article-request.json').read_text(encoding='utf-8'))
    if request.get('status')!=200:
        save(folder/'metadata.json',{'id':row['id'],'full_text_status':'unavailable','request':request});continue
    raw=(folder/'article.html').read_bytes();assert sha(raw)==request['sha256']
    soup=BeautifulSoup(raw.decode('utf-8'),'html.parser')
    title=soup.select_one('h1.item-name');published=soup.select_one('meta[property="article:published_time"]');author=soup.select_one('meta[property="article:author"]')
    assert title is not None and published is not None
    blocks=[];citations=[];media=[];removed=[]
    def add(text,tag,path):
        text=normalized(text)
        if text:blocks.append({'block_id':f'b{len(blocks)+1:03d}','text':text,'tag':tag,'source_path':path})
    node=soup.select_one('input#content_json')
    if node:
        decoded=base64.b64decode(node['value'],validate=True);components=json.loads(decoded)
        (folder/'embedded-components.json').write_bytes(decoded)
        for i,component in enumerate(components):
            kind=component['component'];data=component['data'];prefix=f'/{i}/data'
            def rich(value,tag,path):add(BeautifulSoup(str(value),'html.parser').get_text('',strip=False),tag,path)
            if kind=='Text':
                if data.get('label'):rich(data['label'],'label',prefix+'/label')
                rich(data['content'],'p',prefix+'/content')
                citations.append({'source_path':prefix,'markers':data.get('marker'),'verified_upstream':False})
            elif kind=='SectionTitle':
                for key in ('number','title'):
                    if key in data:rich(data[key],'h',prefix+'/'+key)
            elif kind=='StyledList':
                for j,item in enumerate(data['items']):
                    for key in ('label','content'):
                        if key in item:rich(item[key],'li',prefix+f'/items/{j}/'+key)
                    citations.append({'source_path':prefix+f'/items/{j}','markers':item.get('marker'),'verified_upstream':False})
            else:raise ValueError('unsupported_embedded_component:'+kind)
        coverage={'mode':'embedded_components','components':len(components),'components_parsed':len(components),'render_verified':False,'embedded_sha256':sha(decoded)}
    else:
        article=soup.select_one('article#articleId');assert article is not None
        (folder/'article.dom.html').write_text(str(article),encoding='utf-8')
        clone=deepcopy(article)
        for selector in ('h1.item-name','.recommend-tab','.the-end'):
            for element in clone.select(selector):
                removed.append({'selector':selector,'text':normalized(element.get_text()),'html':str(element)});element.decompose()
        for i,element in enumerate(clone.select('span.referer-link')):
            citations.append({'index':i,'attributes':dict(element.attrs),'visible_text':element.get_text(),'verified_upstream':False});element.decompose()
        for element in clone.select('img,video,iframe'):
            media.append({'tag':element.name,'attributes':dict(element.attrs),'inspected':False})
        atoms={'h1','h2','h3','h4','h5','h6','p','li','blockquote','dir'}
        def walk(element,path):
            if isinstance(element,Comment):return
            if isinstance(element,NavigableString):add(str(element),'text',path)
            elif element.name in ('script','style','input'):return
            elif element.name in atoms:add(element.get_text('',strip=False),element.name,path)
            else:
                for i,child in enumerate(element.children):walk(child,path+f'/{i}')
        walk(clone,'article')
        assert re.sub(r'\s+','',clone.get_text('',strip=False))==re.sub(r'\s+','',''.join(b['text'] for b in blocks))
        coverage={'mode':'article_dom','nonwhitespace_text_coverage_equal':True,'removed_nodes':removed,'citation_chips_separate':True,'render_verified':False}
    body='\n'.join(b['text'] for b in blocks);cursor=0
    for block in blocks:
        block['start_char']=cursor;block['end_char']=cursor+len(block['text']);cursor=block['end_char']+1
    assert blocks and body
    (folder/'body.txt').write_text(body,encoding='utf-8',newline='\n')
    meta={'id':row['id'],'url':row['url'],'title':normalized(title.get_text()),'published_at':published['content'],'publication_evidence':str(published),'author':author.get('content') if author else None,'body_sha256':sha(body.encode()),'source_html_sha256':sha(raw),'full_text_status':'complete','completeness_scope':'已保存全文文字视图；引用UI独立保留，图片像素、页面视觉及上游来源未核验','characters':len(body),'blocks':len(blocks),'media_references':len(media),'citation_records':len(citations),'provenance':'unresolved','human_severity_label':None,'corpus_role':'article_isolated_contract_development','source_rights':'来源版权保留；未据公开阅读认证额外训练许可','extractor_sha256':sha(Path(__file__).read_bytes()),'collected_at_utc':request['requested_at_utc']}
    save(folder/'blocks.json',blocks);save(folder/'citations.json',citations);save(folder/'media.json',media);save(folder/'coverage.json',coverage);save(folder/'metadata.json',meta)
    print(json.dumps({k:meta[k] for k in ('id','characters','blocks','media_references','citation_records')}),flush=True)
