# 官方Qwen3.5-27B BF16：基座与SFT准备

日期：2026-09-15。维护者明确27B也在小模型范围内，要求使用正常Qwen，不再把时间花在便宜API接口。当前角色以 `configs/model-roles-v3.json` 为准，取代此前4B/9B优先的方案。

## 固定模型与交付

采用官方 `Qwen/Qwen3.5-27B`，revision为 `fc05daec18b0a78c049392ed2e771dde82bdf654`，BF16直接运行。官方元数据声明Apache-2.0许可，checkpoint总参数约277.8亿，权重本身约51.75 GiB；这是存储体积计算，不是推理或训练峰值显存。文本模型为64层混合注意力，没有专家路由配置；发布包包含视觉编码器，本项目只处理文本，不训练视觉模块。

最终目标是用当前Astra制作、复核的教师稿做SFT，并自行部署模型。GPT-4.1只保留旧模型文风例子，不继续解题或生成教师数据；廉价9B接口的诊断到此停止，其结果不作正式基座表现或训练目标。

## 已准备的检查

已保存官方模型卡、config、metadata与revision。27B官方non-thinking模板与开发pair的前缀/完整文本字符边界对齐，完整序列6895字符；实际token长度及token级mask仍需在有tokenizer运行库的环境中测量。本机wheel下载TLS失败，没有关闭验证、没有下载权重，也没有训练。

`experiments/student_sft_preflight.py`现在默认选择27B BF16，默认执行只做离线检查。显式cloud模式会先核对完整source+target长度、正文loss mask，再加载官方权重；不静默截断，不向CPU/磁盘卸载，不做4-bit替代。单卡用single映射，多卡可用balanced；多卡训练组合仍要实际验证。

首次分两步：先生成官方基座的完整开发文章，再运行单条原型的3步LoRA兼容检查，观察有限loss、梯度、峰值显存、生成和adapter保存重载。它验证运行与训练链路，不证明一条样例的微调已经改善阅读，更不构成正式训练集。

## 所需云GPU

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
