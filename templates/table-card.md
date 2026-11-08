# 表卡片：TODO_表名

- 粒度：一行 = TODO（例：一个用户 × 一天）
- 分区字段：`pt_d`（yyyyMMdd，脚本运行周期对应的日期）、`pt_h`（HH，00–23，小时粒度表才有）、`device_type`（Phone / Tablet / Vision 等，全量见 `docs/sparksql-style.md`）
- DDL 来源：Hive Metastore 导出（日期：TODO）
- 字段含义与枚举：见下表，含义不明标「待确认」不许猜
- 负责人：TODO
- 状态：推荐使用 / 谨慎使用 / 已下线（下线表写明替代表）
- 坑：TODO（例：某字段 2023 年后口径变更、某字段已废弃勿用）

| 字段 | 类型 | 含义 | 枚举/口径 |
| ---- | ---- | ---- | --------- |
| TODO | TODO | TODO | TODO |
