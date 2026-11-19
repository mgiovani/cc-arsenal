# Typing and lint

## Contents

- [Annotations](#annotations)
- [Ruff](#ruff)
- [ty](#ty)
- [pytest](#pytest)
- [Tooling](#tooling)

## Annotations

Annotate every function, every fixture including its return type, and every variable whose type is not obvious from the right-hand side.

- Write no `Any`, no `# type: ignore`, no `# ty: ignore`, no `cast` used to quiet an error, and no `# noqa` the project has not allowed. When a third-party stub gap forces one, stop and report it. Silencing the checker hides the next real error in the same line.
- A bare generic (`dict`, `list`, `tuple`, `Callable` with no parameters) is an unwritten type. Spell it out.
- For structured data, prefer a `TypedDict`, a dataclass or a `Protocol` to a loose `dict`.
- Use `X | None`, the `type` statement for aliases, and PEP 695 generic syntax where the project's Python version has them. A recursive alias cannot be a quoted string, because Pydantic cannot evaluate it.
- Quote a forward reference only when the class is not yet defined, such as a self-reference.
- Use `Final` for module constants and `Literal` or `StrEnum` for closed sets.

## Ruff

Ruff does both lint and format, under `[tool.ruff.lint]`. Nobody formats by hand.

Base rule set: `E W F I B C4 UP ARG SIM TC TID ICN Q PL RUF`. A stricter project adds families such as `RET`, `ANN`, `DTZ`, `PT`, `PTH`, `ASYNC`, `TRY`, `FBT`, `SLF`, `ERA` and `FAST` for FastAPI. Take the project's list as given.

- Ignore `E501`, which the formatter owns.
- Set no complexity caps: ignore `PLR0911`, `PLR0912`, `PLR0913`, `PLR0915` and `PLR0917`. Collapsing a guard chain into fewer returns, or splitting a function to fit a statement budget, buries the structure the rule counts. When the project sets caps (for example complexity 8 and five arguments), obey them and fix the code.
- Use single quotes, line length 88, and `force-sort-within-sections = true` so `import x` and `from x import y` sort together by module. Set `known-first-party`.
- Set `runtime-evaluated-base-classes = ["pydantic.BaseModel"]` for the `TC` rules, so typing-only imports are not moved behind `TYPE_CHECKING` where Pydantic needs them at runtime.
- Relax per-file rules only for tests: `ARG` for fakes that keep the real signature, `PLR2004` for magic values, and local imports.
- A suppression that is allowed names one rule code and a reason on the same line.

## ty

ty is the type checker, run through the project's command on the package. It is young and its releases change results, so cap the range in the dev dependencies and note why.

- Run it on the source package. Check the tests too only where the project does.
- Fix the type. When only a cast or an ignore comment would silence it, stop and report it.
- Do not add mypy or pyright beside it.

## pytest

- Set `-ra --strict-config --strict-markers` in `addopts`, and `filterwarnings = ["error"]`.
- Typical markers are `unit`, `integration`, `slow`, `db` and `live`. Run `live` only on request.
- Use `pytest-xdist` and cap the worker count on a shared machine. A test that fails only in parallel is fixed at the source.
- Pass boolean expectations to parametrized tests keyword-only, which satisfies `FBT`.
- Set `asyncio_mode = "auto"` for an async-first project.
- Add an autouse guard that blocks tests from reaching a real external binary, service or model unless a test opts in.

## Tooling

- Use uv: `uv sync --locked`, `uv run`, `uv add`. Do not use pip or poetry in a uv project.
- Use `src` layout and hatchling unless the project differs.
- Run lint as one task: `ruff check`, `ruff format --check`, `ty check`, `lint-imports`, and the prose linter if the repo gates on it. Run tests as another.
- Add `deptry` or `vulture` or `bandit` only where the project already gates on them. They are not a default.
