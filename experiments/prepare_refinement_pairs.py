"""Prepare three blinded minimal-edit comparisons for Label Studio."""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Pair:
    pair_id: str
    doc_id: str
    target_lines: tuple[int, int]
    original: str
    revised: str
    operations: tuple[str, ...]


PAIRS = (
    Pair(
        pair_id="contrast-01",
        doc_id="44aa81958a6c585ee8c06847",
        target_lines=(15, 22),
        original=(
            "TCAR（TencentCloudAndonRouter）的核心很简单，但在 Router 中几乎没人认真做过——\n"
            "把路由从直接预测标签，变成先推理再选择 Agent 集合\n"
            "。这时候，Router 不再是一个收发任务的转接系统，而是变成了一个具备推理能力的“决策者”。它把路由过程从单项选择变成了“写分析报告+组建任务组”；它的工作职能从挑选队列最前面的 agent 完成任务，到在专家梯队中找到最合适的那个人选来完成任务。\n"
            "它就像是一个拥有顶尖专家团队的，高度聪明且能够自我决策的“项目经理”。\n"
            "能力一：Reason-then-Select（拒绝黑盒，把思考过程写出来）\n"
            "TCAR 在输出 Agent 之前，会先生成一段自然语言推理链，明确说明问题可能涉及哪些技术栈，不同 Agent 的职责边界，为什么多个 Agent 执行是合理的，这让路由不再是黑盒，而是可解释、可 Debug、可持续优化 Agent 描述。\n"
            "能力二：从单挑到团战\n"
            "在 TCAR 中路由结果不再是 one-hot，而是一个 Agent 子集，这一步直接解决了企业系统中最棘手的 Agent 冲突问题：不强行压缩决策，而是保留不确定性，交给后续协作解决。当然，这也要建立在对指令聪明且充分的理解力上。"
        ),
        revised=(
            "TCAR（TencentCloudAndonRouter）的核心方法是把路由从直接预测标签改为先推理、再选择 Agent 集合。\n"
            "TCAR 在输出 Agent 之前，会先生成一段自然语言推理链，说明问题涉及的技术栈、不同 Agent 的职责边界，以及选择多个 Agent 的理由。这些信息可用于解释和调试路由结果，并持续优化 Agent 描述。\n"
            "TCAR 的路由结果是一个 Agent 子集，而非 one-hot 选择。多个 Agent 可以保留决策中的不确定性，再通过后续协作解决冲突。该方法依赖对指令的准确理解。"
        ),
        operations=(
            "Collapse repeated decision-maker and project-manager reframing into the stated routing mechanism.",
            "Replace repeated not-X-but-Y frames with direct declarative claims.",
            "Preserve the reasoning-chain, multi-agent selection, explainability, uncertainty, conflict-resolution, and instruction-understanding propositions.",
        ),
    ),
    Pair(
        pair_id="contrast-02",
        doc_id="0431c592d5de8246cebcb8e2",
        target_lines=(7, 10),
        original=(
            "巨大的压力开始影响创始团队成员与朋友、伴侣的私人关系 —— 这对许多处于初创阶段的创业者来说，是个常见的困境。颇具讽刺意味的是，正是这种人际关系中的紧张感，催生了最终让他们 “柳暗花明” 的灵感。\n"
            "这种灵感来自于一组调查数据。\n"
            "据统计，全球近 50% 的恋爱关系最终以分手或离婚收场。在美国，这一问题尤为凸显 ——1.4 亿对夫妻正面临 “日常联系难” 的困境，其根源并非缺乏爱意，而是情感疏离、沟通缺失与日益增长的 “不同步”。事业压力、社交媒体干扰、快节奏生活，正将原本属于亲密关系的美好时光，逐渐稀释为碎片化的 “背景噪音”。更值得关注的是，这一问题在新一代年轻夫妻与朋友群体中，呈现出愈发严重的趋势。\n"
            "“大多数关系不会突然破裂，而是在日复一日的相处中，因缺乏持续的情感联结慢慢褪色。” 这一洞察，成为社交应用 Candle 诞生的核心契机。这款主打 “亲密关系维护” 的工具，正试图为情侣、密友打造一个 “每日简单且有意义互动” 的私人空间，填补现代生活中情感联结的空白。"
        ),
        revised=(
            "创业压力开始影响团队成员与朋友、伴侣的私人关系。这是许多创业者在初创阶段都会遇到的困境，也促使团队关注亲密关系维护。\n"
            "团队援引的调查称，全球近 50% 的恋爱关系最终以分手或离婚收场。在美国，1.4 亿对夫妻面临日常联系困难。调查认为，许多关系仍有爱意，但情感疏离、沟通缺失和生活节奏不同步会削弱日常联结。事业压力、社交媒体干扰和快节奏生活进一步减少了亲密互动；这一问题在年轻夫妻和朋友群体中更加严重。\n"
            "团队据此开发了社交应用 Candle，为情侣和密友提供每日互动空间，帮助他们维持亲密关系。"
        ),
        operations=(
            "Replace emphatic discovery framing with a direct causal transition.",
            "Convert the ornamental contrast frame into two explicit claims while preserving the negation.",
            "Remove unattributed quotation styling and repeated product-positioning phrases without changing the reported figures or product purpose.",
        ),
    ),
    Pair(
        pair_id="contrast-03",
        doc_id="3c60dc0a981b686870095450",
        target_lines=(79, 81),
        original=(
            "这四步合起来，指向一件比“接口好不好用”更深的事：所有工具和能力，无论是 CLI、SDK、Terraform、MCP Server，还是网关、身份、权限和可观测，最终都是为了让云真正可靠地运转起来。\n"
            "阿里云给出的，正是这样一套面向 Agent 调云的工程框架。至于关键动作该在哪里停下来，哪些场景可以全自动，哪些场景必须人工介入，仍然需要在真实生产环境里不断打磨和沉淀。\n"
            "但方向已经清楚：Agent 调云，不是把\"人点按钮\"换成\"AI 点按钮\"，而是把云操作重新纳入一套可规划、可校验、可追溯的工程秩序之中。这不是给智能套上枷锁，而是给智能划定一条能够被信任的边界——唯有可控，自动化才谈得上真正可用。、"
        ),
        revised=(
            "这四步共同构成一套云操作流程。CLI、SDK、Terraform、MCP Server，以及网关、身份、权限和可观测能力，都服务于云的可靠运行。\n"
            "阿里云据此给出了一套面向 Agent 调云的工程框架。关键动作何时暂停、哪些场景可以全自动、哪些场景必须人工介入，仍需在真实生产环境中验证。\n"
            "Agent 调云并非简单地用“AI 点按钮”替代“人点按钮”。该框架把云操作纳入可规划、可校验、可追溯的工程流程。边界控制用于建立信任；可控是自动化真正可用的前提。"
        ),
        operations=(
            "Remove depth-announcement and direction-announcement metadiscourse.",
            "Replace two paired contrast frames and the shackle metaphor with direct process claims.",
            "Preserve every named tool, control dimension, automation boundary, and production-validation qualification.",
        ),
    ),
)


LABEL_CONFIG = """<View>
  <Header value="只比较阅读体验，不判断哪一版是 AI" />
  <View style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
    <View style="padding: 16px; border: 1px solid #d9d9d9; border-radius: 8px;">
      <Header value="版本 A" />
      <Text name="version_a" value="$version_a" />
    </View>
    <View style="padding: 16px; border: 1px solid #d9d9d9; border-radius: 8px;">
      <Header value="版本 B" />
      <Text name="version_b" value="$version_b" />
    </View>
  </View>
  <Header value="哪一版更顺畅、更愿意继续读？" />
  <Choices name="preference" toName="version_a" choice="single" required="true" showInline="true">
    <Choice value="A 明显更好" />
    <Choice value="B 明显更好" />
    <Choice value="差不多或都不好" />
  </Choices>
  <Header value="可选：哪一版漏了信息、改了意思，或者哪里仍然难读？" />
  <TextArea name="optional_comment" toName="version_a" rows="3" placeholder="完全可以不填" />
</View>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260821)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    task_order = list(PAIRS)
    rng.shuffle(task_order)
    tasks: list[dict[str, object]] = []
    answer_key: list[dict[str, object]] = []
    for task_number, pair in enumerate(task_order, start=1):
        original_is_a = bool(rng.getrandbits(1))
        tasks.append(
            {
                "data": {
                    "task_number": task_number,
                    "version_a": pair.original if original_is_a else pair.revised,
                    "version_b": pair.revised if original_is_a else pair.original,
                },
                "meta": {"pair_id": pair.pair_id},
            }
        )
        answer_key.append(
            {
                "doc_id": pair.doc_id,
                "operations": list(pair.operations),
                "original_side": "A" if original_is_a else "B",
                "pair_id": pair.pair_id,
                "target_lines": list(pair.target_lines),
                "task_number": task_number,
            }
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "tasks.json").write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.output_dir / "answer_key.json").write_text(
        json.dumps(answer_key, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (args.output_dir / "label_config.xml").write_text(
        LABEL_CONFIG,
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir.resolve()),
                "seed": args.seed,
                "task_count": len(tasks),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
