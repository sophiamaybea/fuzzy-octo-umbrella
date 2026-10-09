from philosophy_core import choose_methods, argument_to_argdown, verify_formal
import pytest

def test_keyword_matches_whole_words():
    x = choose_methods('A small policy.', 6)
    socratic = next((m for m in x['methods'] if m['id'] == 'socratic'), None)
    assert socratic is None or 'all' not in socratic['keyword_matches']

def test_modern_machine_reasoning_lens():
    x = choose_methods('Can ChatGPT machine reasoning be trusted?', 4)
    assert 'machine_epistemics' in [m['id'] for m in x['methods']]

def test_reject_empty_argument_fragments():
    with pytest.raises(ValueError):
        argument_to_argdown([''], 'Q')

def test_reject_more_than_12_propositions():
    with pytest.raises(ValueError):
        verify_formal([f'P{i}' for i in range(14)], 'Q')
