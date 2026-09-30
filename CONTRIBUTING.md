# Contributing

## Setup

```bash
uv sync
uv run pytest
uv run ruff check
```

## Add a mutation

Mutations live in `src/approval_testkit/mutations.py`. A mutation is one function that takes the
`Approval` and `now` and returns a list of `Probe`s — executions the verifier **must reject**.

```python
def _email_case(a: Approval, now: datetime) -> list[Probe]:
    to = a.request.args.get("to")
    if not isinstance(to, str):
        return []
    return [_probe(a, now, "args.to uppercased", args={**a.request.args, "to": to.upper()})]
```

Register it in `MUTATIONS`:

```python
Mutation("email_case", "argument binding", "Recipient casing changed", _email_case),
```

Then add a test in `tests/test_mutations.py` and make sure the secure example still passes
(or explain in the PR why it should fail).

## Write an adapter

An adapter is any class with two methods — see the README. Framework adapters (OpenAI Agents SDK,
MCP, LangGraph, PydanticAI, FastAPI) go under `examples/` first; they move into the package once
the shape is stable.

## Add a reporter

Reporters are plain functions `Report -> str` in `src/approval_testkit/reporters.py`; wire them
into the `Format` enum in `cli.py`.

## Ground rules

- Keep the core framework-neutral: no LLM or agent-framework imports in `src/`.
- Every new check needs a test that fails the vulnerable path and passes the secure path.
- Small PRs over big ones.
