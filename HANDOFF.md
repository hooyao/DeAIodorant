# 续研 handoff：2026-09-17

## 换机交接：自有DGX Spark优先

**最新资源安排：DGX Spark是维护者自有设备，只需电费，后续优先使用它。** 维护者准备换机续研；本轮任务为保存交接、提交并推送。当前未获得新机器的连接方式，没有连接旧`gx10`、下载权重或执行GPU工作。拥有设备与本session已能访问设备是两件事，不应依据历史命令直接启动旧主机上的任务。

本节优先于下方按时间保留的旧检查点。模型角色仍以`configs/model-roles-v3.json`为准，硬件安排以上述自有Spark优先为准；不再把租用80GB云GPU或Linux x86_64当作继续研究的前置条件。

### SFT接下来按什么顺序推进

维护者指出上版交接只说明设备预检、缺少实际SFT步骤。本节补齐执行顺序，详细约定见[首轮SFT执行安排](docs/routes/compact-refiner/student-sft-execution-v1.md)。**以下数量与配置是待执行计划；现在仍只有一条Microduck开发原型，没有正式训练集，也没有多文章trainer。** 此次只补全文档，没有开始制作新教师稿或训练。

| 顺序 | 要做什么 | 完成后留下什么，才能进入下一步 |
| --- | --- | --- |
| 1．先做8篇教师稿 | 选择6篇持续难读的完整信息文章和2篇轻改/不改对照，至少2篇有明确译文证据；事先都归入训练池 | Astra全文编辑→另一原生任务复核内容→Root通读→最多两轮修订；保留初稿、复核、修订及准入理由。不能把模型复核写成人工认可 |
| 2．准备64/12/24篇 | 64篇train、12篇dev、24篇新`pilot_eval`；首8篇通过后计入64，不另加 | 按原文章家族去重分组，转载、译文与各种改稿同split；先冻结来源清单和归属，评估文章不参与教师流程调试或训练 |
| 3．Spark运行验证 | 固定官方27B BF16及revision，完成tokenizer、基座完整生成、3步LoRA兼容，再测训练池代表性长度的连续完整步 | 完整token数、正文loss mask、梯度、系统与GPU内存、吞吐、adapter重载均有实测；拥有Spark不等于当前已连接 |
| 4．补正式训练工程 | 复用预检逻辑，实现多文章导出、加载/padding、梯度累积、dev评估、checkpoint保存/恢复与逐文生成 | 有必要的离线测试及实际训练状态恢复检查。现有3步脚本不能仅加循环就冒充正式trainer；具体待实现项见执行文档 |
| 5．跑首轮SFT | 从全新LoRA开始，r16/alpha32/dropout0，BF16，lr `5e-5`，microbatch1、gradacc4，最多2 epochs | 64篇对应32次optimizer update；保存epoch1/2、数据与配置hash。只训练assistant正文和正确结束token，不训练prompt/padding；不续用Microduck probe adapter |
| 6．只用dev选一个候选 | 在12篇dev上先看完整性和信息保留，再比较阅读效果，并列取epoch1 | 有未解决实质内容错误、空输出或截断的checkpoint不晋级；两份都不合格则不解封24篇评估，先按dev问题修正 |
| 7．一次新文章评估 | 同样指令和生成设置，比较原文、官方基座改写、选中的SFT改写，保存学生原样稿 | 逐篇记录内容与阅读结果，失败保留在分母；通过有限工程门槛后再提交一次少量新完整文章给维护者阅读，并决定是否扩到约128篇训练 |

首轮train/dev/评估分别包含48/8/16篇问题文章和16/4/8篇轻改对照；明确译文至少16/4/8篇，且各自至少12/3/6篇属于问题层。其他材料继续保留直接中文、混合/改编或未知来源的真实标记。两篇旧阅读锚点、Azure衍生稿、旧保留集和Cowork均不混入这批新评估。只有train与dev共76篇需要教师目标；评估先保存源文与内容核查清单，不预写24篇答案给编辑者参考。

教师稿要示范把事情说清楚：归拢同主题信息，说明判断的根据和条件，让事件与后果相邻；保留有用细节，允许通顺段落不改。不能只把“而是”换掉，也不能靠大幅删文取悦读者。复核尤其检查数字、版本、引文、说话者、否定、不确定性和结尾遗漏；不要把审查备注或反复“原文作者认为”的提示腔写进所有成稿。传统NLP只辅助定位与核查。

训练输入为标准编辑指令加原标题/完整中文正文，输出为完整标题和正文；复核笔记、教师参考、年份/作者身份标签不输入学生。第一轮固定一个标准编辑档，不同时搜索多档强度或多个prompt。起步8K是完整输入加目标预算，按锁定tokenizer及Spark实测确定；不得静默截断长文章。超长材料保留为明确覆盖缺口，后续另测长上下文或全文分段方案。

32次update只是小规模学习试验。loss下降不证明好读；源文对比也不能替代基座对比。新评估的默认扩充门槛为24篇SFT原样输出无未解决实质内容错误、空输出或截断，16篇问题文相对基座和相对原文的两项模型辅助阅读比较分别至少9篇偏好SFT，8篇对照相对原文无明确退化；译文问题层在两项比较中也单独有多数偏好。它不是统计显著性或人工产品验收；细则、失败分流和新阅读反馈要求见执行文档。评估一旦读过，后续据此调参就需新评估材料，旧集合仅作回归。

**新机器先交付8篇教师流程和Spark运行记录，然后补trainer；数据与兼容检查齐备才开正式SFT。** Spark暂未连接时继续选材、教师稿和离线数据工具。无需重新选择模型、调用旧GPT-4.1、尝试便宜API或重新讨论NLP reward；DPO/RL继续放在可用SFT之后。

### 本次新增判断

- 目标继续是“让读者看得舒服”：改善公众号、媒体解读、科普、技术说明等完整中文信息文章，包括译文；保留事实、条件、归属、否定和不确定性。不是作者身份检测。
- 使用官方`Qwen/Qwen3.5-27B`，原始BF16权重，revision为`fc05daec18b0a78c049392ed2e771dde82bdf654`。先做基座和LoRA兼容检查，再推进SFT；本次没有更换模型或精度。
- 官方规格为128GB统一内存、273GB/s带宽、Arm CPU与GB10 GPU；checkpoint约51.75GiB。容量上值得尝试27B BF16加LoRA，但系统与CPU共享内存，完整文章的峰值、混合注意力反向传播与高效kernel仍未验证。
- Spark应使用适配aarch64/GB10的PyTorch/CUDA环境。现有`configs/student-cloud-probe-requirements-v1.txt`只是待验证组合；不能机械照搬x86环境，也不能把官方Llama示例当作本项目Qwen3.5已兼容的证据。
- 先前给出的Spark首次摸底4—8小时，以及假设100篇、每对6000 tokens、2 epochs的小训练另需12—36小时，只是粗略占机预算。没有训练实测，也没有现成100条教师数据；适配与实际吞吐可能改变时长。优先用自有设备测量，不需要为准备数据持续租卡。
- 依据、时长算术和官方链接均记录在[27B BF16方案](docs/routes/compact-refiner/student-sft-plan-v2.md#dgx-spark与分阶段预算2026-09-17)。本次仅补充文档，无新增模型API费用、原始语料或训练产物。

### 已有成果与不能丢失的边界

- Microduck已认可全文：`data/local/microduck-readable-transfer-v1/candidate-v2.md`；维护者评价“有一些翻译腔，但是总体来说还不错，至少没什么2025年后的AI的臭味”。由当前Astra及原生子任务直接中文改写、复核产生。保留原稿和反馈，不再要求同一首次评价。
- 《亡灵遗产》已认可局部补充稿：`data/local/gpt4-turbo-followup-v1/partial-restoration-v2.md`；维护者评价“这个局部补充稿挺好的，至少我愿意读”。仍有全文遗漏，不能直接当完整训练目标。后来的2068字符修订没有新的人类评价。
- 当前开发原型为`data/local/student-sft-preparation-v2/development-pair.json`：原网页标题加正文作为输入，Microduck已认可第二版作为目标。只有一条，`training_eligible=false`，不是正式训练集或holdout。token数和token级loss mask尚待运行验证。
- 教师稿和研究复核使用当前Astra或原生子任务；停止廉价托管模型实验。GPT-4.1仅保留历史文风例子，不作教师、研究判断或产品依赖。Azure批次及其修订不用于教师数据。
- 原始语料、失败研究、来源分层和已认可反馈已在此前提交中保留。最新模型阶段清单为`handover/student-transition-2026-09-15/artifacts.json`，157项、2,147,362字节；更早完整研究清单为`handover/release-2026-09-15/artifacts.json`。不要重开旧final test、validation reserve、暂停的87候选池或撤回的Cowork读者任务。
- 本机`.env`、真实密钥、Azure资源地址、live账本与私有缓存继续忽略，不随Git迁移。当前官方公开权重路线无需恢复旧API凭据才能继续；若以后确需使用凭据，单独安全配置，不从研究归档恢复认证信息。

### 新机器从这里继续

新建checkout可使用：

```bash
git clone --branch init https://github.com/hooyao/DeAIodorant.git
cd DeAIodorant
python experiments/verify_research_handover.py --inventory handover/student-transition-2026-09-15/artifacts.json
python experiments/student_sft_preflight.py
```

已有checkout先检查并保留未提交改动，再切换`init`并执行`git pull --ff-only origin init`。本项目只提交到`init`，`main`保持`af751e236c084c0de3cc45a5979749bad0778378`。

1. 先读本节及27B方案，完成上述离线检查；恢复结果和本次发布检查见`handover/spark-priority-2026-09-17/validation.json`。最近一次完整测试为2026-09-15的263项通过，本次文档交接不把它写成重新运行的结果。
2. 在维护者提供的新设备上下文中核实Spark本机或连接方式。检查架构、可用统一内存、驱动、磁盘空间与支持GB10的容器；记录实际版本和镜像digest，安装问题与模型问题分别排查。
3. 先用锁定tokenizer实测完整文章长度和loss mask，再运行官方BF16完整基座生成，检查EOS/长度停止与全文内容。`student_sft_preflight.py`的`--execute-cloud-probe`只是沿用的参数名；脚本限制Linux/CUDA/BF16，并未限制x86或要求设备必须是租赁云主机。
4. 基座可用后再做已有3步LoRA兼容检查；验证梯度、峰值内存、adapter保存重载。后续用连续完整训练步测稳态吞吐。显存或kernel有问题先诊断，不静默截断文章或改成量化权重。
5. 同时继续准备真实信息文章的Astra教师对，包含译文，按文章与来源去重并隔离开发和未见评估材料。数据和兼容检查完成后才开始正式SFT；单条原型过拟合不能当产品改进，DPO/RL仍在后面。

## 2026-09-15检查点：官方Qwen3.5-27B BF16与SFT

维护者明确GPT-4.1只用于旧模型文风例子，不能解题、生成教师数据或成为产品方案；随后要求“27b都算是小模型，不要浪费时间在便宜的api接口上”“使用正常的qwen模型”。当前以 `configs/model-roles-v3.json` 为准，停止Azure研究调用及廉价API摸底，采用官方Qwen3.5-27B原始BF16权重直接云GPU运行、微调。下方旧授权和4B/9B安排只保留历史，不能用于恢复这些路线。

固定模型 `Qwen/Qwen3.5-27B`，revision `fc05daec18b0a78c049392ed2e771dde82bdf654`，官方声明Apache-2.0许可，权重本身约51.75GiB。资料在 `data/local/student-model-selection-v1/`。当前Astra负责教师稿和复核，Microduck已认可稿形成一条development序列化原型，不是完整训练集。

`experiments/student_sft_preflight.py`默认只离线检查，已通过；Linux cloud模式才加载27B BF16，可先baseline-only再3步LoRA兼容检查。它校验实际messages与原文/教师文件一致，检查正文loss边界，不静默截断、不训练视觉模块、不向CPU/磁盘卸载，并记录EOS/长度停止。两个静态审查P2已修复；实际token mask、梯度、多卡和adapter重载仍待云端测量。

当前没有权重下载或训练；本机tokenizers下载发生TLS握手失败，未关闭验证或猜token数。下一步需要云GPU：起步1张80GB A100/H100，主机RAM建议128GB、可用盘200GB。先做正常基座和小批次LoRA，若显存不足再用1张96GB或2张80GB。首次预留1—2小时，按实例单价计费；尚无云主机连接信息。详见[27B BF16计划](docs/routes/compact-refiner/student-sft-plan-v2.md)。

此前旧模型四篇批次已经关闭：4次初稿、4次修订，Azure计划价估算0.77026美元，真实账单未知；原始输出、精确操作、复核和Root收尾保留，不作为SFT教师目标。Azure最新账本快照为 `data/local/azure-readable-batch-v1/azure-final-ledger.json` 与 `azure-final-initialized.json`，恢复时不能回滚到早先连接检查快照。纠正后没有新增Azure调用。

已停止的4B/9B探索和两轮9B托管诊断也保留；OpenRouter报告费用共0.00214532美元。默认接口有多语污染，固定BF16服务的首篇仍有目标修辞与内容偏移，但接口结果不能当官方权重基线，也不继续研究服务商。客户端1.2路由限制改动保留，263项离线测试通过。新产物清单在 `handover/student-transition-2026-09-15/artifacts.json`，详见[阶段记录](docs/routes/compact-refiner/reports/student-transition-v1.md)。

以下是旧检查点。

## 新增可用资源：Azure GPT-4.1

维护者提供已有Azure `gpt-4.1`部署和约50美元额度，已将三项Azure配置安全存入Git忽略的 `.env`，OpenRouter配置不变。新增 `src/deaiodorant/refine/azure.py`，使用OpenAI SDK的Responses API；可选依赖为 `.[azure]`。唯一连接检查已成功返回“连接成功”，输入13／输出3 tokens。按保守计划价估算0.00022美元，实际账单未知；连接成功不代表改写质量得到验证。

使用 `configs/azure-gpt41-research-v1.json`：45美元本地预算上限，中央账本 `.azure-responses-budget/`，缓存 `data/local/azure-gpt41-live-v1/`，都保持忽略。需要继续调用时沿用同一.env和账本，禁止为每批新开账本重置总额。计划价10／30美元每百万token不是实际Azure费率，门户余额和其他客户端消费不在本地记录中；失败保留预留且无自动重试。遇到限流按服务端要求停止并安排后续调用，不即时循环。

冻结的脱敏连接记录在 `data/local/azure-gpt41-connection-v1/`；已有 `run.py` 拒绝重复调用。API key、真实资源URL、live账本和缓存不入库，发布扫描同时覆盖Azure与OpenRouter key。248项离线测试与编译检查通过。[接入说明](docs/routes/compact-refiner/azure-gpt41-access-v1.md)包含调用方法、预算边界与实际结果；恢复清单在 `handover/azure-gpt41-2026-09-15/artifacts.json`。当前没有新的文章实验、训练或GPU操作。

## 当前综述与下一批研究

维护者要求汇总进度和后续研究；完整综述见[研究检查点](docs/research-checkpoint-2026-09-15.md)。当前核心成果是《亡灵遗产》局部稿与Microduck全文稿各自获得正向阅读反馈；不同来源、明确译文、保守编辑对照和学生模型仍未验证。下一步先做约四篇的新开发小批次，再比较必要编辑环节和便宜小模型能力，最后才决定训练。新批次和模型试验都是计划，尚未执行；既有结果、原文和失败实验全部保留。

## 最新：Microduck 得到正向评价，生成过程已说明

维护者评价 Microduck 第二版“有一些翻译腔，但是总体来说还不错，至少没什么2025年后的AI的臭味”。原话和 `candidate-v2.md` 的 hash 在 `data/local/microduck-readable-feedback-v1/reader-feedback.json`。这是第二篇具体文章的正向反馈，不再等待同一整体评价；轻微翻译腔仍保留为待改善感受，不推断作者身份或2025年前后的普遍差异。

该稿由原生 Astra 编辑子任务参考获认可的《亡灵遗产》稿，用中文完成全文重排和自审，再由另一原生子任务复核、经五处局部修订后交付。没有 Microduck 的 GPT-4 调用、中英互译或训练。详细[方法与反馈](docs/routes/compact-refiner/reports/microduck-method-and-reader-feedback-v1.md)及 `method-provenance.json` 保留实际记录和未保存中间措辞的限制，原候选不改。

另完成一项有界离线选材：10篇既有 discovery/development 元数据未见明确跨语言翻译证据，选择0篇，未阅读全文或提交弱样例。见 `data/local/translated-readable-selection-v1/selection.json`。后续需要转向已明确标注译文来源的开发材料，不能将当前0候选说成整个语料无译文。新清单：`handover/microduck-feedback-2026-09-15/artifacts.json`；没有新增外部API费用或GPU工作。

以下是本次反馈前的检查点。

## 前一检查点：局部补充稿也得到“至少我愿意读”的反馈

维护者说：“这个局部补充稿挺好的，至少我愿意读”。对应文件为 `data/local/gpt4-turbo-followup-v1/partial-restoration-v2.md`，SHA256 为 `62a0a16b1b2ec8a91a735ba48f7050d9b305f6d69dc9d3fdac3a7a11bf127f28`。原话见 `data/local/readable-reference-v1/reader-feedback.json`。这是对该稿的明确阅读意愿反馈，不再等待同一评价；原稿继续保留，剩余内容问题仍需修正，不能当作完整训练目标。

已按[下一阶段安排](docs/routes/compact-refiner/readable-reference-next-stage-v1.md)开始执行，见[进展记录](docs/routes/compact-refiner/reports/readable-transfer-progress-v1.md)：《亡灵遗产》另存四处内容修订（2068 字符，仍未补全），Microduck 已完成完整第二版候选及两轮内容复核。新文章为 `data/local/microduck-readable-transfer-v1/candidate-v2.md`；有限全文审查未发现新的关键内容问题，尚需实际阅读判断。初始计划及源文身份在 `data/local/readable-reference-v1/next-work-items.json`，实际状态另存 `execution-progress.json`。不反复打磨同一篇或再问已有强度；当前不需要额外模型预算或 GPU。

本轮保存新反馈、执行安排及两篇原生 Astra 开发稿和审查；没有改已认可稿件，没有新增外部 API 调用。增量恢复清单见 `handover/readable-reference-2026-09-15/artifacts.json`。以下“局部补充稿无人类反馈”仅是反馈到来前的历史记录。

以下保留此前检查点。

## 前一检查点：GPT-4 Turbo 稿获得明确正向阅读反馈

维护者随后说：“虽然省略了很多东西，但是读起来就好多了”“虽然有一点翻译味，但是更像是人写的”。原话和原稿 hash 在 `data/local/gpt4-turbo-followup-v1/reader-feedback.json`。**当前结果是阅读体验明显改善、信息保留未达要求。** 原稿应保留为有价值的阅读参考，旧保真 fail 不覆盖人类阅读反馈；轻微翻译味和自然度的感受分别保留。下方“没有新的阅读评价”是这条反馈到来前的历史状态，不再作为当前结论。

已从获正向反馈的原样 GPT-4 稿另做[三处局部补充](docs/routes/compact-refiner/reports/gpt4-turbo-reader-followup-v1.md)，当前文件 `data/local/gpt4-turbo-followup-v1/partial-restoration-v2.md`。Astra Root 仅补写版本／EAC、存档条件和故障经过，1201 → 1519 字符，其他段落不变。首份局部稿和独立复核均保留；新版补回首次复核指出的背包内修理条件和技能树仍遗留状态。操作、差异、源文定位及两次局部复核另存；整体尚未补全，其他已知内容问题仍在，新稿也没有人类反馈，不自动继承原稿的认可。不进入训练，不要求维护者继续对旧稿逐句挑错。

本轮没有新增 API 调用或费用，不用外部 GPT-4 重试。下一步保住已观察到的好读感受，同时检查有用信息的表达与恢复；词语、结构和篇幅的贡献尚未分开。恢复清单：`handover/gpt4-reader-followup-2026-09-15/artifacts.json`。

以下保留收到正向反馈前的记录。

## 前一检查点：第一版被否定，GPT-4 Turbo 完成一次试写

维护者已对下方首份改写稿给出明确负面反馈：“下边的我也不想看了，第一段就这么恶臭”。后续又指出强行对比、设问加核对资料、操作／后果堆叠、“最致命”和重复稳定版疑问。**不再等待第一版的首次反馈，不要求维护者继续逐句挑错。** 完整原话和第一版 hash 关联在 `data/local/gpt4-turbo-article-v1/reader-feedback-on-v1.json`。旧稿、旧计划和旧含义复核未改。

按维护者随后的指定，检查了 OpenRouter 的 GPT-4，并仅完成一次 `openai/gpt-4-turbo` 全文付费试写，费用 **0.07395 美元**。原样稿为 `data/local/gpt4-turbo-article-v1/rewritten-article.md`；完整输入 3342 字符，输出 1201 字符。模型自行摘要化并遗漏 EAC 等要求，保真复核不通过。最后提到的稳定版句子被整段删去，不是改写成功。没有维护者对 GPT-4 Turbo 输出的新阅读评价。单句 `openai/gpt-4` 请求此前被本地预算预留拦住，账本零交易，没有相应模型回答。

详见[本次报告](docs/routes/compact-refiner/reports/gpt4-turbo-article-v1.md)。`response.json`、完整 prompt、模型目录快照、预算、机械与独立内容检查均保留。模型原稿没有经过 Root 二次润色；可只读运行 `python -X utf8 data/local/gpt4-turbo-article-v1/check.py`。新产物清单在 `handover/gpt4-turbo-2026-09-15/artifacts.json`。两个 `run.py` 仅保留复现过程，已有请求时拒绝重发，归档缓存不再写入。

没有后续付费重试、批量模型对比或训练。通常仍使用当前 Astra／subagent 和便宜小模型，本次 GPT-4 Turbo 是维护者指定的一次试写。下一步处理实际信息关系与阅读表达，同时保住内容；不再用少量词语替换或大幅删文代替完整改写。Markdown 已提交到 Codex 文件面板队列，不能据此声称已实际显示；没有尝试浏览器预览或绕过之前的 URL 限制。

以下是本轮反馈之前的历史检查点。

## 当前产品目标与改写稿

维护者最新将目标明确为：**让读者看得舒服。** 范围限于公众号、媒体解读、科普、技术说明等向公众传播信息、以把问题讲清楚为目的的文章，包括相关译文。排除艺术文体；改善惹人反感的表达、难读的措辞和语句排列，保留原意与有效信息。作者身份判断、特征数值或标注 schema 不是交付目标。

维护者已回答 n01 校准：“不胜枚举，很臭”，并定位四处讲解预告、层级揭示和读者低预期。原话见 `data/local/cognitive-move-contract-probe-v1/reader-calibration-response-v1.json`；不要再询问同一强度。后续目标澄清原话见 `data/local/project-goal-confirmation-2026-09-15.json`。

已完成一篇信息文章的[有限改写试做](docs/routes/compact-refiner/information-refinement-pilot-v1.md)。阅读稿为 `data/local/style-intervention-v1/refined-article.md`，原文对照为同目录 `original-article.md`。六项呈现调整与四项长段分组已通过独立含义复核，原文、提案、计划、四种回放版本及变更日志均保留。没有读者偏好结果、训练导出或 reward 验证；配置分档、旧存档要求与补丁关系等原文内容边界仍未核实。

下一步围绕这类实际改写是否更清楚、更舒服收集反馈，再在另一篇已确认强例上检验；不继续将全部工作投入通用字段或各种文体。HTML 原型只通过静态文字检查，本地预览被浏览器 URL 安全策略拦截，未绕过；交付以 Markdown 稿为准。新增文件清单见 `handover/information-refinement-2026-09-15/artifacts.json`。

以下保留此前字段开发的历史检查点。

## 本机续研检查点：契约 1.1 的四篇新文章检验

已完成[本轮报告](docs/routes/compact-refiner/reports/cognitive-move-contract-probe-v1.md)：四篇新文章、八个单篇任务、32 项详细记录，393 处引用机械核验通过。新工具及默认离线测试为 201 passed。原 2,198 项归档及旧 36 条记录恢复检查通过，未改写。

明确来源链、普通条件和若干读者态度能被保留，但 proposer 的当前发言者／更早出处、暗示预期及“仅支持”的否定角色仍有编码歧义。一处省略说明把时间疑问扩大为等待意向。两份回答先遇到输出目录缺失，其中一份重建载荷时有措辞漂移，已保留偏差和排除它后的敏感性说明。不得把八份都称为无偏差首次生成，也不得转成自动特征、reward 或训练输出。

当时不继续扩张 schema 或回改回答，`data/local/cognitive-move-contract-probe-v1/reader-calibration-request.json` 保存了原始校准请求。此后维护者已明确回复“很臭”，当前进入上方信息文章改写试做；请求文件保留当时的 pending 状态，不用它覆盖后续反馈。旧字段结果、原文及判定在 `data/local/cognitive-move-contract-probe-v1/`，对应原增量清单见 `handover/contract-probe-2026-09-15/artifacts.json`。

```powershell
python experiments/cognitive_move_contract_probe.py verify --run data/local/cognitive-move-contract-probe-v1
python experiments/verify_research_handover.py --inventory handover/contract-probe-2026-09-15/artifacts.json
```

以下是上一台机器的完整归档检查点，其旧“下一项可执行工作”已经由本轮部分执行。

本文件是本次完整归档的最新入口。维护者已明确要求将现有进度和全部研究文件提交、推送，无需再次确认。提交分支为 `init`；`main` 保持初始化提交。发布前基线为 `47ba3bfacba5f0a808ab998a49f5a15bfa96e1c4`。

## 从这里恢复

```powershell
git clone --branch init https://github.com/hooyao/DeAIodorant.git
cd DeAIodorant
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe experiments/verify_research_handover.py --inventory handover/release-2026-09-15/artifacts.json
.\.venv\Scripts\python.exe experiments/cognitive_move_pilot.py verify --run data/local/cognitive-move-pilot-v1/run
```

Linux/macOS使用`.venv/bin/python`。项目最低Python为3.10；本次使用Windows和Python 3.13.14。恢复核验只读文件，不调用模型、网络或GPU。原交接的993项和首轮续研的127项仍可用各自原清单核验；本次[完整研究清单](handover/release-2026-09-15/artifacts.json)统一覆盖实际入库的`data/`与`feature_runs/`研究文件。[发布前验证记录](handover/release-2026-09-15/validation.json)记录测试、完整性、文件覆盖和凭据排除结果。

## 当前研究结论

目标仍是改善完整真实中文文章的机械化风格及实际阅读缺陷，保留原意、事实、限定、归属和有用细节。中文译文在产品范围内。优化结果是读者继续阅读意愿及保真，时间分组、作者身份猜测或AI detector不能替代它。

已完成[篇章动作首轮工程实验](docs/routes/compact-refiner/reports/cognitive-move-pilot-v1.md)：两篇已暴露原文、六案例、18条件、36条隔离模型记录；191处引用与输入精确对应。小幅等义变化的核心解释保持，否定状态、价值重点和因果情态等变化得到反映；M04一条记录未明确保留估算提出者。M01/M05的先前说法字段及M04的评论证据还存在角色或指向歧义，不能把非空字段直接统计成纠正次数或读者误解。

这不证明泛化准确率、读者收益或可用reward。M05从设计时就是数量字段覆盖探针，不能冒充核心语义操纵。记录使用同模型家族，精确后端版本不可知；两个来源及重复条件不能当36个独立样本。

另完成[真实文章发现](docs/routes/compact-refiner/reports/independent-media-discovery-v1.md)：8次搜索、6次文章GET，5篇获得完整文字，共25,504字符、286块、61处精确引文。d01的品牌二分和d02的重复购买指引是后期助手候选；两篇早期文章保留营销夸张/栏目排比反例，d06单列过渡期。图片表格、页面视觉效果及上游来源未核实，没有新人工强度标签，也没有严格匹配的前后对照。

维护者原有评价继续有效：Microduck为强正例，百度为较低强度参照；Cowork预览已撤回，不重复提交。更换连接词不能自动消除修辞动作，正常中文省略也不能自动判为阅读缺陷。

## 下一项可执行工作

1. 使用[记录契约1.1草案](docs/routes/compact-refiner/cognitive-move-record-contract-v1.1.md)，明确否定对象、先前持有者、条件基线的不同角色；给被分析的估算绑定提出者和报道层级；将读者证据绑定到具体命题。
2. 在看结果前固定新文章、任务分配及判定。按文章隔离，避免一个任务通过其他焦点的全文见到相邻条件。旧18个packet和36条输出已暴露，保持原样，不能重标后声称独立通过。
3. 已阅读全文并用于挑选的五篇新文属于discovery。需要新验证材料时，先冻结另一个未读集合，不打开旧validation reserve，也不重筛旧87候选。
4. 只有测量可用后，才准备有界编辑、保真检查和新的读者评价。本次没有产品编辑、训练导出、SFT、DPO或RL，无需GPU。

## 本次还找回了什么

此前交接主要覆盖当前工作树的993项文件。此次按“所有现有文件”检查主目录和旧工作树，另找到了历史语料、标注与实验资源，均按可发布范围保留。`import-plan.json`和`import-result.json`记录来源、hash、重复及排除，复制不改源文件。

- `data/local/post_reader_handoff_v1*`、`post_reader_handoff_v2`、`post_reader_handoff_v3`及`post_reader_staging_v1/v2/v3`：既有交接/采集快照。
- `data/local/translation_v2_review/`、`translation_v2_smoke/`、`machine-smoke-20260820/`、`dgx-spark-qwen38/`：既有复核、采集和硬件实验记录。历史硬件命令只说明当时环境。
- `feature_runs/`中补齐的旧分析、实验、对照和参考资源：保留真实文件状态，不将它们升级为成功证据。
- `data/local/recovered-worktree-2026-09-15/`：与当前文件内容不同的旧工作树版本，另存而非覆盖。

这次“找回”指文件系统和原始字节核验，不意味着重新读取或验证了旧保留集标签，也不证明旧语料已准入、可代表总体或每份历史manifest都满足最新研究口径。早期文档关于“本机缺失”的描述保留为当时观察；当前物理可恢复范围以新清单为准。

## Label Studio进度完整性

旧任务导出合计只覆盖39条当前标注，原数据库实际有3项目、328任务、41标注。新的[data/local/label-studio-research-archive-2026-09-15/](data/local/label-studio-research-archive-2026-09-15/)补齐项目2遗漏的两条，保存任务、结果、状态、配置、原始ID及关联。328是任务数，不代表互不重复的文章数。这些是恢复的旧研究记录，不是本轮新增人工判断。

原SQLite含账号、密码、token、登录及存储配置，继续留本机；新包仅导出白名单研究数据。一个旧export包含本地标注用户名，原件留本机，新镜像只移除`/0/drafts/0/created_username`，其余JSON值一致，并保留其中一条历史草稿。详见[归档说明](handover/release-2026-09-15/label-studio-archive.md)。新机器需新建账号并做导入适配/ID映射；本次没有测试Label Studio应用导入，不能把研究包称为完整登录系统备份。

## 运行与冻结约定

首次两个标注子任务即使使用`fork_turns=none`仍收到了自动注入的旧指南标签，均已排除；正式任务在中性指南下启动，原指南随后按字节恢复。不能只凭“不继承对话”宣称盲法。启动、排除和恢复记录在`data/local/cognitive-move-pilot-v1/run/launch-*.json`及`exposed-attempts-closure.json`。

原始语料、首次标注、协议、映射与历史报告不因发布而回写。历史清单里的`local_task_worktree_not_committed_or_pushed`是生成当时的存储状态，原值保留；本次提交把其列出的文件实际入库。新的本地实验仍使用新版本的被忽略目录；已经入库的历史API缓存不能继续写。

文档中文。强模型工作使用当前Agent/隔离子任务；OpenRouter只限已核对预算的便宜小模型。没有恢复外部Astra文档迁移请求。当前无可用DGX Spark，本地GTX 1080不做SFT；确需训练时先说明模型、方法、显存、运行时间和费用，再使用维护者提供的云GPU。

## 发布范围

本次提交包括现有源码/测试/文档、完整研究清单内的语料与运行产物，以及脱认证的标注归档。保留`.gitignore`对未来本地文件的保护，当前快照按清单显式加入Git。`key.json`、`answer_key.json`等研究映射保留；它们不是认证凭据。

`.env`、真实凭据、原认证数据库、含标注用户名的原export、运行锁/进程文件、服务日志、虚拟环境、可重建缓存、安装元数据和模型运行文件不入库；研究内容有必要时已由安全镜像保存。排除原因与扫描处理见本目录发布记录，不删除本机原件。公开语料与参考资源保留来源；归档不额外认证再分发或训练许可。
