"""离线提取冻结响应，保存逐块原文、出处及完整性检查。"""
import base64
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup, NavigableString, Comment

ROOT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")

def normalize(value):
    return re.sub(r"\s+", " ", value).strip()

def sha(value):
    return hashlib.sha256(value).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def main():
    rows = json.loads((ROOT / "selections.json").read_text(encoding="utf-8"))["articles"]
    if len(sys.argv) > 1:
        rows = [row for row in rows if row["id"] in sys.argv[1:]]
    for row in rows:
        folder = ROOT / "documents" / row["id"]
        if (folder / "metadata.json").exists():
            raise ValueError("拒绝覆盖已有提取")
        raw = (folder / "article.html").read_bytes()
        request = json.loads((folder / "article-request.json").read_text(encoding="utf-8"))
        assert sha(raw) == request["sha256"]
        soup = BeautifulSoup(raw.decode("utf-8"), "html.parser")
        blocks, citations, media = [], [], []
        def add(text, tag, source_path):
            text = normalize(BeautifulSoup(text,"html.parser").get_text("",strip=False)) if row["id"] == "d01" else normalize(text)
            if text:
                blocks.append({"block_id":f"b{len(blocks)+1:03d}","tag":tag,"source_path":source_path,"text":text})
        meta = {**row,"source_html_sha256":sha(raw),"collected_at_utc":request["requested_at_utc"],"extractor_version":"independent-media-extract-1.0","corpus_role":"discovery_assistant_nomination_not_validation_or_training","generation_model":"unknown","translation_status":"unresolved","reader_label":None,"upstream_sources_fetched":False,"media_inspected":False,"rights_status":"再分发／训练许可未核实，仅供本次授权研究核验"}
        if row["id"] == "d05":
            meta.update({"title":None,"published_at":None,"publication_evidence":None,"cohort":"unknown","source_type":"unknown","full_text_status":"failed_client_shell_only","limitations":["HTTP 200，但响应只有客户端应用壳，无标题、日期或正文；不以搜索摘要补全文，未追加 API、浏览器或 reader 请求。"]})
            save(folder / "metadata.json",meta)
            print(json.dumps({"id":row["id"],"status":meta["full_text_status"]},ensure_ascii=False))
            continue
        if row["id"] == "d04":
            title = soup.select_one(".content-head .tit")
            published = soup.select_one(".content-head .time")
            meta.update({"title":normalize(title.get_text()),"published_at":normalize(published.get_text()),"publication_evidence":{"selector":".content-head .time","raw":str(published),"timezone":"页面未注明；按本地日历日期分组"},"source_type":"chinese_original_publisher_claim","source_type_evidence":"网站栏目为原创，页面署名 Mr_Q蝈蝈颀；这是发布者标记，未核实生产过程。","author":"Mr_Q蝈蝈颀"})
            article = soup.select_one("#task_page .des")
            meta["publisher_rights_statement"] = "本文著作权归作者本人和新浪众测共同所有，未经许可不得转载。"
        else:
            title = soup.select_one("h1.item-name")
            published = soup.select_one('meta[property="article:published_time"]')
            author = soup.select_one('meta[property="article:author"]')
            meta.update({"title":normalize(title.get_text()),"published_at":published["content"],"publication_evidence":{"selector":'meta[property="article:published_time"]',"raw":str(published)},"source_type":"unknown","source_type_evidence":"中文页面与署名不单独证明中文原创；所读正文未发现明确译者／翻译来源标记。","author":author.get("content") if author else None})
            article = soup.select_one("article#articleId")
            meta["publisher_rights_statement"] = "本站内容未经书面许可,禁止一切形式的转载。"
        if row["id"] == "d01":
            node = soup.select_one("input#content_json")
            decoded = base64.b64decode(node["value"])
            data = json.loads(decoded)
            (folder / "content-json-decoded.json").write_bytes(decoded)
            meta.update({"source_type":"mixed_or_adapted_publisher_claim","source_type_evidence":"页面披露源自155位全网作者，content_json 引用多平台用户；混合／汇编是发布者声称的来源关系，未独立核验。","publisher_ai_disclosure":"内容由AI生成","publisher_attribution_claim":"源自155位全网作者","full_text_status":"complete_embedded_component_text_not_render_verified","limitations":["HTML 的可见正文容器为空；完整内容在同一公开响应 input#content_json 的 Base64 JSON 内。只离线解码，不追加请求。","8 个渲染组件全部解析；布局、交互、图片及上游引用未独立核实。","58位真实用户与52%/48%是发布方汇总声称，抽样方法和分母未核实。"]})
            for index, item in enumerate(data):
                component, d = item["component"], item["data"]
                prefix = f"/{index}/data"
                if component == "Text":
                    add(d.get("label", ""),"label",prefix+"/label")
                    add(d["content"],"p",prefix+"/content")
                    citations.append({"source_path":prefix,"markers":d.get("marker"),"status":"publisher_attribution_not_independently_verified"})
                elif component == "PKCard":
                    for side in ["pro","con"]:
                        add(d[side]["title"],"h",prefix+f"/{side}/title")
                        add(str(d[side]["percentage"])+"%","percentage",prefix+f"/{side}/percentage")
                        for j, value in enumerate(d[side]["list"]): add(value,"li",prefix+f"/{side}/list/{j}")
                    for key in ["proTitle","conTitle"]: add(d["resultBar"][key],"label",prefix+"/resultBar/"+key)
                elif component == "SectionTitle":
                    add(d["number"],"section_number",prefix+"/number")
                    add(d["title"],"h",prefix+"/title")
                elif component == "StyledList":
                    for j, value in enumerate(d["items"]):
                        add(value["label"],"label",prefix+f"/items/{j}/label")
                        add(value["content"],"li",prefix+f"/items/{j}/content")
                        citations.append({"source_path":prefix+f"/items/{j}","markers":value.get("marker"),"status":"publisher_attribution_not_independently_verified"})
                elif component == "PKSimple":
                    add(d["vote_title"],"vote_title",prefix+"/vote_title")
                    for j,value in enumerate(d["vote_options"]): add(value["option_name"],"vote_option",prefix+f"/vote_options/{j}/option_name")
                else:
                    raise ValueError("未识别渲染组件："+component)
            save(folder / "component-coverage.json",{"components_total":len(data),"components_parsed":len(data),"ignored_fields":"组件技术名称、componentName、交互 ID；marker 完整保存为引用 sidecar，全部阅读性字符串按 JSON 路径保存。","render_verified":False,"embedded_json_sha256":sha(decoded)})
        else:
            assert article is not None
            (folder / "article.dom.html").write_text(str(article),encoding="utf-8")
            clone = copy.deepcopy(article)
            removed=[]
            for selector in ["h1.item-name",".recommend-tab",".the-end"]:
                for node in clone.select(selector):
                    removed.append({"selector":selector,"text":normalize(node.get_text()),"dom_html":str(node)})
                    node.decompose()
            for node in clone.select("img,video,iframe"):
                media.append({"tag":node.name,**{k:v for k,v in node.attrs.items() if k in ("src","data-src","alt","title","data-original")},"status":"reference_only_not_inspected"})
            atoms = {"h1","h2","h3","h4","h5","h6","p","li","blockquote","dir"}
            def walk(node, path):
                if isinstance(node,Comment):
                    return
                if isinstance(node,NavigableString):
                    add(str(node),"text",path)
                elif node.name in ["script","style","input"]:
                    return
                elif node.name in atoms:
                    add(node.get_text("",strip=False),node.name,path)
                else:
                    for index,child in enumerate(node.children): walk(child,path+f"/{index}")
            walk(clone,"article")
            retained=normalize(clone.get_text("",strip=False))
            extracted="".join(x["text"] for x in blocks)
            assert re.sub(r"\s+","",retained) == re.sub(r"\s+","",extracted)
            save(folder / "dom-coverage.json",{"nonwhitespace_text_coverage_equal":True,"removed_metadata_or_footer_nodes":removed,"article_selector":"#task_page .des" if row["id"]=="d04" else "article#articleId","coverage_scope":"正文容器内全部非空白文本；未把图片像素中的文字当作已读取。"})
            meta.update({"full_text_status":"complete_html_text_images_not_inspected","limitations":["正文 HTML 非空白文字全部覆盖；图片／动态图／内嵌媒体未读取，图中表格数据或效果对比不能被当作已核实支持。","商品卡及媒体链接保留在原始 HTML／DOM，不逐个请求。来源声明和产品技术数值未外部核验。"]})
        body="\n".join(x["text"] for x in blocks)
        cursor=0
        for block in blocks:
            block["start_char"]=cursor;block["end_char"]=cursor+len(block["text"])
            assert body[block["start_char"]:block["end_char"]]==block["text"]
            cursor=block["end_char"]+1
        year_date=meta["published_at"][:10]
        meta.update({"cohort":"pre_2023" if year_date<"2023-01-01" else "post_2025_07" if year_date>="2025-07-01" else "transition","body_sha256":sha(body.encode()),"characters":len(body),"text_blocks":len(blocks),"literal_ershi":body.count("而是"),"literal_ershi_interpretation":"只作描述；不决定候选强度或质量。"})
        (folder / "body.txt").write_text(body,encoding="utf-8",newline="\n")
        save(folder / "blocks.json",blocks)
        save(folder / "citations.json",citations)
        save(folder / "media.json",media)
        save(folder / "metadata.json",meta)
        print(json.dumps({"id":row["id"],"characters":len(body),"blocks":len(blocks),"cohort":meta["cohort"],"title":meta["title"]},ensure_ascii=False))

if __name__ == "__main__":
    main()
