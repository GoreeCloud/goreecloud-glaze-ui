#!/usr/bin/env python3
"""Inventory V1.3 candidate-named sources without mutating or promoting them."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'dist', 'build'}
TEXT_SUFFIXES = {'.css', '.html', '.js', '.json', '.md', '.mjs', '.py', '.txt', '.yml', '.yaml'}
CANDIDATE_CSS = 'css/glaze-v1.3.0-candidate.css'
CANDIDATE_RUNTIME = 'js/glaze-v1.3.0-candidate.mjs'


def iter_files(root: Path):
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        yield relative, path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    args = parser.parse_args()

    candidate_named_paths: list[str] = []
    candidate_reference_files: list[str] = []
    for relative, path in iter_files(ROOT):
        rel = relative.as_posix()
        lower = rel.lower()
        if 'v1.3' in lower and 'candidate' in lower:
            candidate_named_paths.append(rel)
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            continue
        if 'v1.3' in text.lower() and 'candidate' in text.lower():
            candidate_reference_files.append(rel)

    result = {
        'schemaVersion': 1,
        'product': 'GLAZE UI V1.3 — Adaptive Resonance',
        'purpose': 'pre-promotion-source-namespace-inventory',
        'lifecycleAuthority': False,
        'qualificationEffect': 'inventory-only-no-pass',
        'candidateNamedPaths': sorted(set(candidate_named_paths)),
        'candidateReferenceFiles': sorted(set(candidate_reference_files)),
        'officialCandidateEntrypoints': {
            'css': {'path': CANDIDATE_CSS, 'exists': (ROOT / CANDIDATE_CSS).exists()},
            'runtime': {'path': CANDIDATE_RUNTIME, 'exists': (ROOT / CANDIDATE_RUNTIME).exists()},
        },
    }
    result['counts'] = {
        'candidateNamedPaths': len(result['candidateNamedPaths']),
        'candidateReferenceFiles': len(result['candidateReferenceFiles']),
    }

    rendered = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        Path(args.output).write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
