#!/usr/bin/env python3
"""Fail closed when the current GLAZE UI web entrypoint has an unsafe or incomplete CSS import graph."""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_ROOT = ROOT / "css"
ENTRYPOINT = CSS_ROOT / "glaze-v1.1.0.css"
IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*)?(?P<quote>[\"'])(?P<target>[^\"']+)(?P=quote)\s*\)?",
    flags=re.IGNORECASE,
)
COMMENT_RE = re.compile(r"/\*.*?\*/", flags=re.DOTALL)


def validate_import_closure(entrypoint: Path, css_root: Path) -> tuple[list[str], set[Path]]:
    errors: list[str] = []
    visited: set[Path] = set()
    active: list[Path] = []
    root = css_root.resolve()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            errors.append(f"CSS import escapes controlled root: {path}")
            return

        if resolved in active:
            cycle = " -> ".join(str(item.relative_to(root)) for item in [*active, resolved])
            errors.append(f"CSS import cycle detected: {cycle}")
            return
        if resolved in visited:
            return
        if path.is_symlink():
            errors.append(f"CSS import target must not be a symlink: {relative}")
            return
        if not resolved.is_file():
            errors.append(f"Missing CSS import target: {relative}")
            return

        visited.add(resolved)
        active.append(resolved)
        text = COMMENT_RE.sub("", resolved.read_text(encoding="utf-8"))
        for match in IMPORT_RE.finditer(text):
            target = match.group("target").strip()
            lowered = target.lower()
            if lowered.startswith(("http://", "https://", "//", "data:")):
                errors.append(f"Remote CSS import is not allowed in {relative}: {target}")
                continue
            if "?" in target or "#" in target:
                errors.append(f"CSS imports must use immutable repository paths in {relative}: {target}")
                continue
            import_path = Path(target)
            if import_path.is_absolute():
                errors.append(f"Absolute CSS import is not allowed in {relative}: {target}")
                continue
            if import_path.suffix.lower() != ".css":
                errors.append(f"CSS import target must be a .css file in {relative}: {target}")
                continue
            visit(resolved.parent / import_path)
        active.pop()

    visit(entrypoint)
    return errors, visited


def self_test() -> list[str]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="glaze-import-closure-") as temp:
        root = Path(temp) / "css"
        root.mkdir()

        (root / "entry.css").write_text('@import url("./child.css");\n', encoding="utf-8")
        (root / "child.css").write_text(":root { --ok: 1; }\n", encoding="utf-8")
        errors, visited = validate_import_closure(root / "entry.css", root)
        if errors or len(visited) != 2:
            failures.append("valid local import graph was rejected")

        (root / "entry.css").write_text('@import url("./missing.css");\n', encoding="utf-8")
        errors, _ = validate_import_closure(root / "entry.css", root)
        if not any("Missing CSS import target" in error for error in errors):
            failures.append("missing import target was not rejected")

        (root / "entry.css").write_text('@import url("https://example.invalid/remote.css");\n', encoding="utf-8")
        errors, _ = validate_import_closure(root / "entry.css", root)
        if not any("Remote CSS import" in error for error in errors):
            failures.append("remote import was not rejected")

        outside = Path(temp) / "outside.css"
        outside.write_text(":root { --outside: 1; }\n", encoding="utf-8")
        (root / "entry.css").write_text('@import url("../outside.css");\n', encoding="utf-8")
        errors, _ = validate_import_closure(root / "entry.css", root)
        if not any("escapes controlled root" in error for error in errors):
            failures.append("root-escaping import was not rejected")

        (root / "entry.css").write_text('@import url("./child.css");\n', encoding="utf-8")
        (root / "child.css").write_text('@import url("./entry.css");\n', encoding="utf-8")
        errors, _ = validate_import_closure(root / "entry.css", root)
        if not any("cycle detected" in error for error in errors):
            failures.append("import cycle was not rejected")

    return failures


def main() -> int:
    failures = self_test()
    errors, visited = validate_import_closure(ENTRYPOINT, CSS_ROOT)
    failures.extend(errors)
    if failures:
        print("GLAZE UI CSS import-closure validation FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"GLAZE UI CSS import closure: PASS ({len(visited)} repository-local CSS files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
