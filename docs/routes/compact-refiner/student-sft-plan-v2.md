# 官方Qwen3.5-27B BF16：基座与SFT准备

日期：2026-09-15。维护者明确27B也在小模型范围内，要求使用正常Qwen，不再把时间花在便宜API接口。当前角色以 `configs/model-roles-v3.json` 为准，取代此前4B/9B优先的方案。

2026-09-17补充：DGX Spark是维护者自有设备，只需电费，后续优先在它上面验证官方27B BF16加LoRA。此前列出的80GB云GPU和x86_64不再作为研究前置条件。资源与预算依据见文末。尚未取得新设备的连接方式，没有启动远程工作；换机恢复入口为根目录`HANDOFF.md`。

**怎样推进SFT：** 按[首轮执行安排](student-sft-execution-v1.md)落实8篇教师流程、64/12/24篇文章隔离、正式trainer、两epoch LoRA及开发/新文章评估。本文件主要记录模型与硬件依据；3步预检不等于正式训练。执行安排的数量与配置是待完成的首轮计划。

## 固定模型与交付

采用官方 `Qwen/Qwen3.5-27B`，revision为 `fc05daec18b0a78c049392ed2e771dde82bdf654`，BF16直接运行。官方元数据声明Apache-2.0许可，checkpoint总参数约277.8亿，权重本身约51.75 GiB；这是存储体积计算，不是推理或训练峰值显存。文本模型为64层混合注意力，没有专家路由配置；发布包包含视觉编码器，本项目只处理文本，不训练视觉模块。

最终目标是用当前Astra制作、复核的教师稿做SFT，并自行部署模型。GPT-4.1只保留旧模型文风例子，不继续解题或生成教师数据；廉价9B接口的诊断到此停止，其结果不作正式基座表现或训练目标。

## 已准备的检查

已保存官方模型卡、config、metadata与revision。`data/local/student-sft-preparation-v2/`的开发pair补入原网页标题，保留原正文与Astra教师稿；27B官方non-thinking模板的前缀/完整文本字符边界对齐。实际token长度及token级mask仍需在有tokenizer运行库的环境中测量。本机wheel下载TLS失败，没有关闭验证、没有下载权重，也没有训练。

`experiments/student_sft_preflight.py`现在默认选择27B BF16，默认执行只做离线检查。显式cloud模式会先核对完整source+target长度、正文loss mask，再加载官方权重；不静默截断，不向CPU/磁盘卸载，不做4-bit替代。单卡用single映射，多卡可用balanced；多卡训练组合仍要实际验证。

首次分两步：先生成官方基座的完整开发文章，再运行单条原型的3步LoRA兼容检查，观察有限loss、梯度、峰值显存、生成和adapter保存重载。它验证运行与训练链路，不证明一条样例的微调已经改善阅读，更不构成正式训练集。

## 2026-09-15的云GPU方案：历史备选

本节保留原始资源估计和命令，不代表当前需要租用云GPU。当前优先使用自有DGX Spark；Spark环境必须另外核实aarch64/GB10兼容性。

- **起步：1张80GB NVIDIA GPU**，如A100 80GB或H100 80GB，用于BF16基座推理和尝试小批次LoRA。权重之外还有激活、logits和梯度开销，因此不保证所有8K设置都能在单卡80GB训练。
- **训练余量：1张96GB，或2张80GB GPU**。如果单卡短跑显存不足，再采用更大显存或多卡；不为了让实验跑通而静默截断文章或换成低精度接口。
- Linux x86_64，建议主机RAM至少128GB，可用磁盘至少200GB。NVIDIA驱动需匹配所装PyTorch CUDA构建，要求BF16支持。
- 首轮预留1—2小时做安装、权重下载、基座与短跑。费用按所选实例单价乘时长计算；当前没有具体实例报价，不编造金额。实测后再确定正式SFT的资源、序列长度和时长。

包版本清单 `configs/student-cloud-probe-requirements-v1.txt` 是待验证组合。离线语法与计划检查已通过，不能冒充云GPU兼容测试。

```bash
python -m pip install -r configs/student-cloud-probe-requirements-v1.txt
python experiments/student_sft_preflight.py
python experiments/student_sft_preflight.py --execute-cloud-probe --baseline-only --max-new-tokens 4096 --output models/qwen27b-baseline-v1
python experiments/student_sft_preflight.py --execute-cloud-probe --output models/qwen27b-lora-probe-v1
# 多卡时在相应命令追加 --device-map balanced
```

GPU输出和权重留在Git忽略的models目录，不能随普通研究快照推送。当前没有云主机连接信息，尚未执行上面两条cloud命令。获得实例后先验证正常官方基座，再继续Astra教师数据、文章级训练／评估分离和正式SFT。

## DGX Spark与分阶段预算：2026-09-17

维护者确认DGX Spark为自有设备，只需电费。当前优先在Spark上测27B BF16基座和LoRA，保留官方模型与精度，不恢复廉价API路线。需要实测内存和吞吐；设备所有权已确认，当前session的访问方式尚未确认。

### 已核验的硬件事实与未验证事项

- [NVIDIA产品规格](https://www.nvidia.com/en-us/products/workstations/dgx-spark/)列出GB10、20核Arm CPU、128GB统一内存和273GB/s内存带宽。网页标称的1 PFLOP使用稀疏FP4口径，不能作为本项目BF16训练速度。
- 固定checkpoint权重约51.75GiB，Spark的总内存容量使27B BF16基座及小批次LoRA值得尝试；128GB由系统、CPU与GPU共享，不能当作全部可用的独立显存。完整文章的激活、临时logits与加载副本仍需测量，尚不能宣布当前8K设置一定放得下。
- [NVIDIA的PyTorch微调说明](https://build.nvidia.com/spark/pytorch-fine-tune/instructions)提供Spark容器和LoRA/QLoRA示例。示例针对Llama，不证明本项目Qwen3.5混合注意力的反向传播和高效kernel已兼容。网页“可微调70B”也不证明单机能做70B原始BF16全参数训练。
- 当前方案只训练LoRA参数，不是27B全参数微调。Spark使用Linux aarch64，需要支持GB10的PyTorch/CUDA构建；不能机械沿用x86安装步骤或用普通pip覆盖已匹配的容器PyTorch。[NVIDIA 26.08容器说明](https://docs.nvidia.com/deeplearning/frameworks/pytorch-release-notes/rel-26-08.html)仅作为候选环境资料，未在本项目验收或锁定新镜像。
- 获得设备后记录系统可用内存、架构、GPU能力、驱动、容器digest与实际包版本；使用官方模型revision，先完整基座生成，再做反向传播和adapter重载。当前3步脚本用于兼容性，不足以代表稳定训练吞吐。

### 时长估计与历史云GPU费用参照

下列时间是安排机器占用和预算的粗估，**没有该模型在两种设备上的训练实测**。安装、约56GB权重传输、kernel编译及输出检查都可能改变墙钟时间。

| 阶段 | A100 80GB预算时间 | DGX Spark预算时间 |
| --- | --- | --- |
| 首次环境、基座、LoRA兼容检查 | 2—4小时 | 4—8小时 |
| 小规模SFT试验：假设100篇、每对完整输入输出6000 tokens、2 epochs，包含少量生成检查 | 4—8小时 | 12—36小时 |

第二行是供询价的试验规模，不是已有100条训练样本，也不是正式SFT效果承诺。纯训练量为120万tokens：若实测10、30、100、200 tokens/s，分别约需33.3、11.1、3.3、1.7小时，再加加载、保存与评估。这里的吞吐按完整输入输出序列计算，即使prompt被mask，其前向计算仍占用时间；各吞吐值是算术场景，不是硬件benchmark。若实际速度或兼容性偏离预算，应先重新估价，不能把表内时长当作上限保证。

当前仅有一条development原型，教师数据还未齐备。后续先在自有Spark上测量，不需要为此充值租卡。此前讨论的云GPU费用公式仅保留为历史参照：小时单价乘使用时长，存储等另计；例如10元/小时运行4—6小时为40—60元，这是算术示例，不是平台报价或当前采购安排。Spark电费需按实际整机耗电与当地电价计算；本次没有测量耗电，也没有把GB10的TDP等同于整机墙上功耗。

软件兼容后，利用连续完整训练步测峰值内存、稳态tokens/s和生成时间，再据实际数据token总量确定下一批预算。教师稿制作与内容复核继续由当前Astra完成，无需让收费GPU空转等待。此次只更新资源判断与预算，没有下载权重、购买资源或开始训练。
