#!/usr/bin/env python3
"""Bounded offline EIP-712 collection inventory; no signing or transport."""
import argparse
import json
import re
import sys

from typed_digest import (TypedDataError, digest, load_workspace_json,
                          parse_hex, validate_tree)

MAX_REQUESTS = 16
MAX_REPORT_BYTES = 65536
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')


def inventory(manifest, loader=load_workspace_json):
    """Validate the complete manifest before reading any named request.

    A request is captured once and that same object supplies all its hashes.
    No grouping is returned if any entry is malformed or inaccessible.
    """
    validate_tree(manifest)
    if type(manifest) is not dict or set(manifest) != {'requests'}:
        raise TypedDataError('manifest needs exactly requests')
    requests = manifest['requests']
    if type(requests) is not list or not 1 <= len(requests) <= MAX_REQUESTS:
        raise TypedDataError('requests needs 1..16 entries')
    seen = set()
    for item in requests:
        if type(item) is not dict or not {'id', 'path'} <= set(item) or set(item) - {'id', 'path', 'expect'}:
            raise TypedDataError('entry needs id, path and optional expect')
        label, path = item['id'], item['path']
        if type(label) is not str or not LABEL.fullmatch(label) or label in seen:
            raise TypedDataError('id must be unique, 1..64 ASCII label characters')
        seen.add(label)
        if type(path) is not str or not 1 <= len(path) <= 1024:
            raise TypedDataError('path needs 1..1024 characters')
        if 'expect' in item:
            parse_hex(item['expect'], 32)
    rows = []
    for item in requests:
        result = digest(loader(item['path']))
        rows.append({
            'id': item['id'], 'path': item['path'],
            **{key: result[key] for key in ('primaryType', 'domainSeparator', 'messageHash', 'digest')},
            'matchesExpectedDigest': (result['digest'] == '0x' + parse_hex(item['expect'], 32).hex()
                                      if 'expect' in item else None),
        })

    def groups(key):
        grouped = {}
        for row in rows:
            grouped.setdefault(row[key], []).append(row['id'])
        return [{'hash': value, 'ids': ids} for value, ids in grouped.items() if len(ids) > 1]

    report = {
        'version': 1, 'complete': True, 'items': rows,
        'allSuppliedExpectationsMatch': all(row['matchesExpectedDigest'] is not False for row in rows),
        'allEntriesPinned': all(row['matchesExpectedDigest'] is not None for row in rows),
        'repeatedDigests': groups('digest'),
        'sharedDomainSeparators': groups('domainSeparator'),
        'meaning': 'Hash equality groups encodings, not source JSON identity, consent or replay protection.',
    }
    if len((json.dumps(report, ensure_ascii=True, indent=2) + '\n').encode()) > MAX_REPORT_BYTES:
        raise TypedDataError('report exceeds 65536 bytes')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', help='bounded workspace JSON manifest; paths resolve beneath cwd')
    args = parser.parse_args(argv)
    try:
        report = inventory(load_workspace_json(args.manifest))
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report['allSuppliedExpectationsMatch'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print('digest-inventory: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
