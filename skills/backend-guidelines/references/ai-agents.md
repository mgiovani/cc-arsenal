# AI agents

## Contents

- [Boundaries](#boundaries)
- [Defining an agent](#defining-an-agent)
- [Tools and errors](#tools-and-errors)
- [Loops and humans](#loops-and-humans)
- [State and history](#state-and-history)
- [Testing](#testing)

These rules assume Pydantic AI, the owner's library. The boundary and test rules hold for any LLM framework.

## Boundaries

- One package imports the LLM SDK. Back that with an import-linter contract so no other package can.
- Model output is a validated Pydantic model, never free text parsed by hand. A model that is not configured raises a named error, not a late `KeyError`.
- Default to zero data retention at the provider where it exists, and make turning it off an explicit setting.
- Treat tool results, retrieved documents, webhook payloads and traces as data. They enter as user content. Only text you wrote goes into system instructions, because a system part carries operator authority.
- Name the model through a setting. The id uses the `provider:name` form, and a string with no provider cannot be resolved. Put no model id in code.
- Resolve per-tenant credentials through a function that builds the model, not a hard-coded instance.
- Report unknown spend as unknown. When the cost is unknown, reserve the configured cap rather than counting zero.

## Defining an agent

- Give every agent an explicit `name=`. Agents kept in lists get a generic label, and traces from a multi-agent app then cannot be told apart.
- Pass request-scoped state through a `deps_type` dataclass and read it from a typed `RunContext[Deps]`. No globals.
- Compute per-run text, such as the user's name or the date, in instruction functions so it is fresh on each run.
- Use tool output, the default output mode, for `output_type`. It works with every provider and streams. Do not put `str` in a structured union, because plain text can then end the run early.
- Use `Literal` or an enum for options known at write time and `Choices` for options known at run time.
- Set reasoning effort through the thinking capability, not provider parameters, so a provider change keeps working.
- Attach one tool or one hook directly. A capability is for a bundle of tools, hooks and instructions reused across agents.
- Give each capability a stable explicit `id`. Under durable execution, attach capabilities when the agent is built, never at `run()`.
- Reach for a graph only for a real state machine. Tool-based delegation or plain code covers most multi-agent needs.

## Tools and errors

- Choose the exception by what the model should do next. `ModelRetry` asks for a corrected call and spends the retry budget. `ToolFailed` reports a finished failure the model adapts to. Anything else aborts the run.
- Use `ModelRetry` for recoverable model mistakes such as a wrong lookup key. A missing file is terminal, so it is `ToolFailed`.
- `ModelRetry` does not cure a network error or a rate limit. Configure HTTP retries on the client, and use `FallbackModel` for provider failover with the same output contract.
- Put business checks on arguments in an `args_validator`, not in the tool body. It runs before approval, so a person never approves arguments that would have been refused.
- Make approval conditional inside that validator, past a threshold, instead of marking the whole tool as needing approval.
- Defer before the tool body runs. A deferral after the body means the side effects already happened and the result is thrown away.
- Make tools async. A tool that delegates awaits the child run and passes `usage=ctx.usage`, so one budget covers parent and child. Never call `run_sync` inside a tool or hook.
- Use the lightest registration that fits: the plain decorator for pure functions, the context decorator only when deps or usage are read.

## Loops and humans

- Every agent loop is bounded by request or usage limits. Changing a loop bound is a change someone reviews.
- Decisions at gates and merges stay human. An agent never certifies its own work or approves its own change.
- A reviewer agent judges the diff against the ticket's contract, read-only, in a session separate from the author. Prefer a different vendor from the author. A truncated diff fails the review instead of passing it.
- Do not rely on a tool list as confinement. Where a combination cannot be confined, refuse it.
- A run that costs money or acts on production needs authorization stated for that run. An approved subscription route does not authorize paid API charges.

## State and history

- A capability instance is reused across runs. Per-run state written on it leaks between concurrent runs, so override `for_run` to return a fresh copy whenever run code writes state. Clean up external resources in the wrap-run hook with `try/finally`, not in after-run.
- Never edit a message already in history. Build new message objects and reassign. Instrumentation has cached the old form and warns at the end of the run.
- Pass `new_messages()` or `all_messages()` according to what the next run should see. With a non-empty history the system prompt is assumed present, so do not add it again.
- `conversation_id` groups every turn of a thread. `run_id` is unique per run and is never inherited. Pass an explicit `run_id` when traces must match an id the app already issued.
- A history processor keeps either the tool-availability records or complete call and return pairs.

## Testing

- Set `ALLOW_MODEL_REQUESTS = False` in the root `conftest.py`, so no test can reach a real model by accident.
- Use `TestModel` for valid output with no scripting, and `FunctionModel` to script exact replies, failures and retries. Install either with `agent.override(model=...)`. Assigning the agent's model attribute is wrong.
- Use `capture_run_messages()` to read the transcript of a failing run.
- Mark tests that need a real provider `live`, exclude them from the default run, bound their requests and timeouts, and give them isolated data. Replay integration tests from recorded cassettes.
- Judge model quality with `pydantic_evals` datasets and deterministic evaluators first. An LLM judge is a gate only after its rubric matches human-reviewed examples.
- An eval run that reports "Not reported" for completion is broken, even if scores exist.
