"""Construct a deterministic heterogeneous graph for Chinese discourse passages."""

from __future__ import annotations

import re
import statistics
from collections import defaultdict, deque
from typing import Any

from .syntax import DependencyToken


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
CONTENT_POS = frozenset({"ADJ", "ADV", "NOUN", "PROPN", "VERB"})
ENTITY_POS = frozenset({"NOUN", "PROPN"})
ARGUMENT_RELATIONS = frozenset({"csubj", "iobj", "nsubj", "obj", "obl"})
PREDICATE_POS = frozenset({"ADJ", "NOUN", "VERB"})
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
DISCOURSE_MARKERS = {
    "causal": ("因此", "所以", "因而", "由此", "正因如此"),
    "contrast": ("但是", "但", "然而", "不过", "反而"),
    "clarification": ("更准确地说", "换句话说", "也就是说"),
    "enumeration": ("首先", "其次", "再次", "最后", "第一", "第二", "第三"),
}
SENTENCE_RE = re.compile(r"[^。！？!?]+[。！？!?]?")
CONTRAST_FRAME_RE = re.compile(
    r"(?:不是|并非|不只是|不仅是|不再是).{0,80}?而是"
)
EMPHATIC_FRAMES = (
    "正是",
    "关键在于",
    "问题在于",
    "这意味着",
    "值得注意的是",
    "真正",
    "本质上",
)
META_FRAMES = (
    "更准确地说",
    "换句话说",
    "事实上",
    "简单来说",
    "归根结底",
    "指向",
)
REFERENTIAL_OPENINGS = (
    "这",
    "这些",
    "这种",
    "这一",
    "它",
    "其",
    "因此",
    "但是",
    "但",
    "而",
)


def _lemma(token: DependencyToken) -> str:
    return (token.lemma if token.lemma != "_" else token.form).casefold()


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _edge_type(sentence_text: str) -> str:
    stripped = sentence_text.lstrip("，,；;：: ")
    for edge_type, markers in DISCOURSE_MARKERS.items():
        if stripped.startswith(markers):
            return edge_type
    return "sequence"


def rhetorical_hypothesis_features(text: str) -> dict[str, float]:
    """Extract frozen rhetorical proxies used by the pilot graph analysis."""

    cjk_count = len(CJK_RE.findall(text))
    sentences = [item.strip() for item in SENTENCE_RE.findall(text) if item.strip()]
    sentence_count = len(sentences)
    contrast_count = sum(
        len(CONTRAST_FRAME_RE.findall(sentence)) for sentence in sentences
    )
    referential_openings = sum(
        sentence.startswith(REFERENTIAL_OPENINGS) for sentence in sentences
    )

    def count_terms(terms: tuple[str, ...] | frozenset[str]) -> int:
        return sum(text.count(term) for term in terms)

    return {
        "hypothesis_abstract_shells_per_1k_cjk": (
            count_terms(ABSTRACT_SHELLS) / cjk_count * 1000 if cjk_count else 0.0
        ),
        "hypothesis_complete_contrast_frames_per_1k_sentences": (
            contrast_count / sentence_count * 1000 if sentence_count else 0.0
        ),
        "hypothesis_emphatic_frames_per_1k_cjk": (
            count_terms(EMPHATIC_FRAMES) / cjk_count * 1000 if cjk_count else 0.0
        ),
        "hypothesis_meta_frames_per_1k_cjk": (
            count_terms(META_FRAMES) / cjk_count * 1000 if cjk_count else 0.0
        ),
        "hypothesis_referential_sentence_opening_ratio": (
            referential_openings / sentence_count if sentence_count else 0.0
        ),
    }


def _predicate_tokens(sentence: list[DependencyToken]) -> list[DependencyToken]:
    predicates = [token for token in sentence if token.upos == "VERB"]
    root = next(token for token in sentence if token.head == 0)
    if not predicates and root.upos in PREDICATE_POS:
        predicates.append(root)
    return predicates


def _connected_components(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[set[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        adjacency[node["id"]]
    for edge in edges:
        if edge["type"] == "discourse_bridge":
            continue
        adjacency[edge["source"]].add(edge["target"])
        adjacency[edge["target"]].add(edge["source"])
    components: list[set[str]] = []
    unseen = set(adjacency)
    while unseen:
        start = min(unseen)
        component = {start}
        queue = deque([start])
        unseen.remove(start)
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def build_discourse_graph(
    text: str,
    sentences: list[list[DependencyToken]],
) -> tuple[dict[str, Any], dict[str, float | int]]:
    """Build the graph and return graph-derived quantitative features."""

    nodes: list[dict[str, Any]] = []
    created_node_ids: set[str] = set()
    edges: list[dict[str, Any]] = []
    entity_node_ids: dict[str, str] = {}
    sentence_entities: list[set[str]] = []
    sentence_content: list[set[str]] = []
    sentence_predicates: list[set[str]] = []
    sentence_texts: list[str] = []
    proposition_signatures: list[tuple[str, tuple[str, ...]]] = []
    proposition_sentence_indices: list[int] = []
    proposition_argument_counts: list[int] = []
    abstract_count = 0
    ungrounded_abstract_count = 0

    for sentence_index, sentence in enumerate(sentences):
        sentence_id = f"s{sentence_index}"
        sentence_text = "".join(token.form for token in sentence)
        sentence_texts.append(sentence_text)
        nodes.append(
            {
                "id": sentence_id,
                "kind": "sentence",
                "sentence_index": sentence_index,
            }
        )
        created_node_ids.add(sentence_id)
        entities = {_lemma(token) for token in sentence if token.upos in ENTITY_POS}
        content = {_lemma(token) for token in sentence if token.upos in CONTENT_POS}
        predicates = _predicate_tokens(sentence)
        predicate_lemmas = {_lemma(token) for token in predicates}
        sentence_entities.append(entities)
        sentence_content.append(content)
        sentence_predicates.append(predicate_lemmas)

        concrete_entities = entities - ABSTRACT_SHELLS
        concrete_predicates = predicate_lemmas - GENERIC_PREDICATES
        has_grounding = bool(concrete_entities and concrete_predicates) or any(
            token.upos == "NUM" for token in sentence
        )
        sentence_shells = [
            token for token in sentence if _lemma(token) in ABSTRACT_SHELLS
        ]
        abstract_count += len(sentence_shells)
        if not has_grounding:
            ungrounded_abstract_count += len(sentence_shells)

        for entity in sorted(entities):
            entity_id = entity_node_ids.setdefault(entity, f"e{len(entity_node_ids)}")
            if entity_id not in created_node_ids:
                nodes.append(
                    {
                        "id": entity_id,
                        "kind": "abstract_entity" if entity in ABSTRACT_SHELLS else "entity",
                        "label": entity,
                    }
                )
                created_node_ids.add(entity_id)
            edges.append(
                {
                    "source": sentence_id,
                    "target": entity_id,
                    "type": "mentions",
                }
            )

        by_head: dict[int, list[DependencyToken]] = defaultdict(list)
        for token in sentence:
            by_head[token.head].append(token)
        for proposition_index, predicate in enumerate(predicates):
            proposition_id = f"p{sentence_index}_{proposition_index}"
            arguments = [
                child
                for child in by_head[predicate.token_id]
                if child.deprel.split(":", 1)[0] in ARGUMENT_RELATIONS
            ]
            argument_lemmas = tuple(sorted({_lemma(argument) for argument in arguments}))
            signature = (_lemma(predicate), argument_lemmas)
            proposition_signatures.append(signature)
            proposition_sentence_indices.append(sentence_index)
            proposition_argument_counts.append(len(argument_lemmas))
            nodes.append(
                {
                    "id": proposition_id,
                    "kind": "proposition",
                    "predicate": signature[0],
                    "signature": [signature[0], list(signature[1])],
                    "sentence_index": sentence_index,
                }
            )
            created_node_ids.add(proposition_id)
            edges.append(
                {
                    "source": sentence_id,
                    "target": proposition_id,
                    "type": "contains_proposition",
                }
            )
            for argument in arguments:
                entity = _lemma(argument)
                entity_id = entity_node_ids.setdefault(
                    entity, f"e{len(entity_node_ids)}"
                )
                if entity_id not in created_node_ids:
                    nodes.append(
                        {
                            "id": entity_id,
                            "kind": "abstract_entity" if entity in ABSTRACT_SHELLS else "entity",
                            "label": entity,
                        }
                    )
                    created_node_ids.add(entity_id)
                edges.append(
                    {
                        "role": argument.deprel.split(":", 1)[0],
                        "source": proposition_id,
                        "target": entity_id,
                        "type": "argument",
                    }
                )

    bridge_weights: list[float] = []
    zero_bridge_count = 0
    unsupported_explicit_count = 0
    explicit_count = 0
    for index in range(1, len(sentences)):
        entity_overlap = _jaccard(sentence_entities[index - 1], sentence_entities[index])
        content_overlap = _jaccard(sentence_content[index - 1], sentence_content[index])
        predicate_overlap = _jaccard(
            sentence_predicates[index - 1], sentence_predicates[index]
        )
        bridge_weight = (
            0.5 * entity_overlap + 0.3 * content_overlap + 0.2 * predicate_overlap
        )
        bridge_weights.append(bridge_weight)
        if bridge_weight == 0:
            zero_bridge_count += 1
        relation = _edge_type(sentence_texts[index])
        if relation != "sequence":
            explicit_count += 1
            unsupported_explicit_count += bridge_weight == 0
        edges.append(
            {
                "content_jaccard": content_overlap,
                "entity_jaccard": entity_overlap,
                "predicate_jaccard": predicate_overlap,
                "relation": relation,
                "source": f"s{index - 1}",
                "target": f"s{index}",
                "type": "discourse_bridge",
                "weight": bridge_weight,
            }
        )

    restatement_count = 0
    for index, (predicate, arguments) in enumerate(proposition_signatures):
        for previous in range(index - 1, -1, -1):
            if proposition_sentence_indices[index] - proposition_sentence_indices[previous] > 3:
                break
            previous_predicate, previous_arguments = proposition_signatures[previous]
            argument_similarity = _jaccard(set(arguments), set(previous_arguments))
            if predicate == previous_predicate and (
                argument_similarity >= 0.5 or not arguments or not previous_arguments
            ):
                restatement_count += 1
                break

    detour_count = 0
    for index in range(1, len(sentences) - 1):
        left_middle = _jaccard(sentence_content[index - 1], sentence_content[index])
        middle_right = _jaccard(sentence_content[index], sentence_content[index + 1])
        left_right = _jaccard(sentence_content[index - 1], sentence_content[index + 1])
        if left_right > 0 and left_right > 2 * max(left_middle, middle_right):
            detour_count += 1

    semantic_components = _connected_components(nodes, edges)
    sentence_node_ids = {f"s{index}" for index in range(len(sentences))}
    sentences_per_component = [
        len(component & sentence_node_ids) for component in semantic_components
    ]
    isolated_sentence_count = sum(count == 1 for count in sentences_per_component)
    largest_sentence_component = max(sentences_per_component, default=0)
    sentence_count = len(sentences)
    proposition_count = len(proposition_signatures)
    unique_proposition_count = len(set(proposition_signatures))
    cjk_count = len(CJK_RE.findall(text))
    adjacent_count = max(0, sentence_count - 1)
    features: dict[str, float | int] = {
        "graph_abstract_shell_count_per_100_cjk": (
            abstract_count / cjk_count * 100 if cjk_count else 0.0
        ),
        "graph_argumentless_proposition_ratio": (
            sum(count == 0 for count in proposition_argument_counts) / proposition_count
            if proposition_count
            else 0.0
        ),
        "graph_explicit_discourse_edge_count": explicit_count,
        "graph_isolated_sentence_ratio": (
            isolated_sentence_count / sentence_count if sentence_count else 0.0
        ),
        "graph_largest_component_sentence_coverage": (
            largest_sentence_component / sentence_count if sentence_count else 0.0
        ),
        "graph_mainline_detour_ratio": (
            detour_count / max(1, sentence_count - 2) if sentence_count >= 3 else 0.0
        ),
        "graph_mean_adjacent_bridge_weight": (
            statistics.fmean(bridge_weights) if bridge_weights else 0.0
        ),
        "graph_mean_proposition_argument_count": (
            statistics.fmean(proposition_argument_counts)
            if proposition_argument_counts
            else 0.0
        ),
        "graph_proposition_restatement_ratio": (
            restatement_count / proposition_count if proposition_count else 0.0
        ),
        "graph_propositions_per_100_cjk": (
            proposition_count / cjk_count * 100 if cjk_count else 0.0
        ),
        "graph_semantic_components_per_sentence": (
            len(semantic_components) / sentence_count if sentence_count else 0.0
        ),
        "graph_surface_chars_per_unique_proposition": (
            cjk_count / unique_proposition_count if unique_proposition_count else 0.0
        ),
        "graph_ungrounded_abstract_shell_ratio": (
            ungrounded_abstract_count / abstract_count if abstract_count else 0.0
        ),
        "graph_unique_proposition_ratio": (
            unique_proposition_count / proposition_count if proposition_count else 0.0
        ),
        "graph_unsupported_explicit_edge_ratio": (
            unsupported_explicit_count / explicit_count if explicit_count else 0.0
        ),
        "graph_zero_adjacent_bridge_ratio": (
            zero_bridge_count / adjacent_count if adjacent_count else 0.0
        ),
    }
    graph = {
        "edges": edges,
        "nodes": nodes,
        "schema_version": "deaiodorant-discourse-graph-0.1",
    }
    return graph, features
