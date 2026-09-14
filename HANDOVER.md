# 研究交接：2026-09-14 session

这份交接用于换机后继续当前研究，覆盖本次 session 的目标校准、实验与失败、当前产物、工作约定和下一步。当前分支为 `init`；`main` 继续停留在初始化 commit。交接前的基线 commit 为 `306e5e0ec1802da2c6f7a741d2ea557d4db04be9`。

## 新机器从这里开始

检出 `init`，不要停在仓库默认的 `main`。研究数据、本地产物和 corpus 已按维护者明确要求随本次提交入库，文件清单见 [artifacts.json](handover/session-2026-09-14/artifacts.json)。不需要迁移密钥或解压包。API 凭据不在仓库中。

```powershell
git clone --branch init https://github.com/hooyao/DeAIodorant.git
cd DeAIodorant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe experiments/verify_research_handover.py --inventory handover/session-2026-09-14/artifacts.json
```

Linux／macOS 将 `.\.venv\Scripts\python.exe` 换为 `.venv/bin/python`。项目最低 Python 版本为 3.10，本次实际环境为 Windows、Python 3.13.5。上述核验只读取文件，不调用网络、LLM 或 GPU，也不改写任何冻结结果。预期检查六个案例、八个语义字段、80 处引用、58 个不同片段和完整产物清单。

先读本文件，再读 [AGENTS.md](AGENTS.md)、[当前目标](docs/target-feature-discovery.md)和[篇章动作分析](docs/routes/compact-refiner/cognitive-move-analysis.md)。入口文档已纠正“本地没有产物”“当前使用 gx10”“下一步仍是复筛”等陈旧描述；历史报告保留当时状态。

初始续研不需要 OpenRouter 凭据。确实需要快速便宜的小模型时，在新机器本地另行配置被 Git 忽略的 `.env`，键名为 `OPENAI_API_KEY`。不要将旧机器的凭据、cookie 或登录文件提交到 Git。

## 已校准的项目目标

产品处理 InfoQ 等媒体已经发布的完整真实中文文章，同时改善两件事：读者反感的机械化风格信号，以及导致难读的指代、表达和推理问题。维护者用“臭味”和“腐败的肉”区分这两层，要求一起解决。

保留有用信息、事实、数字、实体、否定、限定、归属及作者意图。不能为了让文章好读而编造缺失前提、经历或事实。继续阅读意愿是主要产品结果；作者身份猜测和 AI detector 分数不是优化目标。

项目前半部分是从真实强例中发现可重复的特征。之后才验证编辑干预，再考虑训练小模型。当前没有已验证的臭味 detector、复合分数、RL reward 或 SFT 数据集，也没有开始 SFT、DPO 或 RL。

译文是核心产品范围。最终 refiner 应仅凭完整中文文章改善中文译文，英文原文是可选核验材料。按直接以中文写作、翻译、混合／改编、来源未明分层；旧的译文排除结果保留为历史或仅原创对照，不能继续一概排除译文，也不能假定英文原文质量良好。

保留时间框架：早于 2023-01-01；2023-01-01 至 2025-06-30 为独立过渡期；2025-07-01 及以后为后期。2025 年 7 月是维护者观察和采样边界，尚未被数据证明为统计断点。日期不认证单篇文章作者身份或臭味程度。

## 本次最重要的 learning

1. **先选对现象，再谈测量。** 在臭味很弱的文章或合成通知中反复寻找臭味，无法回答目标问题。能解析、能修改、保真检查通过，都不能替代目标覆盖。不要把工程进展写成读者效果。
2. **维护者的感觉是需要解释的观察。** 不要求维护者先给出语言学定义，不让其反复比较没有明显差别的样例。原始反馈必须保留，不能事后升级成更强标签。
3. **不能死磕 Cowork。** 维护者早已认为其臭味弱、像翻译腔，后又明确否定其作为典型中文强例。预览已撤回，不得改称可读性任务再提交。拒绝样本不是 A/B 偏好结果。
4. **字面词频只覆盖表面。** `不是 A，而是 B` 改成 `不是 A，是 B`，动作与臭味可能不变。最强实例如今恰好没有字面 `而是`，这说明计数覆盖不足，不说明对比框架无关。
5. **分析动作，不制造禁用词表。** 当前解释是反复进行认知纠正、揭示深意或指导读者的动作，可能通过无充分依据的对立、以重命名替代解释、连续判词而缺乏推进来实现。标题 `先把买、搓、等三条路算明白` 也属于观察范围。
6. **风格负担与内容价值要分开。** 强臭味文章仍有必要的限定和有用的纠正，不能把每句话都归为错误。正常中文省略不等于缺主谓宾，完整 UD 树也不等于可读性良好。
7. **低成本不等于有效 reward。** 传统 NLP 可辅助定位、实体／否定／情态提取、指代候选、复现及局部聚集；它不能单凭词汇或依存关系证明两个主张同维度、证据足够或读者收益。先检验测量，再谈 RL。
8. **不把可能原因写成已知训练机制。** Gemini 提供的 RLHF、DPO、合成数据和跨语言解释是参考假设。当前没有因果证据；DPO 也不必依赖显式 reward model。
9. **模型用错地方就是浪费。** 当前 Agent 本身是 Astra。强任务由本身或 Astra subagent 承担；OpenRouter 只用于快速便宜的小模型。文档迁移曾误用外部 Astra，已停止，不能写成从未发生。

## 已确认的样例与边界

| 样例 | 人工证据与用途 | 本次直接复核 |
|---|---|---|
| [SMZDM Microduck](https://post.smzdm.com/p/a70dm4ll/) | 维护者明确评价“极其臭”“恶臭”；主要强正例。标题和裸 `是` 对比框架已有明确反馈，不再重复询问。 | 3,231 个 Unicode 字符，30 个正文 blocks；`而是` 0 次、`不是` 5 次。 |
| [百度供给文章](https://www.infoq.cn/article/rDTKqBrlGD5R93NFDOI8) | 维护者评价“一般臭”；较低强度参照，不是干净阴性。 | 5,872 字符，64 blocks；`而是` 3 次。 |
| [Cowork](https://www.infoq.cn/article/UN16P0pugHNutuMbgrNl) | 弱臭味、难读／翻译腔；已撤回读者任务，保留工程产物。 | 不再提名为典型强例，不重发预览。 |

SMZDM 保留原始 HTML、DOM、分析正文、含引用正文、22 个发布方引用标记和四幅图片的引用。图片及上游全文未独立核实。发布方的“内容由AI生成”是单独的披露证据，不证明具体模型或生成／翻译流程。

两篇已知人工标签条件下的助手分析提出四类候选风格：纠正式重构；短平行判词；持续内行或指令式姿态；证据堆叠后的宽泛结论。在这一对文章中，中间两类定性差异较清楚，但来源与体裁混杂仍未解决，不能声称特征泛化。

具体底层问题包括：将个体零售 DIY 估算推广为一般省钱结论，再转用于商业逆向复刻；未定义版本“三件套”；首发／无替代主张缺少对应比较；销量速度与营收推算没有一致核算基础。后者不是已经认证的数值矛盾。

必须保留反例：Jetson／RK3566 平台区分有真实信息；软件开放与硬件未公开是有用限定；玩具与学习管线可以共存；`训练靠算力，实机真不靠` 在上下文中可指机载无需训练级 GPU，不能判为零计算事实错误或缺主语。

## 当前成果：六个关联原文的篇章动作

主要入口：[protocol](docs/routes/compact-refiner/cognitive-move-analysis.md)、[六案例报告](docs/routes/compact-refiner/reports/cognitive-move-analysis-v1.md)。当前标注是 `data/local/cognitive-move-analysis-v1/units-v1.1.json`；初版 `units.json` 保留。

八个字段依次描述动作、当前讨论问题、可选的先前／被否定说法 A、断言或承诺 B、关系 R、依据及推理连接、信息更新、立场与呈现。焦点动作、支持证据和后续总结分开；一个段落可以有多个动作，证据可以跨段。

| 案例 | 所分析的动作 |
|---|---|
| M01 | SMZDM 标题设定议程，A 可以不存在；组织正文有用，但不等于成本已说清。 |
| M02 | 机载硬件纠正；保留真实区分，不推断读者原先相信 Jetson。 |
| M03 | 带用途条件的价值强调；保留“核心”和学习条件，不强判 false dichotomy。 |
| M04 | DIY 估算到一般判断、再到商业复刻的两次不同推断。 |
| M05 | 百度缓存机制的普通解释，不强加一个被否定的 A。 |
| M06 | Apple 因果替换与类比迁移，保留后文条件，不以结果数据认证因果优先性。 |

当前实测关联检查：6 cases、8 字段、80 span occurrences、58 unique spans、16 个原始来源文件 hash。正文 blocks、标题、片段边界和原文切片均相符。这是 source linkage，不是语义准确率、独立人工标签或 reward 验证。

核心文件 SHA256：

| 文件 | SHA256 |
|---|---|
| `units-v1.1.json` | `2045ab168946ff08b96e7fe524ddccf683fc007b465731be928bbd18059140f2` |
| SMZDM `analysis-body.txt` | `6a07bf687b9a91ee7eedaad1d0a8d71b26defcdd9f246b8b8af78dad30180451` |
| Baidu `body.txt` | `2977deaed4317dd195716a9bd051e69a81d45fc2ffba94db7086aa0418a126e2` |

旧 `validate_units_v1_1.py` 故意拒绝覆盖已存在的 `validation-v1.1.json`。换机核验使用新的 `experiments/verify_research_handover.py`，不要删除旧结果以强行重跑。旧 protocol hash 对应文档中文迁移前的英文原件，核验入口已映射到 `data/local/documentation-zh-migration-v1/originals/`。

## 既有工程与负面结果都保留

- 合成 CR-001：24 项计划中生成 23 项草稿，13 项进入编辑阶段；客户端、缓存、失败、盲评映射、编辑提案及意义保留检查保留。三组人工反馈为 A／B／A，但第一组有内容不同顾虑、第三组差别很小，整批被认为无明显臭味。不能记为三次去臭胜出。
- InfoQ 保留译文的既有视图为 40 篇：前期 18 篇／5 次 `而是`，后期 22 篇／65 次。另一次固定扩展是 24 GET 得到 21 篇非空正文：前期 9／2，后期 12／28，其中 DHH 一篇贡献 19/28。口径不同，不能直接拼成代表性总体；翻译披露的后续发现保留为 sidecar。
- 十二篇后期文章重新筛查读完 690 blocks：0 个持续强候选、9 个弱／模糊、3 个格式不匹配。没有为此生成下一轮读者任务。
- 旧的八条评分、138 个非恒定特征及有限排列空间说明统计识别不足；零候选、无效测量和不显著结果不能混为一谈。旧筛选器和读者实验继续保留为失败证据，不重筛暴露的 87 候选，不打开 validation reserve。
- 三篇完整媒体修复提案和多次意义保留修订保留为工程证据。仅保持数字清单不变不足以认证意义不变。Cowork 撤回后没有新的读者偏好或训练导出。
- 81 份既有文档完成中文迁移，保留必要 English terminology。真实 prompt、问卷原句、机器字段和原始引文保留原语言。完整旧文档及迁移检查也随本次研究快照入库。

## 文件地图与本次入库方式

| 路径 | 内容与使用方式 |
|---|---|
| `data/pilot/`、`data/annotations/`、`data/translation_*` | 已有 corpus、人工反馈及冻结 benchmark；不是新的干净最终语料。 |
| `data/local/reader-style-anchors-v1/` | SMZDM 原文、结构、来源披露、人工反馈、两类助手分析。 |
| `data/local/targeted-media-discovery-v1/` | Baidu 原文、提取与定向发现／校准记录。 |
| `data/local/cognitive-move-analysis-v1/` | 六案例原版、1.1 版、旧验证记录和脚本。 |
| `data/local/media-contrast-staging-v1/`、`media-provenance-extension-v1/` | 两批完整原始响应、正文、blocks、来源和采集记录。 |
| `data/local/contrast-context-*`、`contrast-syntax-v1/` | 上下文复核、复现、汇总及 CPU parser 结果。 |
| `data/local/media-repair-development-v1/`、`media-contrast-review-v1/`、`target-coverage-rescreen-v1/` | 修复、评审映射、撤回及目标复筛证据。 |
| `data/local/compact_refiner/`、`feature_runs/compact_refiner/` | CR-001／CR-001B 输入、响应、预算台账、提案、盲评映射与历史代码快照。 |
| `feature_runs/` 的其他目录 | pilot 标注与矩阵、读者统计、`而是` 分组统计及已有分析产物。 |
| `data/local/documentation-zh-migration-v1/` | 英文原件、部分 API 草稿、离线译文与检查、迁移台账；API 迁移入口已禁用。 |
| `docs/routes/compact-refiner/` | 当前路线、protocol、决策与报告；按日期和被取代关系阅读。 |
| `src/deaiodorant/refine/` | 有界、可缓存、带预算台账和 Retry-After 处理的 OpenRouter 客户端，以及记录工具。 |
| `src/deaiodorant/analysis/reading_burden.py`、`experiments/` | 确定性检查、来源暂存／审计、分组统计、原文采集整理与复现入口。 |

本次按维护者要求显式提交 `data/` 和 `feature_runs/` 中现存研究文件。`.gitignore` 仍保护新的本地运行目录，未来新增产物仍需检查后显式提交。历史目录继续保留原路径，避免破坏引用。`.gitattributes` 对冻结数据、结果、fixture 和 prompt 禁用换行转换，保证跨系统原始字节及 hash。

不提交 `.env`、认证密钥、cookie、凭据文件、虚拟环境、模型权重、Python 缓存和运行锁。`answer_key.json`、`teacher_input_key.json` 等是研究映射，不是认证凭据，本次保留。第三方正文保留来源，只用于本次授权的研究交接与复现，不因此获得额外再分发或训练许可。

更早的 97／93／119 篇交接报告并不代表这些完整数据都在当前机器。缺失部分继续按报告证据记录，不编造、重建或用其他语料冒充。当前实际可恢复文件以 manifest 为准。

## 下一步：先让动作标注经得住检验

1. 以现有六案例为开发起点，冻结一项小范围标注可靠性实验。保留原文上下文、字段定义、模型／Agent 身份、分歧与独立复核，不把当前助手记录当 gold。
2. 设置两类工程对照：仅更换连接词或等价表述时，核心动作分析应保持；改变否定、量化、范围、归属或关系时，分析必须相应变化。构造的变体只检验测量行为，不冒充新的真实强文章。
3. 明确分段规则：焦点动作与其证据／总结分开，允许一个段落多个动作及跨段支持。先定位分歧来源，暂不计算任意加权臭味总分。
4. 并行寻找独立真实强例和同体裁购买指南／DIY 对照，缓解 SMZDM 与 Baidu 的来源、主题和体裁混杂。不要又只围绕一篇文章优化规则。
5. 只有测量可用之后，才检验特定问题能否预测有用、保留原意的编辑。再往后才考虑蒸馏、SFT 或 reward。当前无需 GPU，也不向维护者重问已有强度判断。

当前 `rhetorical-frame-measurement.md` 只是未执行的词汇测量草案，不能把实现它当成机制问题已解决。旧原始统计代码可复用作导航与对照，不升级为语义支持证明。

## 执行约定与不要重犯的操作错误

- 文档中文，专业术语按需保留英文；代码标识符、实际命令、机器字段和冻结材料保持原样。
- 普通研究推进自主完成，确需用户决策时再停。具体独立任务可开 subagent；强模型任务由当前 Astra 或 Astra subagent 执行。
- OpenRouter 仅使用快速便宜的小模型。历史缓存是复核材料，不能继续调用外部 Astra，也不能恢复文档迁移中中断的请求。该误用已有成功费用约 $2.69，两笔停止时未返回请求的最终账单未知；保守预留不等于实际收费。
- 已跟踪的历史 API 缓存不能作为新的可写私有缓存。后续小模型实验使用新版本、新的被忽略目录，并先核对费用、最大输出、reasoning 配置及错误处理。
- 当前无 DGX Spark／`gx10`；本地 GTX 1080 不做 SFT。需要训练时，先根据模型、方法、序列长度和数据规模给出最低／推荐 VRAM、RAM、存储、软件、时长及费用，再由维护者提供云 GPU。
- 长任务检查真实进程、日志和产物，不只信任 watcher；约一分钟确认启动，此后按预计时长检查数次。API 的计费／权限失败应立即停止批次，不继续对其他条目发同类失败请求。
- 不执行旧报告中的批量采集、旧 GPU 命令或旧输出覆盖操作，只因为它们看上去是“下一步”。先读当前检查点和对应的冻结边界。

## 验证与交接记录

文档迁移阶段离线测试为 168 passed。本次另增加换机只读核验及其离线测试；最终测试结果、产物数量、字节数和提交前检查记录在 [validation.json](handover/session-2026-09-14/validation.json)。

本次推送只更新 `origin/init`。在另一台机器重新运行上述测试和 `--inventory` 检查，确认完整后即可从“下一步”继续，无需重新抓取已经保存的强例或重复旧标注实验。
