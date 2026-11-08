# SparkSQL Agent 试点工具包 v0.1（草稿）

> 怎么部署、怎么日常使用见 `USAGE.md`；本文件只讲构成和已定事项。

给使用者的内部 SparkSQL agent 落地用的起步套件，对应 2026-11-05 上午
「定制 Agent 理解 SparkSQL 脚本」方案里的第 1–3 周：先跑通试点，再推广。
**不含任何公司脚本或数据**，示例是合成的；真实脚本只在公司内网跑。

## 里面有什么

| 文件 | 用途 |
| ---- | ---- |
| `scripts/extract_lineage.py` | 离线血缘提取：sqlglot（Spark 方言）解析 `.sql`，输出产出表、输入表、CTE、join 键、分区过滤、解析错误（JSON）。已在合成样例上验证通过 |
| `examples/sample_daily.sql` | 合成样例（INSERT OVERWRITE + CTE + join），仅用于验证提取器 |
| `skills/sparksql-dev/SKILL.md` | 主 Skill v0.5 草稿：强制流程 + 红线 + 自检清单（离线静态校验 + 日志存文件读取闭环；变量只认 `set` + `${...}`；正式脚本注释头/`@Modify`；分区约定 pt_d/pt_h/device_type 已定版） |
| `docs/sparksql-style.md` | SQL 编写规范：分区已定版（pt_d=yyyyMMdd 运行周期日期、pt_h=HH、多级按 pt_d/pt_h/device_type、device_type 枚举待补全），排版只定关键字小写 + 前逗号，其余暂不设置保持现状 |
| `docs/udf-catalog.md` | 自定义 UDF 清单模板：总表 + 每函数一张卡（签名/空值/示例/不该用的场景），待 使用者 对照 wiki 手工整理后填公司内网副本 |
| `templates/script-header.md` | 正式脚本注释头占位：仅 `@Modify` 规则已确认，全文模板待 使用者 提供 |
| `templates/table-card.md` | 表卡片模板 |
| `templates/logic-card.md` | 逻辑卡片模板 |
| `templates/pilot-inventory.md` | 试点盘点表：按产出表填 20–30 个核心脚本，填完再跑提取器 |

## 在公司内网跑试点（第 1 步）

本地 shell 以 PowerShell 为主，Python 用 uv 管理：

```powershell
uv run --with sqlglot python scripts\extract_lineage.py <核心脚本目录>
```

（sqlglot 已确认可从公司内网源安装；在本机 Linux 验证时用
`python3 scripts/extract_lineage.py ...` 等价。）

先挑核心链路 20–30 个脚本。解析错误率高的脚本先记下来——那往往是
方言/模板变量（如 `${bizdate}`）需要特殊处理的地方，不是直接扔给模型。

## 已定事项（2026-11-05 使用者 补充的第一批对齐）

- 执行边界：本地无测试/开发环境、无数据源，完全无法运行 SQL；Agent 只做
  生成 `.sql` 文件 + 离线 Python 解析/格式化。校验走静态校验，
  运行反馈走人工从 SparkUI 复制 YARN/Spark 日志回贴的闭环。
- 审批：内部调度平台、人工提交、对 SQL 无强要求，Agent 不关注；
  脚本可用 `SET`、临时表、平台自定义 UDF（清单见 `docs/udf-catalog.md`）。
- 协作：VSCode + Windows Terminal 跑 CLI，CLI 可读本地文件/项目，
  仅本地 Git 管理。
- CLI 能力：已确认支持按需加载 `SKILL.md`、调本地 shell、接 MCP
  （有限，仅公司内部公开资料/论坛）；项目指令自动加载不确定，
  先按支持假设推进，Skill 结构不依赖它。
- 本地环境（2026-11-06 第二批对齐）：shell 以 PowerShell 为主，
  Python 由 uv 管理（版本不必特意关注），离线脚本用 `uv run` 跑；
  sqlglot 可从公司内网源安装。
- 变量：平台只用过 `set example='xxx'` + `${example}` 一种形式，
  平时脚本不太用变量；其他形式未验证，暂按不支持处理，Skill 禁止生成。
- 日志：由 使用者 手工保存成文件放进项目目录，CLI 直接读文件分析。
- 注释头：只有正式脚本有固定注释头，测试脚本不需要；`@Modify` 行
  须写变更日期 + 改动简述，全文模板由 使用者 提供
  （占位见 `templates/script-header.md`）。
- UDF：公司 wiki 有文档，但用 CLI 的 MCP 获取已实测失败；
  改由 使用者 按 `docs/udf-catalog.md` 模板手工整理。

## 还需要 使用者 定（没定也能先跑提取器）

1. 核心脚本目录在哪、产出表怎么盘点（按产出表，不按文件）。
2. `device_type` 完整枚举（已知 Phone/Tablet/Vision，补进 `docs/sparksql-style.md`）。
3. 注释头全文模板（见 `templates/script-header.md` 待补清单）。
4. 其余细节（暂缓，使用者 有时间再确认）：Spark/Hive 版本、
   平时查 DDL/字段含义的路径、脚本目录结构与一文件一任务还是多语句、
   规范里标【暂不设置】的排版/命名/写法各項。

## 安全边界

- 提取器只读本地 `.sql` 文件，不联网、不连仓库、不执行 SQL。
- Agent 只出 SQL 草稿，不直连生产执行、不自动上线；样本只给脱敏 schema。
- 凭证不进 Skill 和知识库。
