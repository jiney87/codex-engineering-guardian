# Technology-specific adaptation

These are prompts for **selecting real project checks**, not universal commands.

## Python
- Prefer existing formatter/linter (ruff, black), type checker (pyright/mypy), `pytest`/`unittest`; invoke only if configured or available.
- Make exceptions intentional. Avoid broad catch-and-ignore; use context managers for resources and parameterized tests for boundaries.
- Do not add a third-party dependency for trivial behavior without explaining trade-offs.

## TypeScript / JavaScript
- Prefer repository scripts for `typecheck`, `lint`, `test`, `build`. In typed projects, avoid `any`/unchecked type assertions at trust boundaries.
- Validate network JSON at runtime even when TypeScript static types are present.
- Review async failure states, cleanup, resource limits, date/time zones and request cancellation.

## Web / mini-program / front-end
- Separate presentation/UI from domain logic and storage adapters where it meaningfully reduces coupling.
- Review authentication/authorization on server side, not just disabled UI controls.
- Mobile and accessibility checks: narrow viewport, keyboard/focus handling, loading/error/empty states; verify with actual rendering if available.
- For WeChat mini-programs, verify actual platform API constraints and upload/permission/privacy requirements against current official documentation; do not invent API capabilities.

## Data, payment, and state transitions
- Document idempotency, retries, transaction boundaries, schema migration direction, audit logs and error recovery before editing critical workflows.
- Use property/round-trip tests for money/quantities and clearly documented currency precision; avoid binary floating-point for exact monetary accounting.

## Security references
- Security requirements should be updated from trusted current sources, including OWASP ASVS and official vendor documentation. Neither Code Complete nor this Skill alone is a complete secure-development standard.
