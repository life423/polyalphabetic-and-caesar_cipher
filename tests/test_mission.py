"""Puzzle content must agree with the cipher engine used by the tools."""
import json
from pathlib import Path

from src.services.web_service import transform_message


def test_observatory_mission_is_a_consistent_solvable_cipher():
    path = Path(__file__).resolve().parents[1] / 'static/missions/observatory-note.json'
    mission = json.loads(path.read_text(encoding='utf-8'))
    assert transform_message(mission['solution'], mission['cipher'], 'Encrypt', mission['key']) == mission['ciphertext']
    assert transform_message(mission['ciphertext'], mission['cipher'], 'Decrypt', mission['key']) == mission['solution']
    assert mission['ciphertext'].split().count('AOL') == 3
    pairs = {cipher: plain for cipher, plain in zip(mission['ciphertext'], mission['solution']) if cipher.isalpha()}
    assert len(pairs) == len(set(pairs.values()))
