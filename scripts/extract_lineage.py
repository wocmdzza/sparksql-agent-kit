#!/usr/bin/env python3
"""Offline lineage extractor for SparkSQL scripts (pilot, v0.1).

Reads .sql files, parses each statement with sqlglot (Spark dialect) and
emits one JSON record per file: output table, input tables, CTE/temp names,
join keys, partition filters, and parse errors. Facts only -- no LLM, no
network, no writes to any warehouse. Run: python3 extract_lineage.py <dir>

v0.2 fix (2026-11-05, tested with sqlglot 30.29.0): partition-filter
detection now also covers unquoted ${var} and date-function-wrapped
values (dt = ${bizdate}, dt = date_sub('${bizdate}', 7)), and tables
created earlier in the same file (TEMPORARY VIEW / temp table) are no
longer listed as inputs. Known limit: a ${var} embedded in a table
name (ods_log_${bizdate}) parses but the table name comes out mangled --
flag those for manual review.

v0.3 fix (2026-11-06): partition names now match 使用者's business
conventions -- pt_d (day), pt_h (hour) and device_type -- not just the
generic dt/ds/pt. pt_d/pt_h must be tried before bare pt: with word
boundaries, pt alone never matches pt_d.
"""
import json
import re
import sys
from pathlib import Path

import sqlglot
from sqlglot import exp


def _tables(node):
    return sorted({t.sql(dialect="spark") for t in node.find_all(exp.Table)})


def _partition_filters(sql_text):
    # Partition-pruning filters, the facts that matter most for a
    # SparkSQL review. Kept regex-based on purpose: sqlglot normalises
    # the predicate away from its literal form.
    # Partition names (使用者's business conventions, 2026-11-06):
    #   pt_d         day partition     pt_h   hour partition
    #   device_type  device-type partition
    # plus the older generic names (dt/ds/pt/...) kept for legacy scripts.
    # Value forms covered, because real scripts use all of them:
    #   '2026-11-04'            quoted literal
    #   ${bizdate}              unquoted scheduling variable (incl. the
    #                           PARTITION(pt_d=${bizdate}) write clause)
    #   date_sub('${bizdate}',7) date function wrapping a literal/variable
    pat = re.compile(
        r"(?i)\b(pt_d|pt_h|device_type|dt|ds|pt|p_date|biz_date)\b\s*"
        r"(=|>=|<=|>|<|BETWEEN)\s*"
        r"('[^']*'|\$\{[^}]*\}|[A-Za-z_][\w]*\s*\([^)]*\))")
    return sorted({m.group(0) for m in pat.finditer(sql_text)})


def _join_keys(node):
    keys = set()
    for join in node.find_all(exp.Join):
        on = join.args.get("on")
        if on:
            keys.add(on.sql(dialect="spark"))
    return sorted(keys)


def analyse_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    rec = {"file": str(path), "statements": [], "parse_errors": []}
    try:
        stmts = sqlglot.parse(text, read="spark")
    except Exception as e:  # noqa: BLE001 - report, don't crash the batch
        rec["parse_errors"].append(str(e))
        return rec
    # Names created earlier in this same file (TEMPORARY VIEW / temp table):
    # they are intermediate steps, not real warehouse inputs.
    created_here = set()
    for stmt in stmts:
        if stmt is None:
            rec["parse_errors"].append("unparseable statement")
            continue
        s = {"kind": stmt.__class__.__name__}
        if isinstance(stmt, exp.Cache):
            s["kind"] = "Cache"
        # Output table: INSERT / CREATE TABLE AS / CREATE VIEW
        out = stmt.args.get("this")
        if isinstance(stmt, (exp.Insert, exp.Cache)):
            target = stmt.find(exp.Table)
            if target is not None:
                s["output_table"] = target.sql(dialect="spark")
        elif isinstance(stmt, exp.Create):
            tbl = stmt.find(exp.Table)
            if tbl is not None:
                s["output_table"] = tbl.sql(dialect="spark")
                created_here.add(tbl.name.lower())
        s["cte_names"] = sorted({c.alias for c in stmt.find_all(exp.CTE)})
        # CTEs are local definitions, not real input tables.
        s["input_tables"] = [
            t for t in _tables(stmt)
            if t != s.get("output_table")
            and t.split(" AS ")[0].strip().lower() not in
            {c.lower() for c in s["cte_names"]}
            and t.split(" AS ")[0].strip().lower() not in created_here
        ]
        s["join_keys"] = _join_keys(stmt)
        s["partition_filters"] = _partition_filters(stmt.sql(dialect="spark"))
        rec["statements"].append(s)
    return rec


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path(".")
    files = sorted(root.rglob("*.sql")) if root.is_dir() else [root]
    out = [analyse_file(f) for f in files]
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv)
