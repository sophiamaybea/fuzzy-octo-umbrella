"""Deterministic tests: no network calls, no third-party executable code."""
import pytest
from capability_hunter.philosophy_learning import (
    record_correction,list_lessons,review_correction,
)
from capability_hunter.philosophy_evolution import evolve
from capability_hunter.philosophy_bridge import run_inquiry


def _observed(repo='owner/argument-tool',sha='ab12', desc='Logic tools'):
    return {'github_discovery':{'successful_searches':2,
        'ranked_candidates':[{'repo':repo,'url':'https://github.com/'+repo,
            'description':desc,'license':'MIT'}],
        'inspections':[{'repo':repo,'source_tree_sha':sha}]}}


def test_evolution_only_tracks_material_changes():
    start,delta=evolve({},_observed())
    assert delta['count']==1
    same,delta=evolve(start,_observed())
    assert same==start and delta['count']==0
    newer,delta=evolve(start,_observed(sha='ab13'))
    assert delta['count']==1
    assert newer['candidates'][0]['source_tree_sha']=='ab13'
    assert newer['candidates'][0]['status']=='UNREVIEWED_NOT_INSTALLED'


def test_evolution_fails_closed_without_live_discovery():
    with pytest.raises(ValueError,match='successful'):
        evolve({}, {'github_discovery':{'successful_searches':0}})


def test_pending_feedback_never_becomes_verified_automatically(tmp_path):
    db=tmp_path/'private.sqlite3'
    r=record_correction('Was the argument valid?','Incorrect premise attribution',
        'The quoted speaker did not assert that premise.',db_path=db)
    assert list_lessons(db_path=db)==[]
    pending=list_lessons(status='PENDING',db_path=db)
    assert len(pending)==1 and pending[0]['id']==r['id']
    assert len(pending[0]['question_sha256'])==64
    review_correction(r['id'],'VERIFIED','Reviewed against verbatim source',db_path=db)
    assert list_lessons(db_path=db)[0]['status']=='VERIFIED'
    with pytest.raises(ValueError,match='already reviewed'):
        review_correction(r['id'],'REJECTED','Not permitted twice',db_path=db)


def test_corrected_feedback_validation(tmp_path):
    with pytest.raises(ValueError,match='HTTPS'):
        record_correction('An adequate question','The error was elsewhere',
             'Here is an updated interpretation','file:///etc/passwd',db_path=tmp_path/'l.db')
    with pytest.raises(ValueError,match='alleged_error'):
        record_correction('An adequate question','bad','A longer correction',db_path=tmp_path/'l.db')


def test_bridge_disabled_by_default(monkeypatch):
    monkeypatch.delenv('PHILOSOPHY_ENGINE_URL',raising=False)
    monkeypatch.delenv('PHILOSOPHY_ENGINE_API_KEY',raising=False)
    assert run_inquiry('How should we understand justice?')['status']=='NOT_CONFIGURED'
    monkeypatch.setenv('PHILOSOPHY_ENGINE_URL','https://philosophy.example')
    monkeypatch.setenv('PHILOSOPHY_ENGINE_API_KEY','not-a-real-token')
    assert run_inquiry('How should we understand justice?')['status']=='DISABLED'
    monkeypatch.setenv('PHILOSOPHY_ALLOW_MCP_INQUIRY','1')
    monkeypatch.setenv('PHILOSOPHY_ENGINE_URL','http://bad.example')
    with pytest.raises(ValueError,match='HTTPS'):
        run_inquiry('How should we understand justice?')
