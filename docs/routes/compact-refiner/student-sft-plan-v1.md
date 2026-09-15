# 新小模型SFT路线：第一个可部署学生

本版4B/9B优先安排已被维护者后续要求取代。当前使用[官方27B BF16方案](student-sft-plan-v2.md)；旧4B预检脚本留在 `data/local/student-model-selection-v1/retired-4b-preflight.py`，当前同名实验入口已改为27B，不要按本页显存预估运行。

日期：2026-09-15。本路线落实维护者最新要求：最终方案必须是可自行部署的新小模型微调。GPT-4.1只保留历史文风例子，不参与继续解题、教师数据或产品运行。当前Astra和原生子任务负责教师稿与复核；模型角色以 `configs/model-roles-v2.json` 为准。

## 已完成的准备

已查阅官方Hugging Face资料并锁定Qwen3.5-4B与9B的revision，许可声明为Apache-2.0。首个学生候选为4B，9B作为容量对照，尚未将任一个模型描述为已验证适合本项目。

4B revision：`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`；9B revision：`c202236235762e1c871ad0ccb60c8ee5ba337b9a`。它们包含视觉编码器以及混合注意力文本模型，不能直接照抄普通Transformer的LoRA模块名。官方支持纯文本推理，不等于训练栈已经验收。

已从获认可的Astra Microduck稿建立一条development序列化原型，不使用GPT-4.1稿作为教师目标。两份官方模板一致，non-thinking前缀能与完整source+target文本严格衔接，完整序列6895字符。模板没有generation标记，所以不直接依赖`assistant_only_loss`自动推断。字符检查不等于token级loss mask或长度检查。

本机安装tokenizers运行库时，官方wheel主机的TLS握手失败；pip、requests和Windows curl均未成功，没有关闭TLS验证。没有下载模型权重，没有开始训练，也没有猜测token数。云端预检将先完成token化及边界检查，再加载权重；超长立即报告，不静默截断。

## 托管摸底的用途与限制

对便宜的Qwen3.5-9B做了两篇已知开发文章的微调前摸底，没有提供Astra参考稿。默认路由返回的Darkbloom稿夹杂无关多语片段和数字损坏；目录将其部署标为FP4。这些输出不作有效模型能力基线或教师数据。

随后固定同价DeepInfra/BF16路由，用相同消息和共同采样参数复核。服务商和精度同时改变，不能把差异单独归因于量化。托管后端的实际精度、权重revision和部分默认参数不能独立验证；未来SFT前后比较必须在云端使用同一锁定权重及同一推理配置。

Microduck的BF16稿未再出现明显多语污染，但仍保留“先厘清”“买的是管线，熬的是时间”等目标写法，并把漏tick写成丢包、凭运行记录增加算法效率结论。这些是具体能力缺口，不能拿模型自己的输出作为教师答案，也不能当作人类评分。

## 第一次云GPU工作

第一步是锁定4B基座的推理／训练兼容检查，不是正式训练或效果实验。准备好的 `experiments/student_sft_preflight.py` 默认只检查开发pair和文件身份；加 `--execute-cloud-probe` 才会在Linux云GPU上下载锁定权重，构造正文loss mask，给文本层添加LoRA，运行3个梯度步骤并验证adapter保存重载。视觉参数不得训练，原文prompt不进入loss。输出保存在被忽略的models目录，不提交权重。

推荐单张48GB NVIDIA GPU（L40S、RTX 6000 Ada或RTX A6000），Linux x86_64，主机RAM至少64GB，可用磁盘至少150GB。24GB只作为后续短序列／QLoRA的待测下限，不保证完整文章在当前BF16 probe上可运行。NVIDIA驱动需支持所装PyTorch CUDA构建，脚本要求CUDA和BF16可用。

包版本来自当前公开PyPI元数据，暂固定在 `configs/student-cloud-probe-requirements-v1.txt`；组合尚未实际验证，不能将此清单当作已通过的兼容环境。首次预留1—2小时做安装、下载和短跑，实际费用为所用GPU实例小时单价乘时长；尚无选定云服务单价，不编造金额。通过短跑取得峰值显存和吞吐后，再确定正式训练资源与费用。

```bash
python -m pip install -r configs/student-cloud-probe-requirements-v1.txt
python experiments/student_sft_preflight.py
python experiments/student_sft_preflight.py --execute-cloud-probe --max-length 8192
```

当前只运行了第一种离线计划检查；云端前向／反向和实际loss mask仍待验证。8K是可拒绝超长的初始检查上限，不是已证明足够的最终训练长度。

## 教师数据和正式SFT

先以真实公众信息文章为输入，由当前Astra重新编辑并独立复核，保留原文、目标稿、内容对应和读者反馈。GPT-4.1及异常托管输出都不作为teacher target。已有研究文章全部视为development；后续训练与评估按完整文章分开，近重复、同源改编和已暴露文章不能跨分区冒充未见数据。

先形成少量经过逐篇审查的教师对与真正未用于调试的评估文章，再运行小规模SFT，观察阅读体验、内容保留和过度改写。prompt基线用于判断微调带来的变化，不能替代微调交付。正式数据量、轮次和学习率在数据及短跑结果明确后冻结；当前一条原型不能冒充训练集。DPO／RL后置，不用“而是”次数、句长或任意NLP加权分直接作奖励。
