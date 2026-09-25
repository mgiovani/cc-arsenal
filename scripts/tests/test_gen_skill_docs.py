"""Unit tests for the skill docs generator."""

import json
from pathlib import Path

import pytest

from scripts import gen_skill_docs

# The count regex only matches two- and three-digit totals, so the fixture repo
# needs >= 10 skills to exercise it: alpha and beta carry the assertions, the
# filler skills just make the totals realistic.
FILLER = tuple(f'filler-{index:02d}' for index in range(10))
ALL_SKILLS = ('alpha', 'beta', *FILLER)


def _marketplace(names: tuple[str, ...] = ALL_SKILLS) -> dict:
    return {
        'name': 'cc-arsenal-marketplace',
        'metadata': {'description': 'All 12 skills.'},
        'plugins': [
            {'name': 'cc-arsenal'},
            {
                'name': 'cc-arsenal-dev',
                'skills': [f'./skills/{name}/' for name in names],
            },
        ],
    }


def _skill(root: Path, name: str, summary: str, *, manual: bool = False) -> None:
    path = root / 'skills' / name
    path.mkdir(parents=True)
    (path / 'SKILL.md').write_text(
        f'---\nname: {name}\ndescription: A long description. And a second sentence.\n'
        f'disable-model-invocation: {str(manual).lower()}\n'
        f'metadata:\n  summary: {json.dumps(summary)}\n---\n\nBody.\n'
    )


def _setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, groupings: list[dict]
) -> None:
    _skill(tmp_path, 'alpha', 'Does alpha things')
    _skill(tmp_path, 'beta', 'Does beta things', manual=True)
    for name in FILLER:
        _skill(tmp_path, name, f'Does {name} things')

    groupings = [
        *groupings,
        {'title': 'Filler', 'description': 'Filler.', 'skills': list(FILLER)},
    ]
    (tmp_path / 'skills.sh.json').write_text(json.dumps({'groupings': groupings}))
    (tmp_path / '.claude-plugin').mkdir()
    (tmp_path / '.claude-plugin' / 'marketplace.json').write_text(
        json.dumps(_marketplace())
    )
    (tmp_path / '.claude-plugin' / 'plugin.json').write_text(
        json.dumps({'description': '12 skills'})
    )
    (tmp_path / 'docs').mkdir()
    for rel, block in (
        ('README.md', 'skills-readme'),
        ('AGENTS.md', 'skills-agents'),
        ('docs/features.md', 'skills-features'),
    ):
        (tmp_path / rel).write_text(
            f'# Title\n\nHolds 12 skills.\n\n<!-- gen:{block} start -->\nold\n'
            f'<!-- gen:{block} end -->\n'
        )
    (tmp_path / 'docs' / 'getting-started.md').write_text('Ships 12 skills.\n')
    (tmp_path / 'docs' / 'onboarding.md').write_text('All 12 skills.\n')
    (tmp_path / 'CONTRIBUTING.md').write_text('Has 12 skills today.\n')

    monkeypatch.setattr(gen_skill_docs, 'ROOT', tmp_path)
    monkeypatch.setattr(gen_skill_docs, 'GROUPS_PATH', tmp_path / 'skills.sh.json')
    monkeypatch.setattr(gen_skill_docs, 'SKILLS_DIR', tmp_path / 'skills')
    monkeypatch.setattr(
        gen_skill_docs,
        'MARKETPLACE_PATH',
        tmp_path / '.claude-plugin' / 'marketplace.json',
    )
    monkeypatch.setattr('sys.argv', ['gen_skill_docs.py'])


def _one_group(skills: list[str]) -> list[dict]:
    return [{'title': 'Group', 'description': 'A group.', 'skills': skills}]


def test_generation_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))

    gen_skill_docs.main()
    first = (tmp_path / 'README.md').read_bytes()
    gen_skill_docs.main()

    assert (tmp_path / 'README.md').read_bytes() == first
    assert 'Does alpha things' in first.decode()


def test_shuffled_groups_and_skills_come_back_sorted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(
        tmp_path,
        monkeypatch,
        [{'title': 'Zulu', 'description': '', 'skills': ['beta', 'alpha']}],
    )

    gen_skill_docs.main()

    config = json.loads((tmp_path / 'skills.sh.json').read_text())
    assert [g['title'] for g in config['groupings']] == ['Filler', 'Zulu']
    zulu = next(g for g in config['groupings'] if g['title'] == 'Zulu')
    assert zulu['skills'] == ['alpha', 'beta']
    agents = (tmp_path / 'AGENTS.md').read_text()
    assert agents.index('### Filler') < agents.index('### Zulu')
    assert agents.index('`alpha`') < agents.index('`beta`')


def test_missing_marker_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    (tmp_path / 'README.md').write_text('# Title\n\nHolds 12 skills.\n')

    with pytest.raises(SystemExit, match='expected 1 start and 1 end marker'):
        gen_skill_docs.main()


def test_skill_in_two_groups_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(
        tmp_path,
        monkeypatch,
        [
            {'title': 'One', 'description': '', 'skills': ['alpha', 'beta']},
            {'title': 'Two', 'description': '', 'skills': ['alpha']},
        ],
    )

    with pytest.raises(SystemExit, match='is in both'):
        gen_skill_docs.main()


def test_ungrouped_skill_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha']))

    with pytest.raises(SystemExit, match='not in any group: beta'):
        gen_skill_docs.main()


def test_feature_bodies_survive_regeneration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    gen_skill_docs.main()

    features = tmp_path / 'docs' / 'features.md'
    features.write_text(
        features.read_text().replace(
            '`/alpha` (auto)\nDoes alpha things',
            '`/alpha` (auto)\nHand-written body.\n- a bullet',
        )
    )
    gen_skill_docs.main()

    assert 'Hand-written body.\n- a bullet' in features.read_text()


def test_group_headings_are_not_absorbed_into_the_body_above_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(
        tmp_path,
        monkeypatch,
        [
            {'title': 'One', 'description': 'First.', 'skills': ['alpha']},
            {'title': 'Two', 'description': 'Second.', 'skills': ['beta']},
        ],
    )

    gen_skill_docs.main()
    gen_skill_docs.main()

    features = (tmp_path / 'docs' / 'features.md').read_text()
    assert features.count('### Two (1 skill)') == 1


def test_marketplace_gap_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    (tmp_path / '.claude-plugin' / 'marketplace.json').write_text(
        json.dumps(_marketplace(('alpha', *FILLER)))
    )

    with pytest.raises(SystemExit, match='no plugin variant includes: beta'):
        gen_skill_docs.main()


def test_check_mode_exits_nonzero_when_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    monkeypatch.setattr('sys.argv', ['gen_skill_docs.py', '--check'])

    with pytest.raises(SystemExit) as excinfo:
        gen_skill_docs.main()

    assert excinfo.value.code == 1


def test_a_count_inside_a_preserved_body_is_left_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    gen_skill_docs.main()

    features = tmp_path / 'docs' / 'features.md'
    features.write_text(
        features.read_text().replace(
            '`/alpha` (auto)\nDoes alpha things',
            '`/alpha` (auto)\nSupports 27 skill toolchains.',
        )
    )
    gen_skill_docs.main()

    assert 'Supports 27 skill toolchains.' in features.read_text()


def test_a_subheading_inside_a_body_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    gen_skill_docs.main()

    features = tmp_path / 'docs' / 'features.md'
    body = '`/alpha` (auto)\nDoes alpha things.\n\n### Usage\n\nRun it like this.'
    features.write_text(
        features.read_text().replace('`/alpha` (auto)\nDoes alpha things', body)
    )
    gen_skill_docs.main()

    assert '### Usage\n\nRun it like this.' in features.read_text()


def test_an_inline_slash_mention_inside_a_body_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    gen_skill_docs.main()

    features = tmp_path / 'docs' / 'features.md'
    body = (
        '`/alpha` (auto)\nDoes alpha things.\nSee also `/beta` (manual) for that.\n'
        '- a bullet after it'
    )
    features.write_text(
        features.read_text().replace('`/alpha` (auto)\nDoes alpha things', body)
    )
    gen_skill_docs.main()

    text = features.read_text()
    assert 'See also `/beta` (manual) for that.\n- a bullet after it' in text


def test_empty_description_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    (tmp_path / 'skills' / 'alpha' / 'SKILL.md').write_text(
        '---\nname: alpha\ndescription:\nmetadata:\n  summary: "x"\n---\n\nBody.\n'
    )

    with pytest.raises(SystemExit, match='non-empty description'):
        gen_skill_docs.main()


def test_summary_falls_back_to_a_truncated_first_sentence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    sentence = 'Alpha ' * 40
    (tmp_path / 'skills' / 'alpha' / 'SKILL.md').write_text(
        f'---\nname: alpha\ndescription: {sentence.strip()}. Second sentence.\n'
        f'---\n\nB.\n'
    )

    gen_skill_docs.main()

    readme = (tmp_path / 'README.md').read_text()
    assert 'Second sentence' not in readme
    summary = next(line for line in readme.splitlines() if line.startswith('| [`alpha`]'))
    assert '…' in summary
    assert len(summary.split('|')[2].strip()) <= gen_skill_docs.SUMMARY_FALLBACK_LEN + 1


def test_unknown_skill_name_in_a_group_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta', 'nope']))

    with pytest.raises(SystemExit, match="unknown skill 'nope'"):
        gen_skill_docs.main()


def test_file_without_a_count_phrase_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    (tmp_path / 'docs' / 'onboarding.md').write_text('Nothing countable here.\n')

    with pytest.raises(SystemExit, match='no skill count matched'):
        gen_skill_docs.main()


def test_check_mode_passes_once_generated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch, _one_group(['alpha', 'beta']))
    gen_skill_docs.main()

    monkeypatch.setattr('sys.argv', ['gen_skill_docs.py', '--check'])
    gen_skill_docs.main()
