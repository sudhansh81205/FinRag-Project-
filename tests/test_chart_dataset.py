import hashlib
import json
import shutil
from pathlib import Path

import pytest

from scripts.verify_chart_set import verify
from src.charts.dataset import load_candidate_set

CHARTS = Path(__file__).resolve().parents[1] / 'data/charts'


def test_complete_candidate_set_has_exact_split_and_resolvable_originals():
    cases, manifest, audit = load_candidate_set(CHARTS)
    assert audit['counts'] == {'dev':15, 'heldout':35}
    assert audit['total'] == 50 and audit['distinct_original_images'] == 6
    assert audit['shortfall'] == {'dev':0,'heldout':0}
    assert not audit['evaluation_ready'] and not audit['heldout_answers_generated_or_scored']
    assert len({s['company'] for s in manifest['sources']}) == 6
    dev = {q['image_sha256'] for q in cases if q['split']=='dev'}
    heldout = {q['image_sha256'] for q in cases if q['split']=='heldout'}
    assert len(dev)==1 and len(heldout)==5 and dev.isdisjoint(heldout)
    assert verify(CHARTS)['filing_inventory_verified']


def test_original_dev_file_still_matches_published_hash():
    assert hashlib.sha256((CHARTS/'apple-2021-candidate-questions.json').read_bytes()).hexdigest() == '48734f19b7e0817cb429e662832fdb8e97e34f543da41460c66e97d20d81a9c3'


def test_changed_asset_is_rejected(tmp_path):
    charts=tmp_path/'charts'
    shutil.copytree(CHARTS, charts)
    manifest=json.loads((charts/'chart-sources.json').read_text())
    (charts/manifest['sources'][1]['asset']).write_bytes(b'changed source image')
    with pytest.raises(ValueError, match='checksum'):
        load_candidate_set(charts)


def test_changed_frozen_question_is_rejected(tmp_path):
    charts=tmp_path/'charts'
    shutil.copytree(CHARTS, charts)
    path=charts/'heldout-35-candidate-questions.json'
    cases=json.loads(path.read_text())
    cases[0]['answer']='Unverified changed label'
    path.write_text(json.dumps(cases))
    with pytest.raises(ValueError, match='checksum'):
        load_candidate_set(charts)


def test_unknown_chart_reference_is_rejected_even_if_question_hash_updated(tmp_path):
    charts=tmp_path/'charts'
    shutil.copytree(CHARTS, charts)
    path=charts/'heldout-35-candidate-questions.json'
    cases=json.loads(path.read_text())
    cases[0]['source_asset_id']='not-an-original-source'
    path.write_text(json.dumps(cases))
    index_path=charts/'question-set.json'
    index=json.loads(index_path.read_text())
    index['question_files_sha256'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    index_path.write_text(json.dumps(index))
    with pytest.raises(ValueError, match='resolve'):
        load_candidate_set(charts)
