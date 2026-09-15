# 续研 handoff：2026-09-15

## 本机续研检查点：契约 1.1 的四篇新文章检验

已完成[本轮报告](docs/routes/compact-refiner/reports/cognitive-move-contract-probe-v1.md)：四篇新文章、八个单篇任务、32 项详细记录，393 处引用机械核验通过。新工具及默认离线测试为 201 passed。原 2,198 项归档及旧 36 条记录恢复检查通过，未改写。

明确来源链、普通条件和若干读者态度能被保留，但 proposer 的当前发言者／更早出处、暗示预期及“仅支持”的否定角色仍有编码歧义。一处省略说明把时间疑问扩大为等待意向。两份回答先遇到输出目录缺失，其中一份重建载荷时有措辞漂移，已保留偏差和排除它后的敏感性说明。不得把八份都称为无偏差首次生成，也不得转成自动特征、reward 或训练输出。

当前不继续扩张 schema 或回改回答。新 n01 原文的主观臭味强度校准已单独向维护者提出，`data/local/cognitive-move-contract-probe-v1/reader-calibration-request.json` 记录该请求；目前等待反馈。维护者回答前，不将该文升级为人工强正例，不自动启动下一批改写。新结果、原文及判定在 `data/local/cognitive-move-contract-probe-v1/`，对应增量清单见 `handover/contract-probe-2026-09-15/artifacts.json`。

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
