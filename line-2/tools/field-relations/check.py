#!/usr/bin/env python3
"""Check explicit scalar field relations and JSON structure, offline."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import types

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'jsonl-unique' / 'check.py'
    helper = types.ModuleType('relation_scalar_helpers')
    helper.__file__ = str(path)
    exec(compile(reader.read_bytes(path.relative_to(Path.cwd()).as_posix()), str(path), 'exec'), helper.__dict__)
    _, framing, source, engine, rules = helper.dependencies()
    return reader, helper, framing, source, engine, rules


def prepare(plan, helper):
    if not isinstance(plan, dict) or set(plan) != {'relations'}:
        raise ValueError('plan must contain only relations')
    rows = plan['relations']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 64:
        raise ValueError('plan needs 1 to 64 relations')
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'left', 'op', 'right'}:
            raise ValueError('each relation needs exactly left, op and right')
        if any(not isinstance(row[k], str) for k in row):
            raise ValueError('relation fields must be strings')
        if row['op'] not in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            raise ValueError('unsupported relation operator')
        # Repeated operands are useful (e.g. checking a root number); validate separately.
        helper.pointers_checked([row['left']])
        helper.pointers_checked([row['right']])
    return rows


def operand(document, helper, pointer):
    anchor = pointer
    while anchor not in document.values:
        anchor = anchor.rsplit('/', 1)[0]
    if pointer not in document.values:
        return {'pointer': pointer, 'present': False,
                'anchor_pointer': anchor, 'anchor_source': document.location(anchor)}, None, 'missing_value'
    location = {'pointer': pointer, 'present': True,
                'document_source': document.location(pointer)}
    value = helper.resolve(document.value, pointer)
    start, end = document.values[pointer]
    try:
        key = helper.scalar_key(value, document.text[start:end])
    except ValueError:
        return location, None, 'non_scalar_or_unsupported_number'
    location['type'] = key[0]
    return location, key, None


def inspect(reader, helper, framing, source, engine, rules, contract_name,
            document_name, plan_name, contract_sha256=None, document_sha256=None,
            plan_sha256=None):
    for pin in (contract_sha256, document_sha256, plan_sha256):
        if pin is not None and (not isinstance(pin, str) or not re.fullmatch('[0-9a-f]{64}', pin)):
            raise ValueError('expected SHA-256 must be 64 lowercase hex digits')
    captured = {}
    def capture(name, pin):
        if name not in captured:
            captured[name] = reader.read_bytes(name)
        raw = captured[name]
        if pin is not None and hashlib.sha256(raw).hexdigest() != pin:
            raise ValueError('source SHA-256 mismatch: ' + name)
        return source.Source(raw, name)
    plan = capture(plan_name, plan_sha256)
    comparisons = prepare(plan.value, helper)
    contract = capture(contract_name, contract_sha256)
    engine.prepare(contract.value)
    document = capture(document_name, document_sha256)
    structural = source.locate(engine, rules, contract, document)
    rows = []
    for i, relation in enumerate(comparisons):
        left, a, left_error = operand(document, helper, relation['left'])
        right, b, right_error = operand(document, helper, relation['right'])
        row = {'index': i, 'operator': relation['op'], 'left': left, 'right': right,
               'plan_source': plan.location('/relations/' + str(i)), 'valid': False}
        if left_error or right_error:
            row.update(status='invalid_operands', operand_errors={
                k: v for k, v in (('left', left_error), ('right', right_error)) if v})
        elif relation['op'] in ('eq', 'ne'):
            row['valid'] = (a == b) if relation['op'] == 'eq' else (a != b)
            row['status'] = 'passed' if row['valid'] else 'comparison_failed'
        elif a[0] != 'number' or b[0] != 'number':
            row['status'] = 'ordering_requires_numbers'
        else:
            row['valid'] = {'lt': a[1] < b[1], 'le': a[1] <= b[1],
                            'gt': a[1] > b[1], 'ge': a[1] >= b[1]}[relation['op']]
            row['status'] = 'passed' if row['valid'] else 'comparison_failed'
        rows.append(row)
    valid = structural['valid'] and all(row['valid'] for row in rows)
    return {'valid': valid, 'complete': True, 'status': 'valid' if valid else 'rejected',
            'sources': dict(structural['sources'], plan=plan.identity()),
            'structural': structural, 'relations': rows,
            'failed_relations': sum(not row['valid'] for row in rows),
            'semantics': 'scalar eq/ne preserve JSON types; numbers compare exact decimal tokens; ordering requires numbers; no coercion or truth claim'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract')
    parser.add_argument('document')
    parser.add_argument('plan')
    for role in ('contract', 'document', 'plan'):
        parser.add_argument('--' + role + '-sha256')
    args = parser.parse_args(argv)
    try:
        deps = dependencies()
        result = inspect(*deps, args.contract, args.document, args.plan,
                         args.contract_sha256, args.document_sha256, args.plan_sha256)
        output = deps[2].encode(result)
        sys.stdout.write(output)
        return 0 if result['valid'] else 1
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        sys.stderr.write(json.dumps({'valid': False, 'complete': False,
                                    'status': 'input_or_output_error',
                                    'error': str(exc)[:1000]}, ensure_ascii=True) + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
