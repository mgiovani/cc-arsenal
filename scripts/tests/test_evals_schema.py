"""Schema validation for skills/*/evals/*.json across the whole repo."""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestEvalsSchema(unittest.TestCase):
    """Validate evals.json files: skill + evals[] with id/prompt/assertions[]."""

    def test_evals_json_files_are_valid(self) -> None:
        eval_files = sorted(REPO_ROOT.glob('skills/*/evals/evals.json'))
        assert eval_files, 'expected at least one evals.json under skills/*/evals/'

        for path in eval_files:
            with self.subTest(path=path):
                data = json.loads(path.read_text())

                assert 'skill' in data, f'{path}: missing "skill"'
                skill = data['skill']
                assert isinstance(skill, str)
                assert skill

                assert 'evals' in data, f'{path}: missing "evals"'
                evals = data['evals']
                assert isinstance(evals, list)
                assert evals, f'{path}: "evals" must be a non-empty list'

                for entry in evals:
                    eval_id = entry.get('id')
                    prefix = f'{path}: eval {eval_id}'
                    assert 'id' in entry, f'{prefix} missing "id"'
                    assert 'prompt' in entry, f'{prefix} missing prompt'
                    assert 'assertions' in entry, f'{prefix} missing assertions'

                    assertions = entry['assertions']
                    assert isinstance(assertions, list)
                    assert assertions, f'{prefix} assertions must be non-empty'


class TestTriggerEvalSchema(unittest.TestCase):
    """Validate trigger-eval.json files: array of {query, should_trigger}."""

    def test_trigger_eval_json_files_are_valid(self) -> None:
        trigger_files = sorted(REPO_ROOT.glob('skills/*/evals/trigger-eval.json'))
        assert trigger_files, 'expected at least one trigger-eval.json under evals/'

        for path in trigger_files:
            with self.subTest(path=path):
                data = json.loads(path.read_text())

                assert isinstance(data, list)
                assert data, f'{path}: must be a non-empty array'

                for entry in data:
                    assert 'query' in entry, f'{path}: entry missing "query"'
                    query = entry['query']
                    assert isinstance(query, str)
                    assert query

                    assert 'should_trigger' in entry, f'{path}: entry missing "trigger"'
                    assert isinstance(entry['should_trigger'], bool), (
                        f'{path}: should_trigger must be a bool'
                    )

                trigger_values = {entry['should_trigger'] for entry in data}
                assert trigger_values == {True, False}, (
                    f'{path}: must contain true and false should_trigger cases'
                )


if __name__ == '__main__':
    unittest.main()
