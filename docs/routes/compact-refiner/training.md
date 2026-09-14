# 小型精修模型训练计划

政策草案版本：`compact-refiner-training-1.1`。尚未选择或运行 base checkpoint、训练后端或超参数配置。以下数值配置是规划建议，不授权启动训练，也不是已确定的硬件需求。

## 模型角色

区分草稿生成器、候选编辑者、小型 student、意义保留复核者和偏好读者。一个模型承担多种角色时须明确记录。自我一致性不等于独立人工 validation。

当前助手可以直接开发编辑政策，并提出经过仔细审查的候选。额外 OpenRouter 调用应服务具体需要，例如多样来源草稿或可复现小模型基线；当前调用范围遵循[路线说明](README.md)中的最新模型限制。不要付费调用额外模型，只为获得看似 gold 的多数票。

小型 student 学习修改完整真实中文媒体文章，包括译文，同时保留来源主张和有用信息。此前事实任务说明的生成任务是辅助工程记录。不要训练文章作者身份分类，也不要把旧人类文章作为任意新内容的未配对改写目标。

## 必需的译文输入能力

维护者明确要求自动优化中文译文。标准输入是中文，外文原文可选。已接受训练和独立评估同时覆盖直接中文及翻译或混合输入，provenance 未明的保持未知。

涵盖具体中文句子或指代修复、重复篇章框架，以及可凭现有内容修复的信息推进问题。包含应保持不变的连贯译文。不得删除技术区别、压缩掉限定，或为使译文自然而编造缺失前提。

原语言文本辅助整理时，将原文、译文、转载、改编和全部编辑归入同一 provenance 组和 split。借助原文的整理不能将外文原文泄漏进仅中文评估输入。单独的可选原文组需要披露自己的输入约定。

训练就绪要求已有复核过的译文输入示例和独立译文评估计划。报告该层的有用偏好、意义保留、fallback 和覆盖。仅在直接中文上成功，不满足用户要求的产品范围。

## Student 选择

先评估约 1.5B-4B、可开放训练且具备中文能力的 instruction checkpoint。这是搜索范围，不表示每个模型都适配已观察 GPU 或能解决任务。只有记录的失败足以支持额外成本时，才比较更大的 student。

选择 checkpoint 前记录：

- 精确仓库 ID 与 revision、tokenizer、chat template 和 special token；
- 权重可用性，以及适配和计划分发的 license；
- development 输入上的中文编辑质量；
- context length 与完整输入、输出 token 要求；
- 支持的 precision、quantization、kernel 和训练栈兼容性；
- 计划主机上实测内存、吞吐、失败和成本。

托管模型名称不足以证明存在相同的可训练 revision。OpenRouter prompt 基线仅是近似对应版本时须记录。最终训练归因需要从实际选定 base checkpoint 取得未微调基线，并使用相同评估政策。

## 算力前提

维护者于 2026-09-14 确认不使用本地 GTX 1080 进行 SFT，将在训练就绪时提供云 GPU。没有 `gx10`。本地工作限于数据准备、检查、统计和产物处理；OpenRouter 提供获授权范围内的推理。尚未提供训练主机，也未开始训练。

维护者选择云实例前，准备针对工作负载的硬件说明，给出最低可用配置和具有内存、时长余量的推荐配置。包含：

- GPU 型号或必需能力、GPU 数量、每卡 VRAM；
- 选定 base checkpoint、参数量、precision，以及 LoRA、QLoRA 或 full-tuning 方法；不能只按参数量估算；
- 最大完整 sequence length、microbatch、gradient accumulation、effective batch size、optimizer 和节省内存假设；
- 主机 CPU、RAM、工作存储、checkpoint 保留和下载需求；
- 兼容 OS、Python、CUDA 与 driver、framework、kernel 版本；
- 预计吞吐、总 GPU-hours、价格假设和总成本；
- 未知项及验证估计所需 smoke test。

计入权重、optimizer state、gradient、activation、临时 buffer 和内存余量。明确估计是否仅覆盖 SFT；DPO reference 存储，以及日后 RL rollout 或 reward 工作负载须单独估算。

选定模型和工作负载前，不给出确定 VRAM 要求。云主机提供后，先验证固定环境和完整 forward、backward、checkpoint smoke test，再按数据集规模执行。本地 Python 3.13.5 不是训练栈要求。API 推理权限本身不提供微调能力或可导出权重。

## R2：已接受编辑数据

构建[数据约定](data-contract.md)定义的人工复核导出。首个工作收集预算为 200 条已接受记录，包括真正不修改的案例和不同编辑幅度。独立组数与示例数分开记录。该预算可在声明的 development 阶段调整，不是最小数据量定理或晋级阈值。

首次训练可能揭示数据覆盖、语义复核或标签一致性不足。增大模型或引入 RL 前，先扩充这些维度。未复核助手或模型编辑保存在独立提案池，不悄悄升级合成接受标签。

## R3：SFT

训练和评估使用同一 student 输入约定：任务指令、合法上下文或锁定内容、强度及原始段落。训练模型只返回修改后或不变的段落。输入部分 mask loss，目标响应部分计算 loss。不训练私有模型推理、复核笔记、特征分数或答案键。

若选定训练栈支持，先采用 parameter-efficient adaptation。保留一个 base model 和一个初始配置，使失败可解释。

以下仅为暂定起点，在硬件 smoke test 后、训练前写入实际运行 manifest 并冻结：

| 设置 | 初始建议 |
|---|---|
| 方法 | LoRA；QLoRA 仅在兼容性证明后采用 |
| Rank / alpha / dropout | 16 / 32 / 0.05 |
| 目标模块 | 选定 attention projection 模块，按实际架构解析 |
| Learning rate | `1e-4` |
| Epoch | 初始 1 |
| Effective batch size | 16 组或示例，记录实际组构成和 accumulation |
| Sequence length | 用固定 tokenizer 测量完整真实文章输入加输出的 token 长度后确定；4096 不是此语料的默认值 |
| Seed | `20260914` |
| Precision 与 optimizer | 按实测兼容性选择，绝不从旧命令推断 |

不允许悄悄截断。超出已验证 token 预算的示例，须注明理由排除，或按保留必需上下文和组身份的版本化政策分段。不得以暴露另一示例目标或允许跨示例 attention 的方式 packing。

当前翻译访谈 development 案例，仅原文就有 21,891 个 Unicode 字符（计得 17,540 个 CJK 字符），尚未包含修改响应。这是字符数，不是 tokenizer 测量，说明合成 pilot 的短上下文假设不适合估算硬件。请求 GPU 规格前，测量完整输入加目标长度，选择受支持的 long-context 配置，或经过单独评估、保留上下文的分段政策。

运行前冻结 validation 安排、checkpoint 选择规则和训练预算。候选搜索保持小规模并记录；final-test 反馈不能进入 learning rate、prompt、checkpoint 或停止决策。训练 loss 下降不自动使 checkpoint 晋级。

保存 adapter、base revision、tokenizer 与 template、导出 hash、实际配置、依赖快照、seed、训练日志和 checkpoint hash。train 与 validation loss 同读者、意义保留结果一起报告。失败或中断运行仍保留账本条目。

## R4：DPO

DPO 是离线偏好学习步骤，不要求在线手写标量 reward。只有 SFT 已具备可用编辑行为，并积累明确可靠的同输入人工偏好，才开始。

从选定 SFT checkpoint 初始化，并以其不可变副本作 reference。风格偏好对的两个候选均须通过意义保留。不安全输出保存在单独 challenge 或审计集，避免把风格偏好与事实正确性混为一谈。平局、两个都差、未知判断和未解决复核分歧，不进入二元 DPO 对，但保留计数。

首个暂定配置为 beta `0.1`、learning rate `1e-5`、一个 epoch、effective batch size 8、seed `20260914`。执行前在运行 manifest 中确定实际 adapter 模块、precision、sequence 处理、optimizer 和 reference 存储。这些默认值可按 development 证据改变，但每次都要记录；它们不是已验证超参数。

监测响应长度、不必要改写、风格丢失、事实失败和 chosen/rejected log-probability 行为。即使没有显式 reward model，preference optimization 也可能利用长度或标注偏差。在同一独立评估 protocol 下，将 DPO 与其 SFT 父模型比较。

## R5：Online RL 的条件

Online RL 暂缓。reward 不必可微，也不必基于传统 NLP；低成本标量很方便，但便宜不说明它与读者偏好一致。

RL 运行前要求：

1. 冻结 reward，并有独立人工偏好证据；
2. 意义保留检查有记录的漏检率和人工审计；
3. 完成[评估](evaluation.md)中的取巧测试与特征 ablation；
4. 与 SFT、DPO 比较，包括输出长度和编辑覆盖；
5. 固定 rollout、token 与成本预算、reference policy、优化设置、中断行为和 rollback checkpoint。

以读者偏好作为质量目标。传统 NLP 可以提供已验证辅助信号；字面变化和过度编辑惩罚是不完整的安全信号。绝不以严重语义失败换更高风格分数。运行时接受流程仍须拒绝或撤销失败编辑。

若 reward 上升但独立读者偏好停滞、内容失败增加、输出坍缩为一种风格或不修改占主导，则停止。Online RL 没有实用增益时，保留更简单的 checkpoint。

## 推理操作

首批从每次一个请求开始，request timeout 为 120 秒，每项最多重试两次。只重试暂时性失败，遵守服务重试指令，记录每次尝试与成本。截断或空回答是失败候选；绝不以隐藏 reasoning 文本代替。不在运行中隐性改变 token 上限或 prompt。

初始接口 smoke test 采用 USD 1 保守工作上限，首批 development 推理累计上限 USD 5。这是 agent 在既有授权内选定的运行限制，不是报价。启动前获取当前模型价格并估算最坏请求成本。即将超过上限时停止；继续前记录预算修订决策。实际调用、失败尝试预留和成本记录在[实验报告](reports/cr001-preflight.md)。

任何长时间生成或训练任务，都在约一分钟后检查真实进程、日志或提供者任务状态，并在预计时长内分散检查约五次。Watcher 仅辅助；完成依据退出状态、终止标记和验证产物。旧写入者可能仍存活时，绝不向同一可变缓存重新启动任务。
