# 使用说明：sparksql-agent-kit 怎么用

> 工具包现在在 维护者的工作区里，只是草稿源文件；真正干活要把它
> 放到你本地 Windows 的 SQL 项目里，给公司内部 CLI 用。
> 工具包内无公司脚本/数据（样例均为合成），带入公司内网的方式
> 按公司规定走。

## 一、放到哪（不要整包放进 CLI 的 skills 目录）

分开放，两类东西两个归属：

- **进 CLI 的 skills 目录的只有一份**：`skills/sparksql-dev/SKILL.md`
  （含它自己的文件夹 `sparksql-dev/`）。skills 目录是放「能力」的，
  通常全局生效、可能被 CLI 升级或同步覆盖。
- **其余全部放你的 SQL 项目里**：`docs/`、`templates/`、`scripts/`、
  说明文件。它们是「这个项目的知识和工具」，要跟着项目走本地 Git，
  尤其是填好真实内容的 UDF 清单、表卡、逻辑卡——放进 skills 目录
  一旦被覆盖就丢了，而且换个项目还会串味。
- `examples/` 和本说明不必部署；`scripts/extract_lineage.py` 是
  项目工具、不是 Skill 的一部分，同样放项目里（见下方目录图）。

关键是 Skill 里引用的 `docs/...`、`templates/...`、
`scripts/...` 都是相对项目根目录的路径：CLI 在项目目录里启动时，
按 Skill 的指引去项目里读这些文件，与 SKILL.md 本身放在哪无关。

```text
<你的 SQL 项目>/
├─ skills/sparksql-dev/SKILL.md   ← 内部 CLI 的技能目录若另有规定，
│                                   按它的规定放这一份，docs/templates
│                                   仍留在项目里，Skill 里改成对应路径
├─ docs/
│  ├─ udf-catalog.md               ← 你手工整理的 UDF 清单（持续更新）
│  ├─ sparksql-style.md            ← 编写规范（持续更新）
│  ├─ table-cards/                 ← 按模板新建：一表一卡（后续逐步建）
│  └─ logic-cards/                 ← 按模板新建：一核心脚本一卡
├─ templates/                      ← 模板，只读参照，填卡时复制着写
│  ├─ table-card.md / logic-card.md / pilot-inventory.md / script-header.md
├─ scripts/extract_lineage.py      ← 离线血缘/分区校验工具，CLI 调用
├─ examples/sample_daily.sql       ← 合成样例，仅验证工具链，可删
└─ <你自己的 .sql 脚本目录>
```

## 一之二、从公开仓 copy 后先还原

从 GitHub 公开仓拿到的是脱敏版。copy 到公司电脑后，先按根目录
`RESTORE.md` 的约定还原成本地真实版再用：A 类还原词全局替换、
B 类 `{{...}}` 占位符逐个替换（可用 `scripts/restore_placeholders.py`
+ 只存本地的映射文件批量做）、C 类模板（表卡/UDF 等）就地填。
公开版放只读参照目录、真实内容只填在项目目录里，不要互相覆盖。

## 二、第一次用之前要填什么（按顺序，填多少用多少）

1. `docs/sparksql-style.md`：分区已定版（pt_d=yyyyMMdd 运行周期日期、pt_h=HH、多级按 pt_d/pt_h/device_type，device_type 已知 Phone/Tablet/Vision、全量待补），排版只定关键字小写 + 字段前逗号两条，其余暂不设置、保持现状——不要再按旧版“逐项确认按默认”来填。
2. `templates/script-header.md`：把你的正式脚本注释头全文替换进来。
3. `docs/udf-catalog.md`：先填最近常用的高频 UDF，不用填全。
4. `templates/pilot-inventory.md`：按产出表填 20–30 个核心脚本，
   然后跑一次提取器（见第四节），拿到血缘和解析错误清单。
5. 表卡/逻辑卡：从核心链路开始，按模板一表一卡、一脚本一卡慢慢建，
   不必一次建完；Agent 查不到卡时会明说「未找到」，不会编。

## 三、日常怎么用（在 Windows Terminal 里对内部 CLI 说话）

**写新脚本**：点名用 sparksql-dev，它会先问口径、查 docs 里的卡片，
先给方案等你确认，再生成 `.sql` 到本地、跑离线静态校验并声明未实际运行。
示例说法：

```text
用 sparksql-dev skill：按 pt_d='20261105'、device_type 只看 android，
写一个统计每日活跃用户的脚本，先给方案别直接写。
```

**改老脚本**：给出脚本路径和改动需求，它按规范改、更新 `@Modify`，
再跑一遍静态校验：

```text
用 sparksql-dev skill：改 scripts/dws_xxx.sql，口径从 X 改成 Y，
改完跑校验并告诉我影响了哪些输入/产出表。
```

**看日志排错**：你先从 SparkUI 把日志存成文件放进项目（如 `logs/`），
再给它路径，它读文件定位报错并给改好的完整 SQL：

```text
用 sparksql-dev skill：看 logs/dws_xxx_20261106.log，
定位失败原因并修改对应的 .sql。
```

## 四、提取器单独怎么跑（PowerShell）

```powershell
uv run --with sqlglot python scripts\extract_lineage.py <核心脚本目录>
```

输出 JSON：每个文件的产出表、输入表、join 键、分区过滤、解析错误。
除日常校验外，它也是试点盘点和批量建逻辑卡前的数据来源。

## 五、维护

- 表、口径、UDF、规范有变化，先改 `docs/` 对应文件，Agent 下次自动按新版执行。
- Skill 本身要改流程/红线时改 `SKILL.md` 并升版本号。
- 所有改动用本地 Git 提交即可，不必推远程。
