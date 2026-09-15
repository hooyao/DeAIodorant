"""只读导出 Label Studio 研究状态；不读取账号、token 或存储凭据的值。"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys


WHITELIST = {
    "project": "id title label_config expert_instruction show_instruction model_version data_types is_published created_at updated_at show_skip_button show_collab_predictions sampling overlap_cohort_percentage show_overlap_first control_weights result_count is_draft description color enable_empty_annotation maximum_annotations min_annotations_to_start_training show_annotation_history show_ground_truth_first evaluate_predictions_automatically reveal_preannotations_interactively skip_queue parsed_label_config label_config_hash annotator_evaluation_enabled".split(),
    "task": "id data created_at updated_at is_labeled project_id meta overlap file_upload_id updated_by_id inner_id total_annotations cancelled_annotations total_predictions comment_count last_comment_updated_at unresolved_comment_count precomputed_agreement allow_skip".split(),
    "task_completion": "id result was_cancelled created_at updated_at task_id prediction lead_time result_count completed_by_id ground_truth parent_prediction_id last_action last_created_by_id project_id updated_by_id unique_id draft_created_at import_id bulk_created parent_annotation_id".split(),
    "prediction": "id result score model_version created_at updated_at task_id cluster mislabeling neighbors project_id model_run_id model_id".split(),
    "tasks_annotationdraft": "id result created_at updated_at task_id user_id annotation_id was_postponed lead_time import_id".split(),
    "projects_projectsummary": "project_id created_at all_data_columns common_data_columns created_annotations created_labels created_labels_drafts".split(),
    "data_manager_view": "id data project_id ordering filter_group_id selected_items user_id order".split(),
    "data_manager_filtergroup": "id conjunction".split(),
    "data_manager_filter": "id column type operator value index parent_id".split(),
    "data_manager_filtergroup_filters": "id filtergroup_id filter_id".split(),
    "projects_labelstreamhistory": "id data project_id user_id".split(),
}
JSON_COLUMNS = {
    "project": {"data_types", "control_weights", "parsed_label_config"},
    "task": {"data", "meta"},
    "task_completion": {"result", "prediction"},
    "prediction": {"result", "neighbors"},
    "tasks_annotationdraft": {"result"},
    "projects_projectsummary": {"all_data_columns", "common_data_columns", "created_annotations", "created_labels", "created_labels_drafts"},
    "data_manager_view": {"data", "ordering", "selected_items"},
    "data_manager_filter": {"value"},
    "projects_labelstreamhistory": {"data"},
}
IDENTITY_FIELD = re.compile(r"(^|_)(password|passwd|secret|token|authorization|cookie|session|email|username|first_name|last_name|phone|login|credential|credentials|contact_info|api_key|access_key)(_|$)", re.I)
SECRET_PATTERNS = {
    "api_key_literal": re.compile(r"\bsk-(?:or-v1-)?[A-Za-z0-9_-]{20,}"),
    "bearer_literal": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{16,}", re.I),
    "private_key": re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    "url_userinfo": re.compile(r"https?://[^/\s:]+:[^/\s@]+@"),
    "auth_assignment": re.compile(r"(?:password|api[_-]?key|access[_-]?token|client[_-]?secret|authorization)\s*[=:]\s*[\x22\x27]?[^\s\x22\x27<>]{8,}", re.I),
}
HISTORICAL_FILE = "project-1-at-2026-08-21-01-28-71d04aa1.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_record(path):
    return {"name": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)}


def dump_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def parsed(table, row):
    result = dict(row)
    for column in JSON_COLUMNS.get(table, set()):
        if result.get(column) is not None:
            result[column] = json.loads(result[column])
    return result


def scan(value, location="$", hits=None):
    """只返回字段位置、模式名称和次数；从不返回匹配值。"""
    if hits is None:
        hits = Counter()
    if isinstance(value, dict):
        for key, item in value.items():
            path = location + "." + key
            if IDENTITY_FIELD.search(key):
                hits[(path, "sensitive_field_name")] += 1
            scan(item, path, hits)
    elif isinstance(value, list):
        for item in value:
            scan(item, location + "[]", hits)
    elif isinstance(value, str):
        for name, pattern in SECRET_PATTERNS.items():
            count = len(pattern.findall(value))
            if count:
                hits[(location, name)] += count
    return hits


def scan_report(value):
    return [{"location": path, "reason": reason, "count": count}
            for (path, reason), count in sorted(scan(value).items())]


def omission_reason(table):
    if table.startswith(("auth_", "authtoken_", "htx_", "organization", "jwt_auth_", "session_policy_", "token_blacklist_", "users_")) or table == "django_session":
        return "账号、身份、组织、权限或认证设置；未读取数据值。"
    if table.startswith(("io_storages_", "ml_", "webhook")):
        return "外部服务或存储集成，可能包含访问凭据；未读取数据值。"
    if table.startswith(("django_", "core_")) or table == "sqlite_sequence":
        return "应用框架、迁移、运行维护或内部序列；仅记录表结构与计数。"
    if table == "tasks_tasklock":
        return "运行时任务锁，不代表持久标注结果。"
    return "不在本次研究状态白名单中；仅记录表结构与计数，未导出记录值。"


def compare_existing(exports_dir, tables):
    tasks = {row["id"]: parsed("task", row) for row in tables["task"]}
    annotations = {row["id"]: parsed("task_completion", row) for row in tables["task_completion"]}
    current_task_ids = defaultdict(set)
    current_annotation_ids = defaultdict(set)
    for row in tables["task"]:
        current_task_ids[row["project_id"]].add(row["id"])
    for row in tables["task_completion"]:
        current_annotation_ids[row["project_id"]].add(row["id"])
    reports = []
    seen_tasks, seen_annotations, exact_annotations = set(), set(), set()
    original_sensitive = None
    for path in sorted(exports_dir.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        report = {"source": file_record(path), "scan_findings": scan_report(value)}
        if isinstance(value, list):
            task_ids = {row["id"] for row in value}
            old_annotations = [item for row in value for item in row.get("annotations", [])]
            annotation_ids = {row["id"] for row in old_annotations}
            project_ids = sorted({row["project"] for row in value})
            seen_tasks |= task_ids
            seen_annotations |= annotation_ids
            unchanged = 0
            for row in old_annotations:
                now = annotations.get(row["id"])
                if now and row["result"] == now["result"] and row["task"] == now["task_id"] and bool(row["was_cancelled"]) == bool(now["was_cancelled"]) and bool(row["ground_truth"]) == bool(now["ground_truth"]):
                    unchanged += 1
                    exact_annotations.add(row["id"])
            expected_tasks = set().union(*(current_task_ids[x] for x in project_ids))
            expected_annotations = set().union(*(current_annotation_ids[x] for x in project_ids))
            report.update({
                "kind": "task_export", "project_ids": project_ids,
                "task_count": len(value), "annotation_count": len(old_annotations),
                "draft_count": sum(len(row.get("drafts", [])) for row in value),
                "prediction_count": sum(len(row.get("predictions", [])) for row in value),
                "matching_current_task_data": sum(row["id"] in tasks and row["data"] == tasks[row["id"]]["data"] for row in value),
                "matching_current_annotation_research_values": unchanged,
                "current_task_ids_missing_from_export": sorted(expected_tasks - task_ids),
                "current_annotation_ids_missing_from_export": sorted(expected_annotations - annotation_ids),
                "export_task_ids_absent_from_current_db": sorted(task_ids - set(tasks)),
                "export_annotation_ids_absent_from_current_db": sorted(annotation_ids - set(annotations)),
            })
        else:
            report["kind"] = "export_metadata"
        reports.append(report)
        if path.name == HISTORICAL_FILE:
            original_sensitive = (path, value)
    coverage = {
        "files": reports,
        "union_current_tasks_covered": len(set(tasks) & seen_tasks),
        "union_current_annotations_covered_by_id": len(set(annotations) & seen_annotations),
        "union_current_annotations_with_matching_research_values": len(exact_annotations),
        "current_task_ids_missing_from_all_old_exports": sorted(set(tasks) - seen_tasks),
        "current_annotation_ids_missing_from_all_old_exports": sorted(set(annotations) - seen_annotations),
        "说明": "只比较ID、任务data、标注result及任务归属、取消与ground_truth状态；不作标签语义分析，不输出标签正文。",
    }
    return coverage, original_sensitive


def sanitized_historical(original, output):
    source_path, original_value = original
    cleaned = json.loads(json.dumps(original_value, ensure_ascii=False))
    removed = []
    for task_index, task in enumerate(cleaned):
        for draft_index, draft in enumerate(task.get("drafts", [])):
            if "created_username" in draft:
                del draft["created_username"]
                removed.append(f"/{task_index}/drafts/{draft_index}/created_username")
    if len(removed) != 1:
        raise RuntimeError("历史镜像待移除字段数量与已审查范围不符；未写入镜像。")
    # 只逆向移除精确 pointer，确保其他 JSON 值与原始对象完全相同。
    expected = json.loads(json.dumps(original_value, ensure_ascii=False))
    for pointer in removed:
        parts = pointer.split("/")[1:]
        target = expected
        for part in parts[:-1]:
            target = target[int(part)] if isinstance(target, list) else target[part]
        del target[parts[-1]]
    if cleaned != expected or scan_report(cleaned):
        raise RuntimeError("历史镜像在许可移除范围外有差异，或仍命中敏感字段／模式。")
    destination = output / "sanitized-exports" / source_path.name
    dump_new(destination, cleaned)
    if json.loads(destination.read_text(encoding="utf-8")) != expected:
        raise RuntimeError("历史镜像写后核验失败。")
    return {
        "original": file_record(source_path),
        "original_local_path": str(source_path),
        "mirror": {"path": destination.relative_to(output).as_posix(), **file_record(destination)},
        "removed_json_pointers": removed,
        "removed_field_count": len(removed),
        "all_other_json_values_equal": True,
        "remaining_scan_findings": [],
        "说明": "仅移除草稿中的本地标注用户名。原文件不改动且不入库；数字ID、文章作者和所有任务／标注／草稿／预测研究值保留。",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--existing-exports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(path.suffix == ".json" for path in output.rglob("*")):
        raise RuntimeError("输出目录已有JSON产物；请使用新目录，禁止覆盖历史归档。")
    database = args.database.resolve(strict=True)
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    # 首次读取固定一个读事务快照；之后所有表读取属于同一事务。
    connection.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
    started = datetime.now(timezone.utc).isoformat()
    components = [database] + [Path(str(database) + suffix) for suffix in ("-wal", "-journal") if Path(str(database) + suffix).exists()]
    source_before = [file_record(path) for path in components]
    schema = []
    tables = {}
    for entry in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        table = entry["name"]
        columns = [{"name": row["name"], "type": row["type"]} for row in connection.execute("PRAGMA table_info(" + quoted(table) + ")")]
        count = connection.execute("SELECT COUNT(*) FROM " + quoted(table)).fetchone()[0]
        whitelist = WHITELIST.get(table, [])
        missing = set(whitelist) - {column["name"] for column in columns}
        if missing:
            raise RuntimeError("白名单列缺失：" + table + "/" + ",".join(sorted(missing)))
        record = {"table": table, "columns": columns, "row_count": count, "exported_columns": whitelist,
                  "omitted_columns": [column["name"] for column in columns if column["name"] not in whitelist]}
        if whitelist:
            order = "id" if "id" in whitelist else "project_id"
            statement = "SELECT " + ",".join(map(quoted, whitelist)) + " FROM " + quoted(table) + " ORDER BY " + quoted(order)
            tables[table] = [dict(row) for row in connection.execute(statement)]
            record["omission_reason"] = "project中的认证、组织／账号关系、运行管理与派生搜索字段不导出。" if table == "project" else "无列省略。"
        else:
            record["omission_reason"] = omission_reason(table)
        schema.append(record)
    if set(WHITELIST) - set(tables):
        raise RuntimeError("数据库缺少研究白名单表。")
    decoded = {table: [parsed(table, row) for row in rows] for table, rows in tables.items()}
    findings = scan_report(decoded)
    if findings:
        print(json.dumps({"归档前扫描命中": findings}, ensure_ascii=False))
        raise RuntimeError("白名单研究值命中潜在身份字段或凭据模式；未写入研究数据。")
    coverage, historical = compare_existing(args.existing_exports, tables)
    if historical is None:
        raise RuntimeError("缺少本次指定的历史导出。")
    ids = {table: {row["id"] for row in rows} for table, rows in tables.items() if "id" in WHITELIST[table]}
    if any(len(ids[table]) != len(tables[table]) for table in ids):
        raise RuntimeError("研究表ID重复。")
    if any(row["project_id"] not in ids["project"] for row in tables["task"]):
        raise RuntimeError("任务引用不存在的项目。")
    for table in ("task_completion", "prediction", "tasks_annotationdraft"):
        if any(row["task_id"] not in ids["task"] for row in tables[table]):
            raise RuntimeError("标注／预测／草稿引用不存在的任务。")
    raw_payload = {"schema_version": "label-studio-research-tables-v1", "tables": tables,
                   "说明": "各列保持SQLite返回的原始值，JSON列仍为未经改写的字符串。账号表和认证字段不在此包内。"}
    dump_new(output / "research-tables.json", raw_payload)
    if json.loads((output / "research-tables.json").read_text(encoding="utf-8")) != raw_payload:
        raise RuntimeError("白名单数据写后逐值核验失败。")
    dump_new(output / "projects.json", decoded["project"])
    grouped = defaultdict(list)
    annotation_by_task, prediction_by_task, draft_by_task = defaultdict(list), defaultdict(list), defaultdict(list)
    mappings = {"project_id": "project", "task_id": "task", "completed_by_id": "completed_by", "updated_by_id": "updated_by", "last_created_by_id": "last_created_by", "parent_prediction_id": "parent_prediction", "parent_annotation_id": "parent_annotation"}
    for table, index in (("task_completion", annotation_by_task), ("prediction", prediction_by_task), ("tasks_annotationdraft", draft_by_task)):
        for row in decoded[table]:
            index[row["task_id"]].append({mappings.get(key, key): value for key, value in row.items()})
    for row in decoded["task"]:
        task = {mappings.get(key, key): value for key, value in row.items()}
        task.update(annotations=annotation_by_task[row["id"]], predictions=prediction_by_task[row["id"]], drafts=draft_by_task[row["id"]])
        grouped[row["project_id"]].append(task)
    by_project = []
    for project in decoded["project"]:
        project_id = project["id"]
        values = grouped[project_id]
        path = output / f"project-{project_id}-tasks.json"
        dump_new(path, values)
        if json.loads(path.read_text(encoding="utf-8")) != values:
            raise RuntimeError("项目任务JSON写后核验失败。")
        by_project.append({"project_id": project_id, "tasks": len(values), "annotations": sum(len(row["annotations"]) for row in values), "predictions": sum(len(row["predictions"]) for row in values), "drafts": sum(len(row["drafts"]) for row in values)})
    mirror = sanitized_historical(historical, output)
    dump_new(output / "existing-export-coverage.json", coverage)
    dump_new(output / "sanitized-exports-validation.json", mirror)
    dump_new(output / "schema-and-exclusions.json", schema)
    source_after = [file_record(path) for path in components]
    if source_before != source_after:
        raise RuntimeError("读取期间数据库／WAL／journal字节发生变化；归档不应发布，须使用新目录重试。")
    journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
    query_only = connection.execute("PRAGMA query_only").fetchone()[0]
    foreign_key_issues = sum(1 for _ in connection.execute("PRAGMA foreign_key_check"))
    connection.rollback()
    connection.close()
    if foreign_key_issues:
        raise RuntimeError("源数据库存在外键异常；只报告数量，不输出内容。")
    validation = {
        "schema_version": "label-studio-research-archive-validation-v1",
        "source_database_local_path": str(database),
        "snapshot_started_at_utc": started,
        "snapshot_finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only_uri": True, "query_only": query_only == 1,
        "single_read_transaction": True, "journal_mode": journal_mode,
        "source_components_before": source_before, "source_components_after": source_after,
        "source_component_bytes_unchanged": source_before == source_after,
        "source_authentication_values_read": False,
        "project_counts": by_project,
        "total_tasks": len(tables["task"]), "total_annotations": len(tables["task_completion"]),
        "total_predictions": len(tables["prediction"]), "total_drafts": len(tables["tasks_annotationdraft"]),
        "unique_ids_pass": True, "research_foreign_keys_pass": True,
        "source_foreign_key_issue_count": foreign_key_issues,
        "raw_sqlite_values_round_trip_equal": True,
        "project_json_round_trip_equal": True,
        "archive_scan_findings": findings,
        "historical_mirror_only_allowed_pointer_removed": mirror["all_other_json_values_equal"],
        "old_exports_missing_current_annotation_count": len(coverage["current_annotation_ids_missing_from_all_old_exports"]),
        "live_application_import_tested": False,
        "说明": "仅做程序级归档、字段／数量／ID／逐值／hash核验；未向模型展示任务、标签或validation reserve正文，未作新的研究推断。",
    }
    dump_new(output / "validation.json", validation)
    manifest = {
        "schema_version": "label-studio-research-archive-manifest-v1",
        "source_database": source_before[0], "table_column_whitelist": WHITELIST,
        "project_counts": by_project,
        "retained_numeric_account_references": "原始数字ID仅作为标注归属与研究追踪关系保留；没有账号记录或ID到身份的映射。",
        "not_a_full_application_database": True,
        "files": [{"path": path.relative_to(output).as_posix(), **file_record(path)} for path in sorted(output.rglob("*")) if path.is_file()],
        "说明": "此manifest不列自身；原始SQLite、.env、账号密码、token、session、组织与存储凭据不包含在归档中。",
    }
    dump_new(output / "manifest.json", manifest)
    print(json.dumps({"projects": by_project, "total_tasks": validation["total_tasks"], "total_annotations": validation["total_annotations"], "missing_from_old_exports": validation["old_exports_missing_current_annotation_count"], "historical_removed_fields": mirror["removed_field_count"], "source_bytes_unchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # 不打印可能携带JSON／数据库记录值的通用异常正文或栈。
        print(json.dumps({"error_type": type(error).__name__, "说明": "归档未成功；不发布未完成目录。错误详情须通过只含字段名／计数的检查定位。"}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
