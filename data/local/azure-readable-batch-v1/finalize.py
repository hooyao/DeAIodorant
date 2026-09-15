"""Root完成有限内容与表达收尾；首次模型输出和JSON修订均不改。"""
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[2]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

translation = [
    ("在微服务和高度分布式系统中，应用、基础设施、版本和配置等众多组件相互作用", "微服务和高度分布式系统由应用程序、基础设施、版本和配置等许多相互关联的部分组成。运维人员很难随时掌握生产、QA、开发和预生产环境的实际状态，这会增加排查故障的难度。本文介绍监控和可观察性各自的用途，以及变更感知（Change Intelligence）如何补充变更上下文，帮助查找问题原因。", "补回QA和预生产环境；直接交代问题与本文用途。"),
    ("监控和可观察性是现代系统运维的基础。你经常会听到有人说", "收集指标、日志和追踪数据，只是获得可观察性的前提。要让数据真正可用，还需要结合业务需求和应用程序的工作方式来理解它们。", "保留遥测仅为前提的关系，减少代读者提出误解再纠正的表达。"),
    ("作者观察到，运维人员实际上利用可观察性工具", "作者观察到，运维人员会用可观察性工具找到问题根因，再把排障经验纳入监控规则，用来发现以后重复出现的问题。配合文档和运行手册，这两类工具可以共同提高系统可靠性。", "保留作者观察归属和先后过程，去掉复制回来的创造奇迹等渲染。"),
    ("然而，即使拥有完善的监控和可观察性", "监控和可观察性仍可能不足以说明故障发生前系统做过哪些变更。变更感知补充了这部分上下文。", "将重复拼图比喻改为具体缺少的信息。"),
    ("在转向微服务之前，作者曾在单体环境中工作", "作者在转向微服务之前，曾在单体系统环境中工作，因此了解这两类环境的差异。他认为，监控和可观察性在单体系统中很有帮助，在微服务系统中则必不可少。微服务数量多、职责不同，各个服务通常还分成更小的单元，同时执行多项操作，彼此需要频繁交换信息，排查故障也更复杂。", "保留个人经历、必要性和并发信息，整理回补后难读的句子。"),
    ("当收到警报（如页面或 Slack 消息）提示业务异常时", "警报可能来自页面或Slack消息。在大型分布式系统中，一项业务异常可能涉及多个服务。监控和可观察性可以帮助工程师从数百个应用程序或服务器中定位故障服务，之后再追查具体发生了什么。这个过程需要以下条件，而实际工作中未必都具备：", "明确先定位后追查的步骤，保留现实条件未必满足。"),
    ("作为一名 DevOps 工程师（现任 Komodor，曾在 Rookout）", "作者现在在Komodor任DevOps工程师，以前在Rookout工作。他曾和团队处理过一次关键服务大量报错的事件，系统只提示“无效值”。他们搜索系统和近期变更，花了一整天才把问题追溯到七个月前实施的一项变更。排查发现，数据库的列使用整数类型，团队尝试写入的数字更大，需要大整数类型才能容纳。原文没有进一步说明七个月前具体做了哪项修改。缺少帮助团队关联错误与历史变更的工具时，简单的数据类型问题也可能耗费整个有经验的团队一天时间。", "补回写入动作的主语，保留整数与大整数机制，不编造七个月前的具体变更。"),
    ("变更感知通常基于发布记录、审计日志、版本差异", "变更感知可依据发布说明、审计日志、版本差异和变更者的信息，把变更与相连的各个服务对应起来，寻找最可能出问题的位置。这样能缩小排查范围，帮助更快恢复服务。", "保留信息来源和最可能的定位范围，减少干草堆对比比喻。"),
    ("以 Komodor 的变更感知解决方案为例，上面的截图", "原文展示了Komodor在K8s环境中的一个例子。时间线上先有新版本部署完成，之后记录到可用副本不足的健康状态变化，随后触发DataDog告警。这些事件说明部署值得进一步检查，但还不能据此确定原因：可能是部署期间没有保证可用性，也可能是代码修改引入了错误或重大变更。作者认为，查看这次部署的细节，能够在几秒钟内进一步查明告警原因。", "撤去刚刚和紧接着的相邻时间暗示；保留顺序、两项可能原因及作者的几秒钟判断；不指向本稿不存在的截图。"),
    ("随着系统规模和复杂度不断提升，让组织走到今天的工具", "过去，人们先使用日志，随后引入跟踪和指标，再把这些数据汇集到仪表板中。随着数据、警报和信息不断增加，工具也越加越多。系统规模继续扩大时，现有工具将来可能无法满足需求。变更感知为监控和可观察性补充变更上下文，帮助工程师理解这些数据。", "补回工具演进叙述，保留未来可能不足，减少生硬的堆栈动力说法。"),
    ("通过变更感知，团队能够更快恢复服务，维护严格的 SLA", "作者认为，在未来更复杂的系统中，这项能力有助于更快恢复服务、满足严格的SLA，并减少可能持续很久的停机及其成本。", "保留作者的未来价值判断与停机目标，去掉重复的关键工具评价。"),
]

for case_id in ["translation", "short_news", "marketing"]:
    directory = RUN / "cases" / case_id
    original = (directory / "candidate-v2.md").read_bytes().decode("utf-8")
    edits = []
    if case_id == "translation":
        for prefix, new, reason in translation:
            matches = [p for p in original.split("\n\n") if p.startswith(prefix)]
            assert len(matches) == 1
            edits.append({"old": matches[0], "new": new, "reason": reason})
    elif case_id == "short_news":
        old = "届时可将 Seedance 2.0 集成到自有工作流中，"
        edits.append({"old": old, "new": old[:-1] + "。", "reason": "只把删除后悬空的句末逗号改为句号。"})
    else:
        edits = [
            {"old": "以上6款是我认为可以提升生活品质的2022年新品扫拖一体机器人，希望对各位选购能有所帮助。", "new": "以上6款是我认为可以提升生活品质的2022年新品扫拖机器人，希望对各位选购能有所帮助。", "reason": "去掉不适用于需手动更换模块的J2的统称，与正文明确限制一致。"},
            {"old": "选购时还可结合家庭面积、地面类型、是否有宠物、对自动化程度的需求以及预算等因素综合考虑。", "new": "", "reason": "删除未在原文给出的新增概括建议，避免混入编辑者结论。"},
        ]
    candidate = original
    for edit in edits:
        assert candidate.count(edit["old"]) == 1
        candidate = candidate.replace(edit["old"], edit["new"], 1)
    path = directory / "candidate-v3.md"
    if path.exists() or (directory / "root-edits-v3.json").exists():
        raise SystemExit("已存在Root收尾版本，不覆盖。")
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(candidate)
    code = json.loads((directory / "protected-code.json").read_text(encoding="utf-8"))
    assert all(p["text"] in candidate for p in code)
    save(directory / "root-edits-v3.json", {"editor": "root_native_astra", "base_sha256": digest(directory / "candidate-v2.md"),
         "candidate_sha256": digest(path), "edits": edits, "characters": len(candidate),
         "scope": "按复核完成内容收尾；translation还整理回补后的复制原句和比喻，明确与Azure纯输出分开。",
         "human_feedback": None, "network_calls": 0, "training_eligible": False})
    print(json.dumps({"case": case_id, "characters": len(candidate), "root_edits": len(edits)}, ensure_ascii=False))
