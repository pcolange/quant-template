---
paths:
  - "**/*.py"
---

# Code Style

Write clean, Pythonic, DRY code. Follow these rules when writing or modifying Python in this repo.

## Linting & Type Checking

Follow the project's `ruff` and `pyright` configurations if present (typically in `pyproject.toml`). When a project does not yet configure these tools, default to the conventions below.
- **Strict Typing:** Prefer `pyright` in strict mode. All functions, arguments, and return values must be annotated.
- **Automated Enforcement:** Naming conventions (`snake_case`), formatting, and import sorting are handled automatically by `ruff`.

## Conventions

- Idiomatic Python: list comprehensions, f-strings, context managers, early returns, guard clauses. Flat over nested.
- DRY: shared helpers go in a utility module — don't copy-paste across files.
- YAGNI: no speculative abstractions or extra configurability. Three similar lines beat a premature abstraction.
- `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants. Private helpers prefixed with `_`.
- Modern type hints: `str | None` not `Optional[str]`, `list[str]` not `List[str]`.
- `dataclasses.dataclass` for simple data containers. Use `pydantic.BaseModel` when you need runtime validation. Prefer functions over classes when there's no state.
- No mutable default arguments — use `None` and assign the default in the body.
- All `open()` calls must pass `encoding="utf-8"`.
- Catch specific exceptions. Broad `except Exception` only at top-level handlers with `# ruff: noqa: BLE001`.
- Documentation: Docstrings are **optional** for internal modules and functions per project configuration, but highly encouraged for complex logic or public APIs.
- Lazy imports for heavy deps (e.g. `google.cloud`). No wildcard or circular imports.

## Documentation & Maintenance

- **Update READMEs:** Any change to functionality, commands, or environment variables must be reflected in the project's README or docs.
- **In-code Comments:**
  - Use sparingly and keep them brief.
  - Favor well-named identifiers over commentary that restates what the code does.
  - Do not reference past or future implementation work (e.g., "added for X", "TODO revisit", "previously did Y"). Exception: a hidden constraint a reader cannot infer from the code.
  - Update docstrings and comments in the same commit as the code change.
- **Maintain CLAUDE.md:** If you add new skills or change the build process, update the local `CLAUDE.md` immediately.

## Logging

- Use `structlog` for all diagnostic, status, and error output. Never use `print()`. Stdlib `logging` is acceptable only when a third-party library requires it; route it through structlog's `ProcessorFormatter` where possible so output stays consistent.
- Get a module-level logger: `logger = structlog.get_logger(__name__)`.
- Use appropriate levels: `logger.debug()` for trace/diagnostic, `logger.info()` for normal events, `logger.warning()` for recoverable issues, `logger.error()` / `logger.exception()` for failures.
- Pass context as structured key-value pairs (`logger.info("event_name", user_id=uid, status=status)`). Do not f-string or concatenate values into the event string.

## Module Boundaries

- Keep architecture separated by domain and ensure strong separation of concerns.
