"""Validate the teaching evidence against independent byte-level SHA-256."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / 'static/learn'


def test_evidence_has_exactly_one_mismatch_against_trusted_record():
    unit = json.loads((ROOT / 'hash-integrity.json').read_text(encoding='utf-8'))
    assert unit['id'] == 'hash-integrity' and unit['version'] == 1
    assert len(unit['files']) == len({file['id'] for file in unit['files']}) == 3
    mismatches = []
    for file in unit['files']:
        assert file['name'] == file['id'] + '.txt'
        contents = (ROOT / 'evidence' / file['name']).read_bytes()
        assert b'\r' not in contents  # Git must preserve these exact teaching fixtures.
        assert len(file['expected']) == 64
        if hashlib.sha256(contents).hexdigest() != file['expected']:
            mismatches.append(file['id'])
    assert mismatches == [unit['altered']] == ['beacon-order']


def test_beacon_record_references_original_order_not_delivered_order():
    unit = json.loads((ROOT / 'hash-integrity.json').read_text(encoding='utf-8'))
    record = next(file for file in unit['files'] if file['id'] == 'beacon-order')
    original = b'BEACON ORDER\nKeep the warning lantern ON until the boats are home.\n'
    assert hashlib.sha256(original).hexdigest() == record['expected']
    delivered = (ROOT / 'evidence/beacon-order.txt').read_bytes()
    assert b'lantern OFF' in delivered and original != delivered
