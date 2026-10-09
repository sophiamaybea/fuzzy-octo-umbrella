"""GitHub-first discovery for philosophical reasoning capabilities.

Runs actual public GitHub queries, captures inspectable proposals and only changes
its versioned catalogue on material differences. Never installs arbitrary code.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .evolution import run_research

TOPIC = 'philosophical reasoning Socratic logic argumentation epistemology'
FAMILIES = {
    'argument_mapping': ('Argdown', 'argument reconstruction, premise-conclusion graphs'),
    'computational_argumentation': ('Carneades', 'defeat relations and admissibility semantics'),
    'guided_deliberation': ('Logikon', 'structured multi-perspective reasoning'),
    'formal_logic': ('Carnap, Lean 4, Z3', 'proof checking and formal counterexamples'),
    'research': ('STORM / Co-STORM', 'source-grounded exploratory research'),
    'evaluation': ('Stanford HELM', 'repeatable effectiveness benchmarks'),
}


def stable_candidate(item: dict) -> dict:
    """Do not write fluctuating popularity metrics to git every hour."""
    return {
        'repo': item['repo'], 'url': item['url'],
        'description': (item.get('description') or '')[:350],
        'licence_reported': item.get('license') or 'UNKNOWN',
        'source_tree_sha': item.get('source_tree_sha'),
        'status': 'UNREVIEWED_NOT_INSTALLED',
    }


def evolve(previous: dict, observation: dict) -> tuple[dict,dict]:
    """Returns stable catalogue and diff. Does not conflate popularity with quality."""
    if not isinstance(previous, dict):
        raise ValueError('previous catalogue must be a JSON object')
    if not isinstance(observation, dict) or observation.get('github_discovery', {}).get('successful_searches',0) < 1:
        raise ValueError('at least one successful fresh GitHub search is required')
    past = {x['repo']: x for x in previous.get('candidates',[])}
    inspections = {x['repo']:x for x in observation['github_discovery']['inspections']}
    next_candidates = dict(past)
    changed=[]
    for raw in observation['github_discovery']['ranked_candidates']:
        slug=raw['repo']
        new=stable_candidate(dict(raw,source_tree_sha=inspections.get(slug,{}).get('source_tree_sha') or past.get(slug,{}).get('source_tree_sha')))
        old=past.get(slug)
        if old is None:
            changed.append({'repo':slug,'reason':'new_candidate'})
            next_candidates[slug]=new
        elif any(old.get(field) != new.get(field) for field in ('licence_reported','source_tree_sha','description')):
            changed.append({'repo':slug,'reason':'candidate_metadata_changed'})
            next_candidates[slug]=new
    if previous and not changed:
        return previous, {'material_changes': [], 'count': 0}
    output={
        'schema_version':1,
        'scope':'PHILOSOPHY_ONLY',
        'warning':'These are UNVERIFIED discovery candidates, not installed integrations or learned model weights.',
        'families':{k:{'examples':v[0],'intended_use':v[1]} for k,v in FAMILIES.items()},
        'candidates': sorted(next_candidates.values(),key=lambda x:x['repo'])[:180],
    }
    return output, {'material_changes': changed, 'count':len(changed)}


def main():
    parser=argparse.ArgumentParser(description='Reviewable philosophical capability evolution')
    parser.add_argument('--catalogue',default='data/philosophy_capabilities.json')
    parser.add_argument('--report',default='reports/philosophy-evolution.json')
    args=parser.parse_args()
    result=run_research(TOPIC,limit=8,include_literature=False)
    target=Path(args.catalogue)
    previous=json.loads(target.read_text('utf8')) if target.exists() else {}
    current,changes=evolve(previous,result)
    if current != previous:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(current,indent=2,ensure_ascii=False)+'\n','utf8')
    report={
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'successful_searches':result['github_discovery']['successful_searches'],
        'queries':result['github_discovery']['queries'],
        'failures':result['github_discovery']['errors'],
        'changes':changes,
        'ranked_candidates':result['github_discovery']['ranked_candidates'],
        'inspections':result['github_discovery']['inspections'],
        'code_installed':False,
        'model_retrained':False,
        'requires_human_review':True,
    }
    path=Path(args.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf8')
    print(json.dumps({'catalogue':str(target),'report':str(path),**changes,'approved_integrations':0}))


if __name__=='__main__':
    main()
