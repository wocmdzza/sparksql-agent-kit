#!/usr/bin/env python3
"""Restore a sanitized (public) copy of the kit to the local real version.

Reads a LOCAL mapping file (never committed anywhere) whose lines are
`PUBLIC_TEXT = REAL_VALUE`, replaces every occurrence of PUBLIC_TEXT in
.md/.sql/.py files under the target directory, and reports any
{{UPPER_SNAKE}} placeholders left over. Dry-run by default; pass
--apply to actually write.

Usage: uv run python scripts/restore_placeholders.py <dir> <mapping.txt> [--apply]
"""
import re
import sys
from pathlib import Path

SUFFIXES = {".md", ".sql", ".py", ".txt"}
TOKEN_RE = re.compile(r"\{\{[A-Z0-9_]+\}\}")


def load_mapping(path: Path):
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        public, real = line.split("=", 1)
        pairs.append((public.strip(), real.strip()))
    return pairs


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    root, mapping_file = Path(argv[1]), Path(argv[2])
    apply = "--apply" in argv[3:]
    pairs = load_mapping(mapping_file)
    # RESTORE.md and this script document the tokens on purpose;
    # they are not restore targets.
    files = [p for p in sorted(root.rglob("*"))
             if p.is_file() and p.suffix in SUFFIXES and p != mapping_file
             and p.name != "RESTORE.md"
             and p.resolve() != Path(__file__).resolve()]
    total = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        new = text
        for public, real in pairs:
            cnt = new.count(public)
            if cnt:
                total += cnt
                new = new.replace(public, real)
        if apply and new != text:
            f.write_text(new, encoding="utf-8")
    remaining = {}
    for f in files:
        text = (f.read_text(encoding="utf-8", errors="replace")
                if apply else f.read_text(encoding="utf-8", errors="replace"))
        # In dry-run, preview what would remain after replacement.
        if not apply:
            for public, real in pairs:
                text = text.replace(public, real)
        for tok in TOKEN_RE.findall(text):
            remaining[tok] = remaining.get(tok, 0) + 1
    mode = "applied" if apply else "dry-run, nothing written"
    print(f"replacements: {total} occurrence(s) across {len(files)} file(s) [{mode}]")
    if remaining:
        print("unresolved {{...}} placeholders:")
        for tok, cnt in sorted(remaining.items()):
            print(f"  {tok}: {cnt}")
    else:
        print("no {{...}} placeholders left")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
