"""保存本轮助手全文分析；全部引文必须精确链接到规范化正文。"""
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent

def sha(v): return hashlib.sha256(v).hexdigest()
def save(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

docs={}
for folder in sorted((ROOT/'documents').iterdir()):
    metadata=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    docs[folder.name]={'metadata':metadata,'folder':folder}
    if (folder/'body.txt').exists():
        docs[folder.name]['body']=(folder/'body.txt').read_text(encoding='utf-8')
        docs[folder.name]['blocks']=json.loads((folder/'blocks.json').read_text(encoding='utf-8'))

def quote(doc,block_id,text):
    blocks=docs[doc]['blocks']; block=next(x for x in blocks if x['block_id']==block_id)
    assert text in block['text'],(doc,block_id,text)
    start=block['start_char']+block['text'].index(text);end=start+len(text)
    assert docs[doc]['body'][start:end]==text
    return {'block_id':block_id,'text':text,'start_char':start,'end_char':end,'body_sha256':docs[doc]['metadata']['body_sha256']}

def finding(doc,kind,analysis,parts,context):
    return {'kind':kind,'analysis':analysis,'quotes':[quote(doc,b,t) for b,t in parts],'context_block_ids':context}

records=[]
records.append({'doc_id':'d01','assistant_nomination':'持续目标动作的后期候选；不等于人工确认的强臭味','full_read_blocks':'b001-b037','overall':'开篇、观点卡、两个支持阵营、结尾和投票均复用同一品牌二分。反复重命名和整齐判词持续存在；显式认知纠正较锚点少，不能把两篇说成同一种完整风格。','findings':[
 finding('d01','parallel_verdict_and_reader_guidance','全能与省心不是互斥的同一性能维度。后文其实分别列出两者清洁和自清洁优势，结尾仍以品牌人格帮助普通家庭二选一；这种重点强调可以用于导航，也可能盖过具体机型条件。', [('b001','是选性能全面的追觅，还是选省心省力的云鲸？'),('b016','全能旗舰'),('b017','痛点精准'),('b034','如果你的家是复杂的战场，选追觅；如果你的生活需要一个省心的管家，选云鲸。')],['b001','b004','b011','b013','b016','b017','b021','b029','b033','b034','b035']),
 finding('d01','mirrored_verdict_series','两个阵营均按认为／看重／认可／赞赏／肯定排列五项。PK 卡与随后六个分节重复清洁、自清洁、智能等价值总结；后文也有新细节，因此不能把整段全判冗余。',[('b004','认为追觅在清洁能力、自清洁能力和智能化设计上整体更优，尤其适合复杂地形和重油污家庭。'),('b011','认为云鲸在毛发处理上表现更出色，整机零缠绕设计让养宠或长发家庭彻底解放双手。')],['b004','b005','b006','b007','b008','b011','b012','b013','b014','b015','b021','b023','b025','b029','b031','b033']),
 finding('d01','grounds_to_superlative','列举来源用户评价，不能在未说明抽样、型号、条件和对比指标时确立普通家庭的最优解。58位用户、155位来源作者与52%/48%并不逻辑矛盾，但本文没有给出对应的抽样/计数方法。',[('b001','本文汇总了58位真实用户的深度体验，帮你找到最适合的答案。'),('b003','52%'),('b010','48%'),('b034','为追求省心省力的普通家庭提供了最优解')],['b001','b002','b003','b009','b010','b029','b031','b033','b034']),
 finding('d01','scope_and_model_mixing','云鲸多型号共享论证：逍遥002、002MAX、J6的表现被收束成品牌哲学。油污重被结论侧重分配给追觅，但云鲸段也出现油污重选择云鲸的引述。80天和120天可能针对不同型号；不能认证数值矛盾。',[('b033','家里油污重的还是选履带式拖布的云鲸逍遥002吧。'),('b033','3k价位顶配还得看活热水履带式拖布的云鲸J6，清洁最干净、用着最省心。'),('b031','基站支持80天免维护，真正实现全链路免手洗维护。')],['b029','b031','b033','b034']),
 finding('d01','useful_detail_and_counterexample','具体使用条件和结构功能值得保留：不用把所有对比删掉。这里记录的是文章内部信息，不是外部核验后的硬件事实。',[('b029','鉴于不在家做饭、不养宠物，只需要基础清扫和解放双手，性价比更高的云鲸逍遥002Max是更好的选择。'),('b025','三重智能升降系统（滚筒、滚刷、边刷独立升降），根据干湿垃圾类型智能切换清洁模式')],['b021','b025','b029'])],
 'limits':['页面明示内容由AI生成，只作为发布方披露，与候选强度分开；模型、翻译流程未知。','JSON 的内容覆盖已检查，页面实际视觉渲染、上游引用和样本比例未核验。']})

records.append({'doc_id':'d02','assistant_nomination':'持续目标动作与重复包装的后期候选；不等于人工确认的强臭味','full_read_blocks':'b001-b138','overall':'前半篇不断宣告本质、核心、进化、必选门槛，再用十个误区指导读者；后半篇多个产品重复适用人群和免维护承诺。比单个连接词明显，且包含大量有用解释。长度和商品推荐体裁是重要混杂。','findings':[
 finding('d02','recurrent_instructional_stance','正文开头把读懂底层原理设为买对产品的前提，随后以必须／直接pass和永远的排序强化指导。认知纠正集中在b090-b100，不能仅凭这些措辞判断建议错误。',[('b002','读懂底层原理，才能避开参数噱头，选到真正好用的产品。'),('b018','2026 年家庭用户选购，最低门槛必须是 LDS 激光导航，低于该标准的机型直接 pass；'),('b094','选购优先级永远是：导航避障＞清洁能力＞自动化基站功能。')],['b002','b015','b018','b027','b040','b048','b071','b090','b091','b092','b094','b098','b099']),
 finding('d02','scope_expansion','自动化功能及月级清理周期，反复被包装为全链路零人工干预或全年零干预。文章也明示集尘袋周期和安装条件，支持的是限定操作频率；未提供全年无需任何维护的跟踪依据。',[('b011','实现从「机身免打理」到「全链路零人工干预」的跨越。'),('b057','从「每次扫完都要打理」进化到「月级免维护，甚至全年零干预」'),('b060','可直接将人工倒尘的频率从「每天一次」降到「1-2 个月一次」。'),('b108','真正实现清洁全流程免手动干预')],['b011','b057','b060','b062','b063','b108','b115','b130','b137']),
 finding('d02','repeat_without_new_discrimination','不同价位、多台产品共用140㎡以上适配、养宠优选、无死角、安静等判词，降低产品间的区分信息。同型号DDX67在3000-4000和2000-3000两档重复，后者标国补版；价格口径可能解释，但正文未明确说明，因此保留待核实。',[('b107','可轻松适配 140㎡以上的居家清洁需求。'),('b117','成为小户型、养宠家庭家用清洁的优选，可完美适配 140㎡以上的居家清洁需求。'),('b129','成为多口之家、宠物家庭家用清洁的优选，可完美适配 140㎡以上的居家清洁需求。'),('b116','型号 DDX67'),('b132','国补版，型号 DDX67')],['b102','b107','b112','b116','b117','b120','b123','b126','b129','b131','b132','b133']),
 finding('d02','criterion_to_recommendation_gap','选购标准要求清扫噪音≤58dB，产品段又以63或65dB宣告低噪和不扰人。测试档位、测距与场景可能不同；本文没有对齐口径，也没有解释推荐为何偏离自身门槛，不据此认证产品数据错误。',[('b076','清扫噪音≤58dB，静音档≤52dB'),('b108','扫拖运行噪音低至 63dB'),('b115','扫拖运行噪音低至 65dB')],['b076','b105','b108','b111','b115','b127']),
 finding('d02','useful_correction_and_counterexample','吸力并非唯一指标、安装条件与功能需求匹配都有实质信息。尤其b092约束不需要买所有新功能，缓和前文部分绝对门槛；应保留这种内在张力，不把整篇只归为命令姿态。',[('b027','但不是唯一指标，风道密封性、滚刷贴合度对清洁效果的影响同等重要。'),('b062','安装前提是提前预留进水口、排水口、电源'),('b092','无顽固污渍清洁需求，就不用为顽渍喷溶功能支付溢价；无嵌入式装修需求，超薄嵌入功能也非必选。')],['b008','b009','b027','b052','b062','b069','b092','b093'])],
 'limits':['全文提到多张对比表，数据呈现在图片中；本次只确认HTML文字完整，不能对图内支持作缺失判定。','网页时间2026-03-19与搜索结果2026年01月01日不一致；使用页面明确日期，保留两者。','来源类型未明，署名不是原创或生成方式证明。']})

records.append({'doc_id':'d03','assistant_nomination':'主体较少持续认知包装的早期同站对照；不是干净阴性','full_read_blocks':'b001-b027','overall':'主体按开箱、连接、控制、模式逐项推进，纠正大多对应具体限制；但结尾栏目说明有三组平行自我定位，读者指引和熟人姿态也存在。此例有助于区分局部体裁公式与全篇持续动作。','findings':[
 finding('d03','concrete_correction','App所称全息消息与机身投影的区别有明确对象，接着说明只能用手机屏幕查看；这项纠正增加可操作理解。',[('b021','App介绍上说是会有记录和查看全息模式，但BB-8机身内并没有投影功能，所以只能透过手机屏幕来查看录好的图像')],['b016','b017','b020','b021']),
 finding('d03','bounded_reader_guidance','指令分别服务于充电、蓝牙、方向校准，较少在每段后重命名价值。不能将面向读者或祈使语气直接算缺陷。',[('b016','当然前提是别忘了打开手机的蓝牙。'),('b018','需要通过控制将闪烁的蓝色灯光移动至自己这一面，完成此方向校准之后，便可尽情玩耍了。')],['b014','b016','b018']),
 finding('d03','counterexample_to_time_or_phrase_rule','旧文结尾也有三连平行判词，声称没有个人观点、客观展示，正文却使用鸡肋等评价。栏目声明可能是在区分栏目定位，不可简单认定故意虚假；此段不能用来推断生成身份。',[('b027','和晒物比，这里没有个人观点，只是最速的介绍；和评测比，这里没有细节测试，只是客观的展示；和广告比，这里没有华丽辞藻，只是简洁的叙述。'),('b021','感觉有点鸡肋')],['b004','b012','b021','b026','b027']),
 finding('d03','useful_limits_and_source_bias','页面提供实体购买条件、随件缺少USB充电头及英文语音限制；主角由天猫提供是商业关联证据，不能视为独立无利益评测。',[('b004','这次我们收到的主角就由天猫提供'),('b011','与国际版类似依旧没有USB充电头。'),('b023','仅支持英文语音，而且识别的不多')],['b004','b009','b011','b023'])],
 'limits':['大量图片／动态图承担展示，本次未读取像素；体裁更偏开箱体验，不能充当严格DIY成本对照。','旧文章的当前累计点赞收藏不可与新文直接比较传播强度。']})

records.append({'doc_id':'d04','assistant_nomination':'较少反复认知纠正的早期同体裁对照；宣传式承诺仍明显','full_read_blocks':'b001-b045','overall':'六个型号分别介绍参数，重复包装的主要来源是促销式赞语，而非持续告诉读者必须如何重新理解。旧文也有不二之选、彻底等强判断，不能把它标为风格完美。','findings':[
 finding('d04','agenda_and_comparison','开头提供四个选购维度，后文按型号展开，标题和结论主要组织信息；不是每个型号后都重置读者认知。',[('b003','我认为可以从清洁能力、避障能力、智能程度、维护成本四方面入手。'),('b044','以上6款是我认为可以提升生活品质的2022年新品扫拖一体机器人')],['b003','b005','b012','b018','b026','b033','b039','b044']),
 finding('d04','grounds_to_strong_promise','旧文也从结构参数直接跨到全面清洁或无细菌滋生可能。应作为竞争性解释：促销体裁本身就会产生这些承诺；不把早期日期视为免检凭证。',[('b011','绝对是提升幸福感的懒人福音。'),('b023','复杂环境都能游刃有余地做出合理选择。'),('b025','无需动手，解决了拖布发臭、细菌滋生的可能。')],['b009','b011','b013','b015','b023','b025','b036','b041']),
 finding('d04','useful_difference_and_counterexample','对缺少集尘功能、扫拖模块需手动切换的限制明确，保留条件性区别。否定并非扫拖一体在这里直接回答产品能否自动切换，属于实质信息。',[('b017','比较可惜的是，基站不具备自动集尘功能。'),('b035','云鲸J2并非扫拖一体机器人，其扫地、拖地模块需手动更换'),('b038','可以在不用手机APP的情况下，也能实现快速建图、调整拖扫模式选择和一些设置操作')],['b017','b034','b035','b038'])],
 'limits':['新浪“原创”是发布方栏目标记，生产历史未独立认证。','发布时间为2022-05-03 13:00，页面未注明时区；搜索的2022年01月01日不是正文日期。','来源不同；仍为商品参数综述，可能有商业宣传混杂。图片与技术参数未外部核验。']})

records.append({'doc_id':'d06','assistant_nomination':'目标现象明显的过渡期诊断候选；不进入主时间对照','full_read_blocks':'b001-b039','overall':'从开头纯干货承诺到真相／致命伤／王者／智商税，再到土豪闭眼入，连续使用纠正与判词。读者指导很强，但呈现近似夸张社区段子；可以是体裁姿态，不能由风格推断身份。','findings':[
 finding('d06','recurrent_correction_and_verdict','标题、分节和列项反复宣布谁是真正王者或谁在骗人，结尾再按人群给断语。不是字面而是触发的候选。',[('b001','没废话，纯干货版，告诉你怎么选扫地机。'),('b010','• 真相：砍掉激光雷达，靠双5000万像素摄像头+AI算法'),('b018','谁在收“智商税”？'),('b027','土豪闭眼入：石头G20S'),('b029','性价比之王：追觅X40')],['b001','b002','b005','b009','b010','b011','b012','b014','b016','b018','b023','b024','b027','b028','b029']),
 finding('d06','authority_without_traceable_mapping','多个高度精确的实测数值后给出国家实验室认证，但所读文字只列报告名与机构，没有具体页码、编号、方法或对应数据。引用图片未读，不能声称所有可能支持均不存在；当前证据不足以认证这些参数。',[('b004','仿生复眼识别0.1mm发丝，复杂户型建图速度2分18秒（行业平均5分钟）。'),('b005','强光下复眼镜头眩光率37%'),('b034','本文引用数据经国家级实验室认证，抄袭者必究！')],['b004','b005','b007','b008','b010','b013','b015','b017','b034','b036','b037','b038','b039']),
 finding('d06','local_value_and_uncertain_scope','文章确实提醒维护、噪音、安装占地和价格口径，不应因为姿态强就抹掉这些考虑。4799元与千元机用法有张力，但未证明同口径成交价格矛盾。',[('b009','售价4799元'),('b025','得做好每周手洗拖布准备。'),('b029','千元机干翻旗舰'),('b030','具体以商家最终答复为准')],['b009','b013','b019','b020','b021','b024','b025','b029','b030'])],
 'limits':['2025-03-07属于预先定义的过渡期；无论助手认为多明显，都不搬入2025-07后组。','产品真伪、实验数值、优惠与传闻未核实，不能向用户当作购买建议。','b019-b021为来源段落中的压缩参数行；列名不完整，不能自行补全或把提取视图当完整表格语义。']})

save(ROOT/'analysis.json',{'version':'independent-media-discovery-analysis-1.0','analyzed_at_utc':datetime.now(timezone.utc).isoformat(),'analyst':'当前环境 Astra 独立 Agent；知晓 SMZDM 人工锚点，不是盲法','reader_labels_collected':0,'semantic_assessment_status':'可出错的助手解释与候选提名，未做编辑干预或效果验证','documents':records,'unread_document':{'doc_id':'d05','reason':'客户端空壳，未提取正文，不作强度或来源判断。'}})

coverage=[]
for doc in records:
    entry=docs[doc['doc_id']]
    coverage.append({'doc_id':doc['doc_id'],'body_sha256':entry['metadata']['body_sha256'],'full_extracted_text_read':True,'blocks_read':[x['block_id'] for x in entry['blocks']],'characters_read':len(entry['body']),'visual_media_read':False,'quote_checks':sum(len(f['quotes']) for f in doc['findings'])})
save(ROOT/'reading-coverage.json',{'version':'independent-media-reading-1.0','analyst':'当前环境 Astra 独立 Agent','completed_at_utc':datetime.now(timezone.utc).isoformat(),'documents':coverage,'failed_full_read_attempts':['d05'],'limitation':'完整阅读指保存的文本内容；不是图片像素、实际网页渲染或每个上游来源的完整阅读。'})

comparison={k:v['body'] for k,v in docs.items() if 'body' in v}
anchor=ROOT.parents[2]/'data/local/reader-style-anchors-v1/smzdm/analysis-body.txt'
# 此路径只读已获授权的固定强正例，不枚举其他语料或保留集。
anchor=ROOT.parents[2]/'data'/'local'/'reader-style-anchors-v1'/'smzdm'/'analysis-body.txt'
comparison['known_smzdm_anchor']=anchor.read_text(encoding='utf-8')
def grams(text):
    text=re.sub(r'\s+','',text)
    return {text[i:i+5] for i in range(max(0,len(text)-4))}
pairs=[]
for a,b in itertools.combinations(comparison,2):
    ga,gb=grams(comparison[a]),grams(comparison[b])
    pairs.append({'a':a,'b':b,'exact_text_equal':comparison[a]==comparison[b],'char_5gram_jaccard':len(ga&gb)/len(ga|gb),'shorter_5gram_containment':len(ga&gb)/min(len(ga),len(gb))})
save(ROOT/'duplicate-check.json',{'scope':'本轮五篇正文加固定SMZDM锚点；未扫描旧87候选、validation reserve或全仓语料。','method':'去空白字符5-gram集合的Jaccard及较短集合包含率；没有根据结果设定自动去重阈值。','decision':'没有相同URL或相同全文；阅读全文未发现同篇转发。共同主题、模板和同平台聚合来源仍可能相关，不保证统计独立。','pairs':pairs})

provenance=[]
for name,entry in docs.items():
    s=BeautifulSoup((entry['folder']/'article.html').read_bytes(),'html.parser')
    selectors=['.recommend-tab','.content-head .time','.content-head .tit','.content-head .author','a.zan','a.comment','.aigc-article-origin','.update-time']
    evidence=[]
    for selector in selectors:
        for node in s.select(selector):
            evidence.append({'selector':selector,'text':re.sub(r'\s+',' ',node.get_text(' ',strip=True)).strip(),'dom_html':str(node)})
    if name=='d01':
        refs=s.select_one('#refer-origin-modal')
        if refs: (entry['folder']/'publisher-references.dom.html').write_text(str(refs),encoding='utf-8')
        images=[{'src':n.get('src'),'alt':n.get('alt'),'status':'reference_only_not_inspected'} for n in s.select('.img-head img')]
        save(entry['folder']/'header-media.json',images)
    search=json.loads((ROOT/'searches'/f"{entry['metadata']['search_id']}.json").read_text(encoding='utf-8'))
    payload=json.loads(search['result']['content'][0]['text'])
    result=next(x for x in payload['webpages'] if x['position']==entry['metadata']['result_position'])
    provenance.append({'doc_id':name,'page_evidence':evidence,'search_result':result,'search_started_at_utc':search['started_at'],'visibility_limit':'当前页面可见互动计数是抓取时点的累计数；不与历史热门曝光量直接比较，缺失或动态计数不作为零曝光。','translation_evidence':'只检查本篇正文和页面元数据；未查上游，未发现译者不证明原创。'})
save(ROOT/'source-provenance.json',provenance)

print(json.dumps({'full_documents':len(records),'characters':sum(x['characters_read'] for x in coverage),'blocks':sum(len(x['blocks_read']) for x in coverage),'quotes':sum(x['quote_checks'] for x in coverage),'max_jaccard':max(p['char_5gram_jaccard'] for p in pairs)},ensure_ascii=True))
