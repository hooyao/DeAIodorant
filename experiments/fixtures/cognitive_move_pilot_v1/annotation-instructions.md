# 中文篇章动作标注说明 1.0

你是独立模型标注者。任务是解释给定全文中指定位置的文本动作，不评价作者身份，不给出文章臭味分数。来源主张不等于已核实事实。

只读分配文件、它列出的六个 packet，以及本说明。任务负责人已读仓库规则，并将适用约束保留在这里：中文说明；忠实引用；保留数量、实体、否定、范围、情态、归属和不确定性；正常中文省略不自动构成缺陷；不得编造原文没有的事实或读者信念；不得读取历史标签、其他标注、key、design、报告、HANDOVER 或 AGENTS 中包含已知评价的部分。本次隔离来自维护者接受的实验设计。不得访问网络或外部模型。

按照分配顺序处理，每份 packet 先读完整 document，再解释 focus_blocks。一个 block 可以含多个动作，支持证据可跨段。每份记录确定后再读下一份；不要为了让相邻材料一致而回改先前判断。相同文章会重复出现，不要据此推测分组或参照其他版本补全当前输入。只解释当前 packet。

八个字段：

1. `operation`：纠正、范围收窄、解释、推断、评价性重构、回顾、议程设置等，可多选并解释。
2. `question_under_discussion`：`text` 为中性问题；`provenance` 为 `explicit`、`analyst_reconstruction` 或 `unknown`。
3. `prior_or_foil`：原文先前或被否定说法；`text` 可为 null；`status` 描述其来源；`reader_belief_evidence` 只填原文能证明的实际读者信念，否则 null。没有 A 是合法情况。
4. `asserted_or_promised_content`：精确改述肯定主张、条件、价值重点或组织承诺，保留数量、时间、范围、否定、情态和归属。
5. `relation`：关系类型和说明，区分备选、可兼容的不同维度、优先级、限定、因果、手段目的、重述、普通解释或未定。不要把修辞对比自动当作逻辑互斥。
6. `grounds_and_warrant`：`evidence_spans` 保存原文支持；`text` 区分原文明说的连接、合理但未明说的连接和未知项。文章内部支持不等于事实核验。
7. `information_update`：具体化、限定、组织、回顾、优先级、外推或贡献不明；有用回顾可以不增加新事实。
8. `stance_and_presentation`：描述纠正、确定性、权威、引导、排比等可观察表现，不揣测动机。

另记录 `focal_spans`（所识别核心动作的精确片段，允许多个）、`support_assessment`、`preserved_usefulness`、`uncertainties`。需要引用时统一用 `{"block_id":"b006","quote":"精确的连续原文"}`，标题使用 `title`。引文不得加省略号、改标点或写改述；改述应置于说明字段。不同合理分段可记录为不确定性，不必追求唯一答案。

输出 UTF-8 JSON：

```json
{
  "session_id": "分配文件中的值",
  "annotator": {
    "agent_task": "当前任务名",
    "runtime": "Codex subagent",
    "model": "填实际可知的模型标识；不确定就写 unknown",
    "prior_labels_seen": false,
    "other_annotations_seen": false,
    "read_scope": "assignment, instructions, assigned packets only",
    "human_annotation": false
  },
  "records": [
    {
      "packet_id": "分配的 packet id",
      "full_context_read": true,
      "focal_spans": [{"block_id":"title","quote":"逐字引用"}],
      "operation": ["议程设置"],
      "question_under_discussion": {"text":"问题", "provenance":"analyst_reconstruction"},
      "prior_or_foil": {"text":null, "status":"未提出", "reader_belief_evidence":null},
      "asserted_or_promised_content": "主张与限定",
      "relation": {"type":"关系类型", "text":"解释"},
      "grounds_and_warrant": {"evidence_spans":[], "text":"支持与未知项"},
      "information_update": "信息作用",
      "stance_and_presentation": "可观察的呈现",
      "support_assessment": "支持状态，避免把未核实写成错误",
      "preserved_usefulness": "应保留的内容或用途",
      "uncertainties": ["解释或分段歧义"]
    }
  ]
}
```

示例结构不是该实验任何材料的答案。每条记录使用简洁中文，八字段合计约 400–700 汉字即可。保存到负责人指定的唯一输出文件，使用独占创建，保留首次回答。不得替别人写记录或互看结果。如发现任务隔离被破坏，在身份字段如实记录并告知负责人。
