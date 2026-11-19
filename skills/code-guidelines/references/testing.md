# Testing

## Contents

- [Fixing a bug](#fixing-a-bug)
- [Where tests live](#where-tests-live)
- [How a test is written](#how-a-test-is-written)
- [Tests that can fail](#tests-that-can-fail)
- [Environment and isolation](#environment-and-isolation)
- [Gates and honest reporting](#gates-and-honest-reporting)

## Fixing a bug

Follow this order. Do not touch the code before step 2.

```
- [ ] 1. Find out why the tests missed it (a double shaped unlike the real thing, a missing case, a weak assertion)
- [ ] 2. Fix or add a test that fails because of the bug, and run it to see it fail
- [ ] 3. Find the root cause and fix it once, in the shared code
- [ ] 4. Run the new test, then the full gate
```

Before step 3, grep every caller of the function you will change. Guarding only the path the report names leaves a sibling caller broken.

If step 2 does not produce a red test, you have not understood the bug yet.

## Where tests live

Tests mirror the source tree one to one. `src/app/vault/models.py` is covered by `tests/vault/test_models.py`. Shared fixtures live in the nearest `conftest.py`.

- Split by cost: a test that crosses no process or network is a unit test. One that needs a real database or a real socket is an integration test.
- A test module that would pass 300 lines splits into `test_<module>_<topic>.py` beside it.
- Where a module has not been split out yet, the test file mirrors the flat module name.

## How a test is written

- Test behaviour through the public API of the module. A test that reaches into private helpers pins the implementation.
- Use a fake or the real thing before a mock. When a mock is the right tool, use the framework's helper (`mocker` in pytest) before a raw `unittest.mock`. A test double keeps the real callable's parameter names.
- No `if`, `else` or `match` inside a test body. Vary the case with a parametrized table: a typed case object and a readable id per case.
- Name each test as a full sentence of behaviour: `test_the_exit_question_is_only_open_for_48_hours`.
- Give a test no docstring by default. If the project traces requirements, use its mechanism (a marker, or a one-line note naming the requirement and acceptance criterion). Never invent a requirement id.
- Build test data with a small closure or helper that has sensible defaults and unique ids per call. Do not add a factory library for it.
- Use a fixed clock constant for time. Do not read the real clock.
- Cover loading, empty, error, overflow and edge states, not only the happy path. Edge inputs: empty, null, zero, maximum, negative, unicode.
- A validator, sanitizer or allowlist needs adversarial cases: encodings, case variants, nested and boundary input, `../..` paths, injection strings, a newline inside an address.

## Tests that can fail

- A test must be able to fail. Flip a comparison or drop a branch in the code and confirm the test goes red.
- Check an absence ("not shown", "not called") only after the async work has settled. Otherwise it passes whether or not the code works.
- Assert on behaviour or accessible output, not on class names or selectors.
- A truthy check where a specific value is expected, a test with no assertion, and a snapshot with no behaviour check are weak.
- Logic with real branching, parsing, money or security earns a test. A trivial edit does not. Do not add a framework for one check.
- Coverage is a gate, not a goal. Meet the project's threshold when it sets one. Never invent one. One test that matters beats a number.
- When you count lines of change, leave tests out. A test is a positive signal, not bloat.

## Environment and isolation

- Set the environment through `monkeypatch` or the framework's equivalent, never by exporting a variable before the run.
- Warnings are errors. Silence a dependency's warning with a named entry that says why, never by relaxing the setting.
- Use strict markers. A new marker is registered in the config before it is used.
- Test databases refuse any URL whose name does not mark it as a test store. Use disposable stores, vaults and origins for failure, replay and restart checks.
- Block tests from reaching a real external tool or service unless one opts in. Add an autouse guard for it.
- A test that needs a real database is part of the gate. Without one it fails or is reported as not run, never counted as passed.
- Never delete pre-existing or production resources during cleanup.

## Gates and honest reporting

Zero failures, zero flakes. Never rerun until green, raise a retry count or record a flake as tolerated. A test that fails under parallel runs is fixed at its source, not excluded.

Never weaken the gate or the assertion to close a ticket.

- Run the narrow failing test first, then the full gate the project defines. Cap parallel workers where the machine is shared.
- Record exit codes, test counts and the tested revision. Redo the run after a material change.
- Fixture tests do not prove installed-backend behaviour. A mocked API does not prove a live flow.
- Where a feature has a real user flow, run it end to end. Automated tests supplement that check and do not replace it.
- Report a check you could not run as unvalidated, never as passed.
- Elapsed time is not deployment proof. After a deploy, check the health endpoint and the running revision against the intended commit.
