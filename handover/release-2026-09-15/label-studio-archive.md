# Label Studio 研究状态归档：2026-09-15

本次将主目录中 Label Studio 的最新研究状态导出至 [`data/local/label-studio-research-archive-2026-09-15/`](../../data/local/label-studio-research-archive-2026-09-15/)。归档保存 3 个项目、328 个任务、41 条标注；现存旧导出的并集只有 39 条当前标注，新包补齐了项目 2 的另外 2 条。归档只是文件交接与程序核验，不是新的研究分析，也不提升标签的证据状态。328 指任务记录数，不代表 328 篇互不重复的文章。

原始数据库路径为 `F:\MyProjects\DeAIodorant\data\local\translation_v2_review\label_studio_data\label_studio.sqlite3`，大小 8,138,752 字节，SHA256 为 `7a672efd29d591b2ce1f5a93ce5b5f13ebabba7604a6c1d5750639ef7f682ca7`。原数据库及其认证信息只留本机，不入库。

## 保存的研究进度

| 原始项目 ID | 当前任务 | 当前标注 | 当前预测 | 当前草稿 | 该项目旧导出最多标注数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 220 | 9 | 0 | 0 | 9 |
| 2 | 83 | 7 | 0 | 0 | 5 |
| 3 | 25 | 25 | 0 | 0 | 25 |
| 合计 | 328 | 41 | 0 | 0 | 39 |

8 份旧任务导出全部通过相应任务 `data` 的逐值比较。旧导出并集中的 39 条当前标注，其 `result`、任务归属、取消状态和 `ground_truth` 状态与当前数据库一致。每份旧导出的覆盖、缺失 ID、文件 hash 及扫描结果见 [`existing-export-coverage.json`](../../data/local/label-studio-research-archive-2026-09-15/existing-export-coverage.json)。这里只检查值相等和覆盖，不解释标签含义；没有向模型显示任务、标签或 validation reserve 正文。

当前数据库草稿数为零。早期文件另保存 1 条历史草稿，新包的脱身份镜像保留了该历史状态，不能将其加到当前标注或草稿数量中。

## 数据保留与排除范围

[`research-tables.json`](../../data/local/label-studio-research-archive-2026-09-15/research-tables.json) 保留白名单列在 SQLite 中的原始值；其中 JSON 列仍保持未经改写的原始字符串。已保留的表包括 `project`、`task`、`task_completion`、`prediction`、`tasks_annotationdraft`，以及项目摘要、数据管理视图和筛选器、标注导航历史。任务文本、来源字段、候选标签及证据、人工标注、取消与 `ground_truth` 状态、原始任务／标注 ID、时间戳和关联 ID 均保留。

[`projects.json`](../../data/local/label-studio-research-archive-2026-09-15/projects.json) 保存经白名单筛选的项目研究设置，包括标签配置、研究说明、采样和标注数量设置。`project-1-tasks.json` 至 `project-3-tasks.json` 按项目组织任务及嵌套标注、预测和草稿，方便后续编写导入适配器；原始 ID 同时保存在规范研究表中。数字账号引用仅用于保留标注归属与研究追踪关系，没有账号记录或数字 ID 到真实身份的映射。

项目表采用明确的列白名单，排除了 `task_data_login`、`task_data_password`、`token`、组织／账号关系及运行管理字段。账号、密码 hash、访问 token、会话、组织信息、权限和登录设置，以及云存储、模型服务连接、webhook 等集成表均不导出；认证表只读取表结构与记录数，不读取数据值。运行时任务锁、迁移记录和内部序列也不进入研究包。完整表／列白名单、计数和省略原因见 [`schema-and-exclusions.json`](../../data/local/label-studio-research-archive-2026-09-15/schema-and-exclusions.json)。

`.env`、`OPEN_ME_credentials.txt`、原始 SQLite 和登录配置均不属于本包。此包不是可直接恢复登录的完整应用数据库，也不包含虚拟环境或应用服务。包内未启动网络服务、模型推理或训练。

## 早期导出的脱身份镜像

以下原文件含 1 个本地标注用户名字段，继续留本机并从发布范围排除：

```text
F:\MyProjects\DeAIodorant\data\local\translation_v2_review\label_studio_data\export\project-1-at-2026-08-21-01-28-71d04aa1.json
```

新镜像位于 [`sanitized-exports/project-1-at-2026-08-21-01-28-71d04aa1.json`](../../data/local/label-studio-research-archive-2026-09-15/sanitized-exports/project-1-at-2026-08-21-01-28-71d04aa1.json)。唯一许可移除的 JSON Pointer 为 `/0/drafts/0/created_username`。其余 JSON 值与原文件逐项相同；稳定数字 ID、文章作者、220 个任务以及 1 条历史草稿的研究内容全部保留。原文件未改写。由于重新序列化，镜像不主张除该字段外仍保持原始字节。

| 文件 | SHA256 |
| --- | --- |
| 原文件 | `7a202aa8c2a8f7fe8a83920f131b2e8d4538108d82fe0819fb04476628c4797c` |
| 脱身份镜像 | `29fbaaf47169f5d474efbbf7224a0e101247d8a907e5a3f7e2d8ca99563839c4` |

精确位置、删除数量、前后 hash 和逐值核验结果见 [`sanitized-exports-validation.json`](../../data/local/label-studio-research-archive-2026-09-15/sanitized-exports-validation.json)。其他旧 export 的字段／常见凭据模式扫描未命中；这项有限扫描不是任意秘密值绝对不存在的证明，发布方仍需执行本次整体凭据检查。

## 只读快照与验证

导出使用 Python 标准库 `sqlite3`，通过 `mode=ro` 打开数据库，再设置 `PRAGMA query_only=ON`，执行 `BEGIN` 并首次读取，固定同一读事务快照。所有研究表、表结构和计数均在该事务内读取，最后 `ROLLBACK` 结束读事务；不修改原数据库。此次 `journal_mode=delete`，没有 WAL 或 journal 侧文件参与快照。UTC 读取时间为 `2026-09-15T02:22:54.873752+00:00` 至 `2026-09-15T02:22:55.795886+00:00`。

源数据库读取前后字节数和 SHA256 一致。白名单数据和各项目 JSON 写入后逐值相等，表内 ID 无重复，研究任务／标注引用存在，源数据库外键检查发现 0 项异常。导出前对研究值的敏感字段名及常见凭据模式检查为 0 命中。新镜像只有上述精确 pointer 被移除。结果见 [`validation.json`](../../data/local/label-studio-research-archive-2026-09-15/validation.json)。

[`manifest.json`](../../data/local/label-studio-research-archive-2026-09-15/manifest.json) 记录源 hash、列白名单及包内另外 11 个文件的大小和 SHA256，不递归记录自身。生成后已独立重算这 11 个文件的 hash，全部通过。

## 换机后使用

研究状态可直接从 `research-tables.json` 读取；解释标注时应同时保留 `project_id` 和原始标签配置。若需要继续使用 Label Studio，应在新机器创建新的本地账号和项目，使用保存的项目配置及 `project-*-tasks.json` 编写适配导入。应用可能重新分配 ID，旧数字账号 ID 不能直接当作新机器账号；需另存旧 ID 到新 ID 的映射，并在导入后核对本表数量、任务文本和标注结果。不要在新环境中为恢复登录而导入本机原 SQLite。此次未启动 Label Studio，也未执行应用导入测试。

只验证文件完整性，不必打开正文或标签：

```powershell
@'
import hashlib, json
from pathlib import Path
root = Path('data/local/label-studio-research-archive-2026-09-15')
manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
for entry in manifest['files']:
    path = root / entry['path']
    assert path.stat().st_size == entry['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']
print(len(manifest['files']))
'@ | python -
```

预期输出 `11`。复现导出时只能写到新的空目录，不能覆盖本次归档或旧 exports：

```powershell
python data/local/label-studio-research-archive-2026-09-15/export_research_archive.py `
  --database 'F:\MyProjects\DeAIodorant\data\local\translation_v2_review\label_studio_data\label_studio.sqlite3' `
  --existing-exports 'F:\MyProjects\DeAIodorant\data\local\translation_v2_review\label_studio_data\export' `
  --output data/local/label-studio-research-archive-recheck
```

脚本同时是本次具体数据库 schema 的白名单契约；若未来新增列、存在潜在身份字段或源数据库在读取期间变化，应重新审查，不能将失败目录当作成功归档发布。脚本不输出正文、标签或匹配凭据值。

## 本次新增文件

下列 12 个文件位于 `data/local/label-studio-research-archive-2026-09-15/`，另有本说明 `handover/release-2026-09-15/label-studio-archive.md`：

- `export_research_archive.py`
- `research-tables.json`
- `projects.json`
- `project-1-tasks.json`
- `project-2-tasks.json`
- `project-3-tasks.json`
- `existing-export-coverage.json`
- `schema-and-exclusions.json`
- `sanitized-exports/project-1-at-2026-08-21-01-28-71d04aa1.json`
- `sanitized-exports-validation.json`
- `validation.json`
- `manifest.json`
