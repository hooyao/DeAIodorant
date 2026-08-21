"""Measure typed evidence for explicit Chinese discourse-relation claims."""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Any

from .syntax import DependencyToken

SCHEMA_VERSION = "deaiodorant-discourse-relations-0.1"
CONTENT_POS = frozenset({"ADJ", "ADV", "NOUN", "PROPN", "VERB"})
ENTITY_POS = frozenset({"NOUN", "PRON", "PROPN"})
PREDICATE_POS = frozenset({"ADJ", "NOUN", "VERB"})
ROLE_RELATIONS = frozenset({"iobj", "nsubj", "obj", "obl"})
ABSTRACT_SHELLS = frozenset(
    {
        "问题",
        "体系",
        "链路",
        "逻辑",
        "判断",
        "层面",
        "维度",
        "能力",
        "方式",
        "模式",
        "价值",
        "意义",
        "不确定性",
        "底层",
        "框架",
        "方向",
        "秩序",
        "边界",
        "核心",
        "关键",
    }
)
GENERIC_PREDICATES = frozenset(
    {
        "是",
        "有",
        "做",
        "进行",
        "处理",
        "指向",
        "意味着",
        "围绕",
        "成为",
        "涉及",
        "包括",
        "需要",
        "能够",
        "可以",
        "让",
        "使",
    }
)
NEGATION_TERMS = frozenset(
    {"不", "不是", "并非", "没有", "没", "不能", "不会", "未", "无需", "别"}
)
MODALITY_TERMS = frozenset(
    {"可能", "或许", "大概", "预计", "必须", "应该", "需要", "可以", "能够", "很难"}
)
CAUSAL_PREDICATES = frozenset(
    {"导致", "造成", "引发", "促使", "带来", "推动", "依赖", "源于", "来自"}
)
COMPARATIVE_TERMS = frozenset(
    {"更", "最", "高于", "低于", "超过", "不足", "相比", "不同", "相同", "一致"}
)
ANTONYM_PAIRS = frozenset(
    {
        frozenset({"增加", "减少"}),
        frozenset({"提高", "降低"}),
        frozenset({"上升", "下降"}),
        frozenset({"允许", "禁止"}),
        frozenset({"接受", "拒绝"}),
        frozenset({"支持", "反对"}),
        frozenset({"成功", "失败"}),
        frozenset({"进入", "退出"}),
        frozenset({"开放", "封闭"}),
        frozenset({"保留", "删除"}),
        frozenset({"直接", "间接"}),
        frozenset({"自动", "人工"}),
        frozenset({"相同", "不同"}),
        frozenset({"一致", "冲突"}),
        frozenset({"有", "无"}),
    }
)
REFERENTIAL_TERMS = frozenset({"这", "这些", "这种", "这一", "它", "其"})


@dataclass(frozen=True)
class MarkerSpec:
    marker: str
    claimed_type: str
    strength: str


MARKER_SPECS = tuple(
    sorted(
        (
            MarkerSpec("更准确地说", "clarification", "strong"),
            MarkerSpec("值得注意的是", "emphasis", "strong"),
            MarkerSpec("换句话说", "clarification", "strong"),
            MarkerSpec("也就是说", "clarification", "strong"),
            MarkerSpec("正因如此", "causal", "strong"),
            MarkerSpec("关键在于", "emphasis", "strong"),
            MarkerSpec("问题在于", "emphasis", "strong"),
            MarkerSpec("简单来说", "clarification", "strong"),
            MarkerSpec("这意味着", "inference", "strong"),
            MarkerSpec("本质上", "emphasis", "strong"),
            MarkerSpec("事实上", "emphasis", "medium"),
            MarkerSpec("相反", "contrast", "strong"),
            MarkerSpec("然而", "contrast", "medium"),
            MarkerSpec("但是", "contrast", "medium"),
            MarkerSpec("不过", "contrast", "medium"),
            MarkerSpec("反而", "contrast", "strong"),
            MarkerSpec("因此", "causal", "strong"),
            MarkerSpec("所以", "causal", "medium"),
            MarkerSpec("因而", "causal", "strong"),
            MarkerSpec("由此", "causal", "medium"),
            MarkerSpec("正是", "emphasis", "strong"),
            MarkerSpec("真正", "emphasis", "medium"),
            MarkerSpec("但", "contrast", "weak"),
        ),
        key=lambda item: (-len(item.marker), item.marker),
    )
)
PAIRED_CONTRAST_RE = re.compile(
    r"(?P<prefix>不是|并非|不只是|不仅是|不再是)"
    r"(?P<left>.{1,80}?)"
    r"(?P<connector>而是)"
    r"(?P<right>[^。！？!?]+)"
)


def _lemma(token: DependencyToken) -> str:
    return (token.lemma if token.lemma != "_" else token.form).casefold()


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _token_spans(sentence: list[DependencyToken]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    cursor = 0
    for token in sentence:
        end = cursor + len(token.form)
        spans.append((cursor, end))
        cursor = end
    return spans


def _tokens_inside(
    sentence: list[DependencyToken],
    spans: list[tuple[int, int]],
    start: int,
    end: int,
) -> list[DependencyToken]:
    return [
        token
        for token, (token_start, token_end) in zip(sentence, spans, strict=True)
        if token_start >= start and token_end <= end
    ]


def _argument_view(tokens: list[DependencyToken]) -> dict[str, Any]:
    content = {_lemma(token) for token in tokens if token.upos in CONTENT_POS}
    entities = {_lemma(token) for token in tokens if token.upos in ENTITY_POS}
    predicates = {
        _lemma(token)
        for token in tokens
        if token.upos == "VERB" or (token.head == 0 and token.upos in PREDICATE_POS)
    }
    roles: dict[str, set[str]] = {
        "iobj": set(),
        "nsubj": set(),
        "obj": set(),
        "obl": set(),
    }
    for token in tokens:
        relation = token.deprel.split(":", 1)[0]
        if relation in ROLE_RELATIONS:
            roles[relation].add(_lemma(token))
    negation_count = sum(
        token.form in NEGATION_TERMS or _lemma(token) in NEGATION_TERMS
        for token in tokens
    )
    modality = {token.form for token in tokens if token.form in MODALITY_TERMS}
    numbers = {token.form for token in tokens if token.upos == "NUM"}
    abstract_shells = content & ABSTRACT_SHELLS
    concrete_content = {
        item
        for item in content
        if item not in ABSTRACT_SHELLS and item not in GENERIC_PREDICATES
    }
    proposition_present = bool(predicates) and bool(
        entities or any(roles.values()) or concrete_content
    )
    return {
        "abstract_shells": abstract_shells,
        "concrete_content": concrete_content,
        "content": content,
        "entities": entities,
        "modality": modality,
        "negation_count": negation_count,
        "numbers": numbers,
        "predicates": predicates,
        "proposition_present": proposition_present,
        "roles": roles,
        "text": "".join(token.form for token in tokens),
    }


def _antonym_count(left: set[str], right: set[str]) -> int:
    return sum(
        any(
            left_item != right_item
            for left_item in pair & left
            for right_item in pair & right
        )
        for pair in ANTONYM_PAIRS
    )


def _shared_role_count(left: dict[str, set[str]], right: dict[str, set[str]]) -> int:
    return sum(len(left[role] & right[role]) for role in sorted(ROLE_RELATIONS))


def _evidence(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    paired_frame: bool,
) -> dict[str, float | int | bool]:
    shared_entities = left["entities"] & right["entities"]
    shared_content = left["content"] & right["content"]
    shared_predicates = left["predicates"] & right["predicates"]
    shared_specific_predicates = shared_predicates - GENERIC_PREDICATES
    shared_role_count = _shared_role_count(left["roles"], right["roles"])
    antonym_count = _antonym_count(left["content"], right["content"])
    polarity_flip = bool(
        (left["negation_count"] > 0) != (right["negation_count"] > 0)
        and shared_specific_predicates
    )
    new_concrete = right["concrete_content"] - left["concrete_content"]
    new_entities = right["entities"] - left["entities"]
    new_predicates = right["predicates"] - left["predicates"]
    payload_gain_count = len(new_concrete | new_entities | new_predicates) + len(
        right["numbers"] - left["numbers"]
    )
    abstract_only_right = bool(right["content"]) and not bool(
        right["concrete_content"] or right["numbers"]
    )
    role_overlap = shared_role_count / max(
        1,
        sum(len(values) for values in left["roles"].values())
        + sum(len(values) for values in right["roles"].values()),
    )
    anchor_score = (
        0.5 * _jaccard(left["entities"], right["entities"])
        + 0.3 * _jaccard(left["content"], right["content"])
        + 0.2 * role_overlap
    )
    return {
        "abstract_only_right": abstract_only_right,
        "anchor_score": anchor_score,
        "antonym_count": antonym_count,
        "content_jaccard": _jaccard(left["content"], right["content"]),
        "entity_jaccard": _jaccard(left["entities"], right["entities"]),
        "left_proposition_present": left["proposition_present"],
        "paired_frame": paired_frame,
        "payload_gain_count": payload_gain_count,
        "polarity_flip": polarity_flip,
        "right_abstract_shell_count": len(right["abstract_shells"]),
        "right_concrete_content_count": len(right["concrete_content"]),
        "right_proposition_present": right["proposition_present"],
        "shared_content_count": len(shared_content),
        "shared_entity_count": len(shared_entities),
        "shared_predicate_count": len(shared_predicates),
        "shared_specific_predicate_count": len(shared_specific_predicates),
        "shared_role_count": shared_role_count,
    }


def _decision(
    claimed_type: str,
    marker_strength: str,
    evidence: dict[str, float | int | bool],
    left: dict[str, Any],
    right: dict[str, Any],
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    propositions_present = bool(
        evidence["left_proposition_present"] and evidence["right_proposition_present"]
    )
    shared_anchor = bool(
        evidence["shared_entity_count"]
        or evidence["shared_predicate_count"]
        or evidence["shared_role_count"]
        or float(evidence["content_jaccard"]) >= 0.2
    )
    payload_gain = int(evidence["payload_gain_count"])

    if not propositions_present:
        return "indeterminate", ("ARGUMENT_PROPOSITION_INCOMPLETE",)

    if claimed_type == "contrast":
        if evidence["polarity_flip"]:
            reasons.append("POLARITY_FLIP_ON_SHARED_ANCHOR")
        if int(evidence["antonym_count"]) > 0:
            reasons.append("FROZEN_ANTONYM_PAIR")
        if any(
            term in left["content"] | right["content"] for term in COMPARATIVE_TERMS
        ):
            reasons.append("EXPLICIT_COMPARATIVE_DIMENSION")
        if reasons:
            return "supported", tuple(reasons)
        if shared_anchor and payload_gain > 0:
            return "type_mismatch", ("ELABORATION_EVIDENCE_WITHOUT_CONTRAST",)
        if bool(evidence["abstract_only_right"]) and marker_strength == "strong":
            return "unsupported", ("STRONG_CONTRAST_WITH_ABSTRACT_PAYLOAD",)
        return "indeterminate", ("NO_HIGH_CONFIDENCE_CONTRAST_EVIDENCE",)

    if claimed_type == "causal":
        causal_predicate = bool(
            (left["predicates"] | right["predicates"]) & CAUSAL_PREDICATES
        )
        if shared_anchor and causal_predicate:
            return "supported", ("SHARED_ANCHOR_WITH_CAUSAL_PREDICATE",)
        if shared_anchor and payload_gain > 0:
            return "indeterminate", ("CONNECTED_CLAIMS_WITHOUT_CAUSAL_MECHANISM",)
        if (
            marker_strength == "strong"
            and not shared_anchor
            and bool(evidence["abstract_only_right"])
        ):
            return "unsupported", ("STRONG_CAUSAL_MARKER_WITHOUT_LOCAL_BRIDGE",)
        return "indeterminate", ("NO_HIGH_CONFIDENCE_CAUSAL_EVIDENCE",)

    if claimed_type == "inference":
        if shared_anchor and payload_gain > 0:
            return "supported", ("SHARED_ANCHOR_WITH_NEW_CONSEQUENCE_PAYLOAD",)
        if float(evidence["content_jaccard"]) >= 0.6 and payload_gain == 0:
            return "redundant", ("INFERENCE_RESTATES_PRIOR_CONTENT",)
        if not shared_anchor and bool(evidence["abstract_only_right"]):
            return "unsupported", ("INFERENCE_WITHOUT_LOCAL_BRIDGE",)
        return "indeterminate", ("NO_HIGH_CONFIDENCE_INFERENCE_EVIDENCE",)

    if claimed_type == "clarification":
        if shared_anchor and payload_gain > 0:
            return "supported", ("SHARED_ANCHOR_WITH_SPECIFICITY_GAIN",)
        if float(evidence["content_jaccard"]) >= 0.6 and payload_gain == 0:
            return "redundant", ("CLARIFICATION_WITHOUT_NEW_PAYLOAD",)
        if not shared_anchor:
            return "unsupported", ("CLARIFICATION_WITHOUT_SHARED_ANCHOR",)
        return "indeterminate", ("NO_HIGH_CONFIDENCE_CLARIFICATION_EVIDENCE",)

    if claimed_type == "emphasis":
        if bool(evidence["abstract_only_right"]):
            return "unsupported", ("EMPHASIS_HAS_ONLY_ABSTRACT_PAYLOAD",)
        if float(evidence["content_jaccard"]) >= 0.6 and payload_gain == 0:
            return "redundant", ("EMPHASIS_RESTATES_PRIOR_CONTENT",)
        if payload_gain > 0 and int(evidence["right_concrete_content_count"]) > 0:
            return "supported", ("EMPHASIS_HAS_IMMEDIATE_CONCRETE_PAYLOAD",)
        return "indeterminate", ("NO_HIGH_CONFIDENCE_EMPHASIS_EVIDENCE",)

    raise ValueError(f"Unsupported claimed relation type: {claimed_type}")


def _make_instance(
    *,
    instance_index: int,
    marker: str,
    claimed_type: str,
    marker_strength: str,
    left_tokens: list[DependencyToken],
    right_tokens: list[DependencyToken],
    left_sentence_index: int,
    right_sentence_index: int,
    paired_frame: bool,
) -> dict[str, Any]:
    left = _argument_view(left_tokens)
    right = _argument_view(right_tokens)
    evidence = _evidence(left, right, paired_frame=paired_frame)
    decision, reason_codes = _decision(
        claimed_type,
        marker_strength,
        evidence,
        left,
        right,
    )
    return {
        "arg1_sentence_index": left_sentence_index,
        "arg1_text": left["text"],
        "arg2_sentence_index": right_sentence_index,
        "arg2_text": right["text"],
        "claimed_type": claimed_type,
        "decision": decision,
        "evidence": evidence,
        "instance_id": f"r{instance_index}",
        "marker": marker,
        "marker_strength": marker_strength,
        "reason_codes": list(reason_codes),
    }


def extract_relation_instances(
    sentences: list[list[DependencyToken]],
) -> list[dict[str, Any]]:
    """Extract relation claims and classify their typed local evidence."""

    instances: list[dict[str, Any]] = []
    sentence_texts = [
        "".join(token.form for token in sentence) for sentence in sentences
    ]
    for sentence_index, (sentence, sentence_text) in enumerate(
        zip(sentences, sentence_texts, strict=True)
    ):
        spans = _token_spans(sentence)
        occupied: list[tuple[int, int]] = []
        for match in PAIRED_CONTRAST_RE.finditer(sentence_text):
            left_tokens = _tokens_inside(
                sentence,
                spans,
                match.start("left"),
                match.end("left"),
            )
            right_tokens = _tokens_inside(
                sentence,
                spans,
                match.start("right"),
                match.end("right"),
            )
            if left_tokens and right_tokens:
                instances.append(
                    _make_instance(
                        instance_index=len(instances),
                        marker=f"{match.group('prefix')}…{match.group('connector')}",
                        claimed_type="contrast",
                        marker_strength="strong",
                        left_tokens=left_tokens,
                        right_tokens=right_tokens,
                        left_sentence_index=sentence_index,
                        right_sentence_index=sentence_index,
                        paired_frame=True,
                    )
                )
                occupied.append((match.start(), match.end()))

        marker_spans: list[tuple[int, int]] = []
        for spec in MARKER_SPECS:
            search_start = 0
            while True:
                marker_start = sentence_text.find(spec.marker, search_start)
                if marker_start < 0:
                    break
                marker_end = marker_start + len(spec.marker)
                search_start = marker_end
                if any(
                    marker_start < occupied_end and marker_end > occupied_start
                    for occupied_start, occupied_end in occupied
                ):
                    continue
                if any(
                    marker_start < used_end and marker_end > used_start
                    for used_start, used_end in marker_spans
                ):
                    continue
                if (
                    spec.marker == "但"
                    and marker_start > 0
                    and sentence_text[marker_start - 1] in {"不", "非"}
                ):
                    continue
                left_tokens = _tokens_inside(sentence, spans, 0, marker_start)
                right_tokens = _tokens_inside(
                    sentence, spans, marker_end, len(sentence_text)
                )
                left_sentence_index = sentence_index
                if len(_argument_view(left_tokens)["content"]) < 2:
                    if sentence_index == 0:
                        continue
                    left_tokens = sentences[sentence_index - 1]
                    left_sentence_index = sentence_index - 1
                if len(_argument_view(right_tokens)["content"]) < 1:
                    continue
                instances.append(
                    _make_instance(
                        instance_index=len(instances),
                        marker=spec.marker,
                        claimed_type=spec.claimed_type,
                        marker_strength=spec.strength,
                        left_tokens=left_tokens,
                        right_tokens=right_tokens,
                        left_sentence_index=left_sentence_index,
                        right_sentence_index=sentence_index,
                        paired_frame=False,
                    )
                )
                marker_spans.append((marker_start, marker_end))
    return instances


def relation_support_features(
    instances: list[dict[str, Any]],
    *,
    sentence_count: int,
) -> dict[str, float | int]:
    """Aggregate relation-instance evidence without hiding abstentions."""

    relation_count = len(instances)
    decisions = [item["decision"] for item in instances]
    determinate_count = sum(decision != "indeterminate" for decision in decisions)
    problem_decisions = {"redundant", "type_mismatch", "unsupported"}
    problem_count = sum(decision in problem_decisions for decision in decisions)

    def ratio(count: int, denominator: int = relation_count) -> float:
        return count / denominator if denominator else 0.0

    features: dict[str, float | int] = {
        "relation_support_determinate_ratio": ratio(determinate_count),
        "relation_support_indeterminate_ratio": ratio(decisions.count("indeterminate")),
        "relation_support_instance_count": relation_count,
        "relation_support_instances_per_100_sentences": (
            relation_count / sentence_count * 100 if sentence_count else 0.0
        ),
        "relation_support_mean_anchor_score": (
            statistics.fmean(
                float(item["evidence"]["anchor_score"]) for item in instances
            )
            if instances
            else 0.0
        ),
        "relation_support_mean_payload_gain": (
            statistics.fmean(
                int(item["evidence"]["payload_gain_count"]) for item in instances
            )
            if instances
            else 0.0
        ),
        "relation_support_problem_count": problem_count,
        "relation_support_problem_per_100_sentences": (
            problem_count / sentence_count * 100 if sentence_count else 0.0
        ),
        "relation_support_problem_ratio": ratio(problem_count),
        "relation_support_problem_ratio_determinate": ratio(
            problem_count, determinate_count
        ),
        "relation_support_redundant_ratio": ratio(decisions.count("redundant")),
        "relation_support_supported_ratio": ratio(decisions.count("supported")),
        "relation_support_type_mismatch_ratio": ratio(decisions.count("type_mismatch")),
        "relation_support_unsupported_ratio": ratio(decisions.count("unsupported")),
    }
    for claimed_type in (
        "causal",
        "clarification",
        "contrast",
        "emphasis",
        "inference",
    ):
        typed = [item for item in instances if item["claimed_type"] == claimed_type]
        typed_problem_count = sum(
            item["decision"] in problem_decisions for item in typed
        )
        features[f"relation_support_{claimed_type}_count"] = len(typed)
        features[f"relation_support_{claimed_type}_per_100_sentences"] = (
            len(typed) / sentence_count * 100 if sentence_count else 0.0
        )
        features[f"relation_support_{claimed_type}_problem_ratio"] = (
            typed_problem_count / len(typed) if typed else 0.0
        )
    return features


def analyze_relation_support(
    sentences: list[list[DependencyToken]],
) -> tuple[list[dict[str, Any]], dict[str, float | int]]:
    """Return inspectable relation instances and aggregate numeric features."""

    instances = extract_relation_instances(sentences)
    return instances, relation_support_features(
        instances,
        sentence_count=len(sentences),
    )
