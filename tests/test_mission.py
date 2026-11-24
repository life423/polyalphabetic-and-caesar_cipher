"""Puzzle content must agree with the cipher engine used by the tools."""
import json
from pathlib import Path
import pytest

from src.services.web_service import transform_message

ROOT = Path(__file__).resolve().parents[1] / 'static/missions'
MANIFEST = json.loads((ROOT / 'campaign.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('filename', MANIFEST['missions'])
def test_campaign_case_matches_shared_cipher_engine(filename):
    mission = json.loads((ROOT / filename).read_text(encoding='utf-8'))
    assert transform_message(mission['solution'], mission['cipher'], 'Encrypt', mission['key']) == mission['ciphertext']
    assert transform_message(mission['ciphertext'], mission['cipher'], 'Decrypt', mission['key']) == mission['solution']
    assert len(mission['clues']) == 3
    pairs = {cipher: plain for cipher, plain in zip(mission['ciphertext'], mission['solution']) if cipher.isalpha()}
    assert len(pairs) == len(set(pairs.values()))
    assert max(map(len, mission['ciphertext'].split())) <= 12  # Fits the narrow-phone word board.
    if 'firstMove' in mission:
        first = mission['firstMove']
        assert first['cipher'] in mission['ciphertext']
        assert ''.join(pairs[letter] for letter in first['cipher']) == first['plain']


def test_campaign_has_five_distinct_connected_cases():
    cases = [json.loads((ROOT / filename).read_text(encoding='utf-8')) for filename in MANIFEST['missions']]
    assert len(cases) == len({case['id'] for case in cases}) == 5
    assert {case['cipher'] for case in cases} == {'Caesar', 'Substitution', 'Affine'}
    assert len({case['ciphertext'] for case in cases}) == 5
    assert cases[0]['id'] == 'observatory-note' and cases[0]['version'] == 1
    assert 'mystery is solved' in cases[-1]['ending']


def test_observatory_mission_is_a_consistent_solvable_cipher():
    path = Path(__file__).resolve().parents[1] / 'static/missions/observatory-note.json'
    mission = json.loads(path.read_text(encoding='utf-8'))
    assert transform_message(mission['solution'], mission['cipher'], 'Encrypt', mission['key']) == mission['ciphertext']
    assert transform_message(mission['ciphertext'], mission['cipher'], 'Decrypt', mission['key']) == mission['solution']
    assert mission['ciphertext'].split().count('AOL') == 3
    pairs = {cipher: plain for cipher, plain in zip(mission['ciphertext'], mission['solution']) if cipher.isalpha()}
    assert len(pairs) == len(set(pairs.values()))
