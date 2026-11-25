#!/usr/bin/env python3
"""Validate root-level skill packages without executing their scripts."""
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit('ERROR: install repository dependencies: python -m pip install -r requirements-dev.txt')


RESOURCE_DIRS = {'docs', 'scripts', 'tests', 'templates', 'examples', 'assets'}
NAME = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently overwriting metadata."""


def mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError('YAML mapping keys must be strings')
        if key in result:
            raise ValueError(f'duplicate YAML key: {key}')
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def validate_skill(folder):
    errors = []
    try:
        content = (folder / 'SKILL.md').read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError) as exc:
        return None, [f'cannot read SKILL.md: {exc}']
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)', content, re.S)
    if not match:
        return None, ['missing or invalid YAML frontmatter delimiters']
    try:
        metadata = yaml.load(match.group(1), Loader=UniqueLoader)
    except (yaml.YAMLError, ValueError, TypeError) as exc:
        return None, [f'invalid YAML: {exc}']
    if not isinstance(metadata, dict):
        return None, ['frontmatter must be a mapping']
    name = metadata.get('name')
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
        errors.append('name must use lowercase letters, digits and single hyphens (1-64 characters)')
    elif name != folder.name:
        errors.append(f'name {name!r} must match directory {folder.name!r}')
    description = metadata.get('description')
    if not isinstance(description, str) or not description.strip():
        errors.append('description must be a non-empty string')
    elif len(description) > 1024:
        errors.append('description exceeds 1024 characters')
    if not content[match.end():].strip():
        errors.append('skill instructions must not be empty')
    return name if isinstance(name, str) else None, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--skill', help='Validate one direct child skill directory')
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f'repository root is not a directory: {root}')
    if args.skill:
        if not NAME.fullmatch(args.skill) or len(args.skill) > 64:
            parser.error('--skill must be a skill directory name, not a path')
        folders = [root / args.skill]
    else:
        folders = sorted(p for p in root.iterdir() if p.is_dir()
                         and not p.name.startswith('.') and p.name not in RESOURCE_DIRS
                         and p.name not in {'venv', '__pycache__'})
    if not folders:
        print('ERROR: no skill directories found', file=sys.stderr)
        return 1
    names = {}
    failures = 0
    for folder in folders:
        name, errors = validate_skill(folder)
        if name:
            if name in names:
                errors.append(f'duplicate skill name {name!r}; also found in {names[name]}')
            names[name] = folder.name
        if errors:
            failures += 1
            for error in errors:
                print(f'ERROR {folder.name}: {error}', file=sys.stderr)
        else:
            print(f'OK {folder.name}')
    print(f'Checked {len(folders)} skill(s); {failures} failed.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
